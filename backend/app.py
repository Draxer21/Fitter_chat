# backend/app.py
import os
import json
import logging
from typing import Any, Dict, Optional
from flask import Flask, request, jsonify, render_template
from logging.handlers import RotatingFileHandler
import requests

from .extensions import db, migrate, cors  # ← única instancia compartida

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

    # Seguridad / tamaño de payload
    app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_CONTENT_LENGTH", "1048576"))  # 1MB
    app.json.ensure_ascii = False
    app.json.sort_keys = False

    # CORS (única inicialización)
    cors_origins = os.getenv("CORS_ORIGINS", "*")
    cors.init_app(
        app,
        supports_credentials=True,
        resources={r"/*": {"origins": cors_origins}}
    )
    if cors_origins == "*" and True:  # supports_credentials=True por diseño
        app.logger.warning(
            "CORS con supports_credentials=True y origins='*' no es válido en navegadores. "
            "Define CORS_ORIGINS con una lista de orígenes explícitos en producción."
        )

    # Rate limiting (compat v2/v3)
    if Limiter and get_remote_address:
        try:
            # v3 style
            limiter = Limiter(get_remote_address, app=app,
                              default_limits=[os.getenv("RATE_LIMIT_DEFAULT", "60/minute")])
        except TypeError:
            # v2 style
            limiter = Limiter(key_func=get_remote_address, app=app,
                              default_limits=[os.getenv("RATE_LIMIT_DEFAULT", "60/minute")])
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
    migrate.init_app(app, db)

    # Carga modelos para que Alembic detecte metadata
    with app.app_context():
        try:
            from .gestor_inventario import models  # noqa: F401
        except Exception as e:
            app.logger.warning(f"No se pudieron cargar modelos de gestor_inventario: {e}")

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

    # ---------------- Endpoints propios ----------------
    @app.get("/health")
    def health():
        return {"status": "ok"}, 200

    @app.post("/chat/send")
    def chat_send():
        # Validación y límites
        try:
            data: Dict[str, Any] = request.get_json(force=True, silent=False)
        except Exception:
            return _error("JSON inválido", 400)

        sender = str(data.get("sender", "web-user")).strip() or "web-user"
        message = str(data.get("message", "")).strip()
        if not message:
            return _error("El campo 'message' es obligatorio.", 400)
        if len(message) > int(os.getenv("MAX_MESSAGE_LEN", "5000")):
            return _error("El mensaje es demasiado largo.", 413)

        try:
            resp = session.post(
                _rasa_url(app.config["RASA_REST_WEBHOOK"]),
                json={"sender": sender, "message": message},
                timeout=app.config["RASA_TIMEOUT_SEND"],
            )
            resp.raise_for_status()
            payload = resp.json()  # Rasa responde array de objetos
            if not isinstance(payload, (list, tuple)):
                # Normaliza a lista por si Rasa/GW devolviera un objeto
                payload = [payload]
        except requests.exceptions.RequestException as e:
            app.logger.exception("Fallo al contactar Rasa en /chat/send")
            return _error(f"No se pudo contactar a Rasa: {e}", 502)
        except json.JSONDecodeError:
            return _error("Respuesta de Rasa no es JSON válido.", 502)

        return jsonify(payload), 200

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
