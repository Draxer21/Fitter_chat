# backend/app.py
import os
import json
import logging
from typing import Any, Dict, Optional
from flask import Flask, request, jsonify, render_template, session
from logging.handlers import RotatingFileHandler
import requests

from .extensions import db, migrate, cors  # unica instancia compartida
from .chat.models import ChatUserContext

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
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-me")

    # Base de datos
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "SQLALCHEMY_DATABASE_URI",
        "postgresql+psycopg2://rasa_user:rasa123@127.0.0.1:5432/rasa_db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Rasa
    app.config["RASA_BASE_URL"] = os.getenv("RASA_BASE_URL", "http://localhost:5005").rstrip("/")
    app.config["RASA_REST_WEBHOOK"] = os.getenv("RASA_REST_WEBHOOK", "/webhooks/rest/webhook")
    app.config["RASA_PARSE_ENDPOINT"] = os.getenv("RASA_PARSE_ENDPOINT", "/model/parse")
    app.config["RASA_TIMEOUT_SEND"] = float(os.getenv("RASA_TIMEOUT_SEND", "15"))
    app.config["RASA_TIMEOUT_PARSE"] = float(os.getenv("RASA_TIMEOUT_PARSE", "10"))
    app.config["CHAT_CONTEXT_API_KEY"] = os.getenv("CHAT_CONTEXT_API_KEY", "")

    # Seguridad / tamaño de payload
    app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_CONTENT_LENGTH", "1048576"))  # 1MB
    app.json.ensure_ascii = False
    app.json.sort_keys = False

    # CORS (unica inicializacion)
    raw_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000")
    cors_supports_credentials = os.getenv("CORS_SUPPORTS_CREDENTIALS", "true").lower() not in {"0", "false", "no"}
    if not raw_cors_origins.strip():
        parsed_cors_origins = ["http://localhost:3000"]
    elif raw_cors_origins.strip() == "*":
        parsed_cors_origins = ["*"]
    else:
        parsed_cors_origins = [origin.strip() for origin in raw_cors_origins.split(",") if origin.strip()]
    if not parsed_cors_origins:
        parsed_cors_origins = ["http://localhost:3000"]
    wildcard_cors = parsed_cors_origins == ["*"]
    if wildcard_cors and cors_supports_credentials:
        app.logger.warning(
            "CORS con supports_credentials=True y origins='*' no es valido en navegadores. "
            "Define CORS_ORIGINS con una lista de origenes explicitos en produccion. "
            "Se deshabilita supports_credentials para continuar."
        )
        cors_supports_credentials = False
    cors.init_app(
        app,
        supports_credentials=cors_supports_credentials,
        resources={r"/*": {"origins": "*" if wildcard_cors else parsed_cors_origins}}
    )

    # Rate limiting (compat v2/v3)
    if Limiter and get_remote_address:
        limiter_defaults = [os.getenv("RATE_LIMIT_DEFAULT", "60/minute")]
        limiter_storage_uri = os.getenv("RATELIMIT_STORAGE_URI")
        limiter_kwargs = {
            "default_limits": limiter_defaults,
            "storage_uri": limiter_storage_uri or "memory://",
        }
        strategy = os.getenv("RATELIMIT_STRATEGY")
        if strategy:
            limiter_kwargs["strategy"] = strategy
        try:
            # v3 style
            limiter = Limiter(get_remote_address, app=app, **limiter_kwargs)
        except TypeError:
            # v2 style
            limiter = Limiter(key_func=get_remote_address, app=app, **limiter_kwargs)
        if not limiter_storage_uri:
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
    db.init_app(app)
    migrations_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "migrations"))
    migrate.init_app(app, db, directory=migrations_dir)

    # Carga modelos para que Alembic detecte metadata
    with app.app_context():
        try:
            from .gestor_inventario import models  # noqa: F401
        except Exception as e:
            app.logger.warning(f"No se pudieron cargar modelos de gestor_inventario: {e}")
        try:
            from .login import models as login_models  # noqa: F401
        except Exception as e:
            app.logger.warning(f"No se pudieron cargar modelos de login: {e}")

    # ---------------- Blueprints ----------------
    try:
        from .gestor_inventario.routes import bp as inventario_bp
        app.register_blueprint(inventario_bp, url_prefix="/inventario")
    except Exception as e:
        app.logger.warning(f"No se pudo registrar blueprint inventario: {e}")

    try:
        from .carritoapp.routes import bp as carrito_bp
        app.register_blueprint(carrito_bp, url_prefix="/carrito")
    except Exception as e:
        app.logger.warning(f"No se pudo registrar blueprint carrito: {e}")

    try:
        from .producto.routes import bp as producto_bp
        app.register_blueprint(producto_bp, url_prefix="/producto")
    except Exception as e:
        app.logger.warning(f"No se pudo registrar blueprint producto: {e}")

    try:
        from .login.routes import bp as auth_bp
        app.register_blueprint(auth_bp, url_prefix="/auth")
    except Exception as e:
        app.logger.warning(f"No se pudo registrar blueprint auth: {e}")

    # ---------------- Cliente HTTP con retry/backoff ----------------
    session = requests.Session()
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
        session.mount("http://", adapter)
        session.mount("https://", adapter)
    except Exception:
        # Si no están disponibles, usamos session por defecto
        pass

    # ---------------- Utiles internos ----------------
    def _rasa_url(path: str) -> str:
        path = path if path.startswith("/") else "/" + path
        return f"{app.config['RASA_BASE_URL']}{path}"

    def _error(msg: str, code: int = 400):
        return jsonify({"error": msg}), code

    def _context_api_key_valid() -> bool:
        expected = (app.config.get("CHAT_CONTEXT_API_KEY") or "").strip()
        if not expected:
            return False
        provided = (
            request.headers.get("X-Context-Key")
            or request.headers.get("X-Api-Key")
            or request.headers.get("Authorization")
            or ""
        ).strip()
        if provided.lower().startswith("bearer "):
            provided = provided.split(" ", 1)[1].strip()
        return provided == expected

    def _session_uid() -> Optional[int]:
        try:
            uid = session.get("uid")
        except Exception:
            return None
        try:
            return int(uid) if uid is not None else None
        except (TypeError, ValueError):
            return None

    def _ensure_context_access(ctx: Optional[ChatUserContext]) -> bool:
        if _context_api_key_valid():
            return True
        uid = _session_uid()
        if uid is None:
            return False
        if ctx is None:
            return True
        if ctx.user_id and ctx.user_id != uid:
            return False
        if not ctx.user_id:
            ctx.user_id = uid
        return True

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
            return _error("JSON invalido", 400)

        sender = str(data.get("sender", "web-user")).strip() or "web-user"
        sender = sender[:80]
        message = str(data.get("message", "")).strip()
        if not message:
            db.session.rollback()
            return _error("El campo 'message' es obligatorio.", 400)
        if len(message) > int(os.getenv("MAX_MESSAGE_LEN", "5000")):
            db.session.rollback()
            return _error("El mensaje es demasiado largo.", 413)

        ctx = ChatUserContext.get_or_create(sender, _session_uid())
        if not _ensure_context_access(ctx):
            db.session.rollback()
            return _error("No autorizado para este contexto.", 401)

        rasa_payload: Dict[str, Any] = {"sender": sender, "message": message}
        metadata = ctx.to_metadata()
        if metadata:
            rasa_payload["metadata"] = {"persisted_context": metadata}

        try:
            resp = session.post(
                _rasa_url(app.config["RASA_REST_WEBHOOK"]),
                json=rasa_payload,
                timeout=app.config["RASA_TIMEOUT_SEND"],
            )
            resp.raise_for_status()
            payload = resp.json()
            if not isinstance(payload, (list, tuple)):
                payload = [payload]
        except requests.exceptions.RequestException as e:
            app.logger.exception("Fallo al contactar Rasa en /chat/send")
            db.session.rollback()
            return _error(f"No se pudo contactar a Rasa: {e}", 502)
        except json.JSONDecodeError:
            db.session.rollback()
            return _error("Respuesta de Rasa no es JSON valido.", 502)

        updated_context = False
        for item in payload:
            if not isinstance(item, dict):
                continue
            custom_payload = item.get("custom")
            if not custom_payload and isinstance(item.get("json_message"), dict):
                custom_payload = item["json_message"]
            if not isinstance(custom_payload, dict):
                continue
            msg_type = str(custom_payload.get("type") or "").strip().lower()
            if msg_type == "routine_detail":
                ctx.set_last_routine(custom_payload)
                updated_context = True
            elif msg_type == "diet_plan":
                ctx.set_last_diet(custom_payload)
                updated_context = True

        if not updated_context:
            ctx.touch()

        db.session.commit()
        return jsonify(payload), 200

    @app.get("/chat/context/<sender>")
    def chat_context_get(sender: str):
        sender = (sender or "").strip()[:80]
        ctx = ChatUserContext.query.filter_by(sender_id=sender).one_or_none()
        if not ctx:
            if _context_api_key_valid() or _session_uid() is not None:
                return jsonify({"found": False}), 404
            return _error("Contexto no encontrado.", 404)
        if not _ensure_context_access(ctx):
            db.session.rollback()
            return _error("No autorizado para este contexto.", 401)
        db.session.commit()
        return jsonify({"context": ctx.to_dict()}), 200

    @app.post("/chat/context/<sender>")
    def chat_context_update(sender: str):
        try:
            data: Dict[str, Any] = request.get_json(force=True, silent=False)
        except Exception:
            db.session.rollback()
            return _error("JSON invalido", 400)

        sender = (sender or "").strip()[:80]
        ctx = ChatUserContext.get_or_create(sender, _session_uid())
        if not _ensure_context_access(ctx):
            db.session.rollback()
            return _error("No autorizado para este contexto.", 401)

        updated = False
        if "allergies" in data:
            raw = data.get("allergies")
            ctx.set_allergies(raw if isinstance(raw, str) else (str(raw) if raw is not None else None))
            updated = True
        if "medical_conditions" in data:
            raw = data.get("medical_conditions")
            ctx.set_medical_conditions(raw if isinstance(raw, str) else (str(raw) if raw is not None else None))
            updated = True
        if "notes" in data:
            note = data.get("notes")
            if isinstance(note, str):
                ctx.notes = note.strip() or None
            elif note is None:
                ctx.notes = None
            else:
                ctx.notes = str(note).strip() or None
            updated = True
        if isinstance(data.get("last_routine"), dict):
            ctx.set_last_routine(data["last_routine"])
            updated = True
        if isinstance(data.get("last_diet"), dict):
            ctx.set_last_diet(data["last_diet"])
            updated = True
        history_entry = data.get("history_entry")
        if isinstance(history_entry, dict):
            ctx.append_history(history_entry)
            updated = True

        if not updated:
            ctx.touch()

        db.session.commit()
        return jsonify({"ok": True, "context": ctx.to_dict()}), 200

    @app.post("/nlu/parse")
    def nlu_parse():
        try:
            data: Dict[str, Any] = request.get_json(force=True, silent=False)
        except Exception:
            return _error("JSON inválido", 400)

        text = str(data.get("text", "")).strip()
        if not text:
            return _error("El campo 'text' es obligatorio.", 400)
        if len(text) > int(os.getenv("MAX_MESSAGE_LEN", "5000")):
            return _error("El texto es demasiado largo.", 413)

        try:
            resp = session.post(
                _rasa_url(app.config["RASA_PARSE_ENDPOINT"]),
                json={"text": text},
                timeout=app.config["RASA_TIMEOUT_PARSE"],
            )
            resp.raise_for_status()
            payload = resp.json()
        except requests.exceptions.RequestException as e:
            app.logger.exception("Fallo al contactar Rasa en /nlu/parse")
            return _error(f"No se pudo contactar a Rasa NLU: {e}", 502)
        except json.JSONDecodeError:
            return _error("Respuesta de Rasa NLU no es JSON válido.", 502)

        return jsonify(payload), 200

    # ---------------- Seguridad básica en headers ----------------
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
                return _error("index.html no encontrado en templates/ (SPA_FALLBACK está activo).", 404)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "1") == "1"
    )
