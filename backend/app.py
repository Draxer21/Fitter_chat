# backend/app.py
import os
import json
import logging
import time
from collections import deque
from datetime import datetime
from math import ceil
from typing import Any, Dict
from flask import Flask, request, jsonify, render_template, session as flask_session
from logging.handlers import RotatingFileHandler
import requests
from dotenv import load_dotenv

from .config import (
    build_cors_config,
    build_json_config,
    build_rate_limit_config,
    load_app_config,
)
from .bootstrap import init_extensions, load_models
from .blueprints import register_blueprints
from .extensions import db, cors, socketio  # unica instancia compartida
from .chat.service import ChatService, ChatServiceError, ServiceResponse
from .metrics import metrics, setup_metrics_logger

# (opcional) rate limit si lo tienes instalado
Limiter = None
get_remote_address = None
try:
    from flask_limiter import Limiter as _Limiter
    from flask_limiter.util import get_remote_address as _get_remote_address
    Limiter = _Limiter
    get_remote_address = _get_remote_address
except Exception:
    pass


class OperationalMetrics:
    def __init__(self, window_size: int) -> None:
        self._events = deque(maxlen=max(1, int(window_size or 500)))

    def record(
        self,
        *,
        status_code: int,
        latency_ms: float,
        interaction_result: str | None,
    ) -> None:
        self._events.append(
            {
                "status_code": int(status_code),
                "latency_ms": max(0.0, float(latency_ms)),
                "interaction_result": interaction_result or "",
            }
        )

    def snapshot(self) -> Dict[str, Any]:
        events = list(self._events)
        total = len(events)
        count_2xx = sum(1 for event in events if 200 <= event["status_code"] < 300)
        count_4xx = sum(1 for event in events if 400 <= event["status_code"] < 500)
        count_5xx = sum(1 for event in events if 500 <= event["status_code"] < 600)
        fallback_count = sum(1 for event in events if event["interaction_result"] == "fallback")
        handoff_count = sum(1 for event in events if event["interaction_result"] == "handoff")
        blocked_count = sum(1 for event in events if event["interaction_result"] == "blocked_no_consent")

        p95_latency_ms = 0.0
        if events:
            latencies = sorted(event["latency_ms"] for event in events)
            index = max(0, ceil(0.95 * len(latencies)) - 1)
            p95_latency_ms = round(latencies[index], 3)

        return {
            "window_size": total,
            "fallback_rate": round(fallback_count / total, 4) if total else 0.0,
            "handoff_rate": round(handoff_count / total, 4) if total else 0.0,
            "blocked_rate": round(blocked_count / total, 4) if total else 0.0,
            "p95_latency_ms": p95_latency_ms,
            "count_2xx": count_2xx,
            "count_4xx": count_4xx,
            "count_5xx": count_5xx,
        }


def create_app() -> Flask:
    # Carga opcional de variables de entorno desde .env para no exportarlas en cada sesión.
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    load_dotenv(os.path.join(base_dir, ".env"))
    load_dotenv()

    app = Flask(__name__, static_folder="static", template_folder="templates")

    # ---------------- Config ----------------
    app.config.from_object(load_app_config())

    json_config = build_json_config()
    app.json.ensure_ascii = json_config.ensure_ascii
    app.json.sort_keys = json_config.sort_keys

    cors_config = build_cors_config()
    if cors_config.warning:
        app.logger.warning(cors_config.warning)
    cors.init_app(app, **cors_config.to_kwargs())

    if socketio is not None:
        socketio.init_app(app, cors_allowed_origins="*", async_mode="threading")

    limiter = None
    rate_limit_config = build_rate_limit_config()
    if Limiter and get_remote_address:
        limiter_kwargs = rate_limit_config.to_kwargs()

        def _get_client_ip():
            """Obtiene la IP real del cliente, considerando proxies reversos."""
            forwarded = request.headers.get("X-Forwarded-For", "")
            if forwarded:
                # X-Forwarded-For: client, proxy1, proxy2 — tomamos la primera
                return forwarded.split(",")[0].strip()
            return get_remote_address()

        try:
            # v3 style
            limiter = Limiter(_get_client_ip, app=app, **limiter_kwargs)
        except TypeError:
            # v2 style
            limiter = Limiter(key_func=_get_client_ip, app=app, **limiter_kwargs)
        if rate_limit_config.uses_memory_storage:
            app.logger.warning("RATELIMIT_STORAGE_URI no esta definido. Se usa memoria en proceso.")
        app.limiter = limiter  # por si luego quieres usar decorators

    # Logging rotativo (tolerante a FS)
    try:
        logs_path = os.path.join(os.path.dirname(__file__), "logs")
        os.makedirs(logs_path, exist_ok=True)
        handler = RotatingFileHandler(
            os.path.join(logs_path, "backend.log"),
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8"
        )
        handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s"))
        app.logger.setLevel(logging.INFO)
        app.logger.addHandler(handler)
        app.logger.info("Logging a archivo inicializado.")
    except Exception as e:
        # Si no se puede escribir a disco, no rompemos la app
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s"))
        app.logger.setLevel(logging.INFO)
        app.logger.addHandler(stream_handler)
        app.logger.warning(f"No se pudo inicializar logging a archivo: {e}")

    # ---------------- Init extensiones ----------------
    init_extensions(app)
    load_models(app)

    # ---------------- Metrics logger ----------------
    setup_metrics_logger(app.logger)

    # ---------------- Blueprints ----------------
    register_blueprints(app)

    # ---------------- Rate-limits por endpoint (anti-DDoS / brute-force) --------
    from .login.routes import _apply_rate_limits
    _apply_rate_limits(app)

    # ── /chat/demo/send — planificador público sin autenticación ──
    import uuid as _uuid_mod

    @app.post("/chat/demo/send")
    def chat_demo_send():
        from .chat.demo_service import process_demo_message
        data = request.get_json(force=True, silent=True) or {}
        message = str(data.get("message") or "").strip()
        if not message:
            return jsonify({"error": "Mensaje vacío."}), 400
        session_id = str(data.get("session_id") or "").strip()
        if not session_id or len(session_id) > 64:
            session_id = str(_uuid_mod.uuid4())
        try:
            result = process_demo_message(session_id=session_id, message=message)
        except Exception as exc:
            app.logger.exception("Error en chat_demo_send: %s", exc)
            return jsonify({"error": "Error interno en la demo."}), 500
        return jsonify({
            "responses":  result["responses"],
            "session_id": session_id,
            "turns_left": result["turns_left"],
            "exhausted":  result["exhausted"],
        }), 200

    # Rate limit para demo pública (30 mensajes/hora por IP)
    if limiter:
        limiter.limit("30/hour")(chat_demo_send)

    # ---------------- Realtime (SocketIO) ----------------
    from .realtime.events import init_realtime
    init_realtime(app)

    # ---------------- Cliente HTTP con retry/backoff ----------------
    http_session = requests.Session()
    try:
        from urllib3.util.retry import Retry  # type: ignore
        from requests.adapters import HTTPAdapter
        retries = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=(502, 503, 504),
            allowed_methods=frozenset(["GET", "POST", "PUT", "DELETE", "PATCH"])
        )
        adapter = HTTPAdapter(max_retries=retries)
        http_session.mount("http://", adapter)
        http_session.mount("https://", adapter)
    except Exception:
        # Si no estÃ¡n disponibles, usamos session por defecto
        pass

    chat_service = ChatService(app, db, http_session)
    app.chat_service = chat_service
    app.operational_metrics = OperationalMetrics(app.config.get("METRICS_WINDOW_SIZE", 500))

    # ---------------- Utiles internos ----------------
    def _json_error(msg: str, code: int = 400):
        return jsonify({"error": msg}), code

    # ---------------- Endpoints propios ----------------
    @app.get("/health")
    def health():
        return {
            "ok": True,
            "service": app.config.get("SERVICE_NAME", "fitter-backend"),
            "ts": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        }, 200

    if limiter:
        limiter.exempt(health)

    @app.get("/ready")
    def ready():
        if not chat_service.check_database_ready():
            return {
                "ok": False,
                "reason": "db_unavailable",
            }, 503
        if not chat_service.check_rasa_ready():
            return {
                "ok": False,
                "reason": "rasa_unavailable",
            }, 503
        return {
            "ok": True,
            "service": app.config.get("SERVICE_NAME", "fitter-backend"),
        }, 200

    if limiter:
        limiter.exempt(ready)

    @app.get("/metrics")
    def operational_metrics():
        return jsonify(app.operational_metrics.snapshot()), 200

    if limiter:
        limiter.exempt(operational_metrics)

    @app.post("/chat/send")
    def chat_send():
        started = time.perf_counter()
        status = "ok"
        status_code = 200
        interaction_result = None
        try:
            data: Dict[str, Any] = request.get_json(force=True, silent=False)
        except Exception:
            db.session.rollback()
            status = "error"
            status_code = 400
            elapsed_ms = (time.perf_counter() - started) * 1000
            app.operational_metrics.record(
                status_code=status_code,
                latency_ms=elapsed_ms,
                interaction_result=interaction_result,
            )
            metrics.inc_counter("chat_send_total", tags={"status": status, "code": status_code})
            metrics.observe_latency("chat_send_latency_ms", elapsed_ms, tags={"status": status})
            return _json_error("JSON invalido", 400)

        try:
            result = chat_service.send_message(data, request.headers, flask_session)
        except ChatServiceError as exc:
            # Si Rasa está caído (502) caemos al planificador local
            if exc.status_code == 502:
                try:
                    from .chat.demo_service import process_demo_message
                    sender_fb = str(data.get("sender", "web-user"))
                    message_fb = str(data.get("message", "")).strip()
                    fb_result = process_demo_message(session_id=sender_fb, message=message_fb)
                    return jsonify(fb_result["responses"]), 200
                except Exception:
                    app.logger.exception("Fallback al planificador también falló")
            status = "error"
            status_code = exc.status_code
            elapsed_ms = (time.perf_counter() - started) * 1000
            app.operational_metrics.record(
                status_code=status_code,
                latency_ms=elapsed_ms,
                interaction_result=interaction_result,
            )
            metrics.inc_counter("chat_send_total", tags={"status": status, "code": status_code})
            metrics.observe_latency("chat_send_latency_ms", elapsed_ms, tags={"status": status})
            return _json_error(exc.message, exc.status_code)
        status_code = result.status_code
        interaction_result = result.interaction_result
        elapsed_ms = (time.perf_counter() - started) * 1000
        app.operational_metrics.record(
            status_code=status_code,
            latency_ms=elapsed_ms,
            interaction_result=interaction_result,
        )
        metrics.inc_counter("chat_send_total", tags={"status": status, "code": status_code})
        metrics.observe_latency("chat_send_latency_ms", elapsed_ms, tags={"status": status})
        return jsonify(result.payload), result.status_code

    @app.get("/chat/context/<sender>")
    def chat_context_get(sender: str):
        try:
            chat_id = request.args.get("chat_id")
            result = chat_service.get_context(sender, chat_id, request.headers, flask_session)
        except ChatServiceError as exc:
            return _json_error(exc.message, exc.status_code)
        return jsonify(result.payload), result.status_code

    @app.post("/chat/context/<sender>")
    def chat_context_update(sender: str):
        try:
            data: Dict[str, Any] = request.get_json(force=True, silent=False)
        except Exception:
            db.session.rollback()
            return _json_error("JSON invalido", 400)

        try:
            chat_id = request.args.get("chat_id") or data.get("chat_id")
            result = chat_service.update_context(sender, chat_id, data, request.headers, flask_session)
        except ChatServiceError as exc:
            return _json_error(exc.message, exc.status_code)
        return jsonify(result.payload), result.status_code

    @app.post("/chat/consent/revoke/<sender>")
    def chat_consent_revoke(sender: str):
        try:
            data: Dict[str, Any] = request.get_json(force=True, silent=True) or {}
        except Exception:
            db.session.rollback()
            return _json_error("JSON invalido", 400)
        chat_id = data.get("chat_id")
        try:
            result = chat_service.revoke_consent(sender, chat_id, request.headers, flask_session)
        except ChatServiceError as exc:
            return _json_error(exc.message, exc.status_code)
        return jsonify(result.payload), result.status_code

    @app.get("/chat/sessions/<sender>")
    def chat_sessions(sender: str):
        try:
            limit_arg = request.args.get("limit", None)
            try:
                limit = int(limit_arg) if limit_arg is not None else 50
            except Exception:
                limit = 50
            result = chat_service.get_sessions(sender, limit, request.headers, flask_session)
        except ChatServiceError as exc:
            return _json_error(exc.message, exc.status_code)
        return jsonify(result.payload), result.status_code

    @app.post("/nlu/parse")
    def nlu_parse():
        started = time.perf_counter()
        status = "ok"
        status_code = 200
        try:
            data: Dict[str, Any] = request.get_json(force=True, silent=False)
        except Exception:
            status = "error"
            status_code = 400
            elapsed_ms = (time.perf_counter() - started) * 1000
            metrics.inc_counter("nlu_parse_total", tags={"status": status, "code": status_code})
            metrics.observe_latency("nlu_parse_latency_ms", elapsed_ms, tags={"status": status})
            return _json_error("JSON invÃ¡lido", 400)

        text = str(data.get("text", "")).strip()
        if not text:
            status = "error"
            status_code = 400
            elapsed_ms = (time.perf_counter() - started) * 1000
            metrics.inc_counter("nlu_parse_total", tags={"status": status, "code": status_code})
            metrics.observe_latency("nlu_parse_latency_ms", elapsed_ms, tags={"status": status})
            return _json_error("El campo 'text' es obligatorio.", 400)
        max_message_len = int(app.config.get("MAX_MESSAGE_LEN", 5000))
        if len(text) > max_message_len:
            status = "error"
            status_code = 413
            elapsed_ms = (time.perf_counter() - started) * 1000
            metrics.inc_counter("nlu_parse_total", tags={"status": status, "code": status_code})
            metrics.observe_latency("nlu_parse_latency_ms", elapsed_ms, tags={"status": status})
            return _json_error("El texto es demasiado largo.", 413)

        try:
            resp = http_session.post(
                chat_service.rasa_url(app.config["RASA_PARSE_ENDPOINT"]),
                json={"text": text},
                timeout=app.config["RASA_TIMEOUT_PARSE"],
            )
            resp.raise_for_status()
            payload = resp.json()
        except requests.exceptions.RequestException as e:
            app.logger.exception("Fallo al contactar Rasa en /nlu/parse")
            status = "error"
            status_code = 502
            elapsed_ms = (time.perf_counter() - started) * 1000
            metrics.inc_counter("nlu_parse_total", tags={"status": status, "code": status_code})
            metrics.observe_latency("nlu_parse_latency_ms", elapsed_ms, tags={"status": status})
            return _json_error(f"No se pudo contactar a Rasa NLU: {e}", 502)
        except json.JSONDecodeError:
            status = "error"
            status_code = 502
            elapsed_ms = (time.perf_counter() - started) * 1000
            metrics.inc_counter("nlu_parse_total", tags={"status": status, "code": status_code})
            metrics.observe_latency("nlu_parse_latency_ms", elapsed_ms, tags={"status": status})
            return _json_error("Respuesta de Rasa NLU no es JSON vÃ¡lido.", 502)
        elapsed_ms = (time.perf_counter() - started) * 1000
        metrics.inc_counter("nlu_parse_total", tags={"status": status, "code": 200})
        metrics.observe_latency("nlu_parse_latency_ms", elapsed_ms, tags={"status": status})
        return jsonify(payload), 200

    # ---------------- Seguridad bÃ¡sica en headers ----------------
    @app.after_request
    def add_security_headers(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        resp.headers.setdefault("Referrer-Policy", "no-referrer")
        resp.headers.setdefault("Permissions-Policy", "geolocation=()")
        return resp

    # ---------------- SPA fallback (React build) ----------------
    # Usa SPA_FALLBACK=1 para habilitar en prod cuando sirves el build desde templates/index.html
    if os.getenv("SPA_FALLBACK", "0") == "1":
        @app.route("/", defaults={"path": ""})
        @app.route("/<path:path>")
        def spa(path: str):
            try:
                return render_template("index.html")
            except Exception:
                return _json_error("index.html no encontrado en templates/ (SPA_FALLBACK estÃ¡ activo).", 404)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "0") == "1"
    )
