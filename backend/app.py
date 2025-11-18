# backend/app.py
import os
import json
import logging
from typing import Any, Dict
from flask import Flask, request, jsonify, render_template, session as flask_session
from logging.handlers import RotatingFileHandler
import requests

from .config import (
    build_cors_config,
    build_json_config,
    build_rate_limit_config,
    load_app_config,
)
from .bootstrap import init_extensions, load_models
from .blueprints import register_blueprints
from .extensions import db, cors  # unica instancia compartida
from .chat.service import ChatService, ChatServiceError, ServiceResponse

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


def create_app() -> Flask:
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

    rate_limit_config = build_rate_limit_config()
    if Limiter and get_remote_address:
        limiter_kwargs = rate_limit_config.to_kwargs()
        try:
            # v3 style
            limiter = Limiter(get_remote_address, app=app, **limiter_kwargs)
        except TypeError:
            # v2 style
            limiter = Limiter(key_func=get_remote_address, app=app, **limiter_kwargs)
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

    # ---------------- Blueprints ----------------
    register_blueprints(app)

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

    # ---------------- Utiles internos ----------------
    def _json_error(msg: str, code: int = 400):
        return jsonify({"error": msg}), code

    # ---------------- Endpoints propios ----------------
    @app.get("/health")
    def health():
        return {"status": "ok"}, 200

    @app.post("/chat/send")
    def chat_send():
        try:
            data: Dict[str, Any] = request.get_json(force=True, silent=False)
        except Exception:
            db.session.rollback()
            return _json_error("JSON invalido", 400)

        try:
            result = chat_service.send_message(data, request.headers, flask_session)
        except ChatServiceError as exc:
            return _json_error(exc.message, exc.status_code)
        return jsonify(result.payload), result.status_code

    @app.get("/chat/context/<sender>")
    def chat_context_get(sender: str):
        try:
            result = chat_service.get_context(sender, request.headers, flask_session)
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
            result = chat_service.update_context(sender, data, request.headers, flask_session)
        except ChatServiceError as exc:
            return _json_error(exc.message, exc.status_code)
        return jsonify(result.payload), result.status_code

    @app.post("/nlu/parse")
    def nlu_parse():
        try:
            data: Dict[str, Any] = request.get_json(force=True, silent=False)
        except Exception:
            return _json_error("JSON invÃ¡lido", 400)

        text = str(data.get("text", "")).strip()
        if not text:
            return _json_error("El campo 'text' es obligatorio.", 400)
        max_message_len = int(app.config.get("MAX_MESSAGE_LEN", 5000))
        if len(text) > max_message_len:
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
            return _json_error(f"No se pudo contactar a Rasa NLU: {e}", 502)
        except json.JSONDecodeError:
            return _json_error("Respuesta de Rasa NLU no es JSON vÃ¡lido.", 502)

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
        debug=os.getenv("FLASK_DEBUG", "1") == "1"
    )


