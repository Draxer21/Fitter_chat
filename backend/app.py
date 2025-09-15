# backend/app.py
import os
import json
from typing import Any, Dict
from flask import Flask, request, jsonify
import requests

# --- Opcionales: cargador .env, CORS y rate limit (si las instalas) ---
try:
    from dotenv import load_dotenv  # pip install python-dotenv
    load_dotenv()
except Exception:
    pass

try:
    from flask_cors import CORS  # pip install Flask-Cors
except Exception:
    CORS = None

try:
    from flask_limiter import Limiter            # pip install Flask-Limiter
    from flask_limiter.util import get_remote_address
except Exception:
    Limiter = None
    get_remote_address = None
# ----------------------------------------------------------------------

def create_app() -> Flask:
    app = Flask(__name__)

    # -----------------------
    # Configuración por ENV
    # -----------------------
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-me")
    app.config["RASA_BASE_URL"] = os.getenv("RASA_BASE_URL", "http://localhost:5005").rstrip("/")
    app.config["RASA_REST_WEBHOOK"] = os.getenv("RASA_REST_WEBHOOK", "/webhooks/rest/webhook")
    app.config["RASA_PARSE_ENDPOINT"] = os.getenv("RASA_PARSE_ENDPOINT", "/model/parse")
    app.config["CORS_ORIGINS"] = os.getenv("CORS_ORIGINS", "*")
    app.config["RATE_LIMIT_DEFAULT"] = os.getenv("RATE_LIMIT_DEFAULT", "60/minute")

    # CORS (opcional)
    if CORS:
        CORS(app, resources={r"/*": {"origins": app.config["CORS_ORIGINS"]}})

    # Rate limiting (opcional)
    if Limiter and get_remote_address:
        Limiter(
            key_func=get_remote_address,
            app=app,
            default_limits=[app.config["RATE_LIMIT_DEFAULT"]],
        )

    # -----------------------
    # Utilidades internas
    # -----------------------
    def _rasa_url(path: str) -> str:
        path = path if path.startswith("/") else "/" + path
        return f"{app.config['RASA_BASE_URL']}{path}"

    def _error(msg: str, code: int = 400):
        return jsonify({"error": msg}), code

    # -----------------------
    # Endpoints
    # -----------------------
    @app.get("/health")
    def health():
        """
        Healthcheck simple para monitoreo.
        """
        return {"status": "ok"}, 200

    @app.post("/chat/send")
    def chat_send():
        """
        Body:
          {
            "sender": "diego",
            "message": "hola"
          }
        Respuesta: lista de mensajes de Rasa (REST channel).
        """
        try:
            data: Dict[str, Any] = request.get_json(force=True, silent=False)
        except Exception:
            return _error("JSON inválido", 400)

        sender = str(data.get("sender", "user")).strip()
        message = str(data.get("message", "")).strip()

        if not message:
            return _error("El campo 'message' es obligatorio y no puede ir vacío.", 400)

        try:
            resp = requests.post(
                _rasa_url(app.config["RASA_REST_WEBHOOK"]),
                json={"sender": sender, "message": message},
                timeout=15,
            )
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            return _error(f"No se pudo contactar a Rasa: {e}", 502)

        # Rasa REST devuelve lista de objetos (text, buttons, custom, etc.)
        try:
            payload = resp.json()
        except json.JSONDecodeError:
            return _error("Respuesta de Rasa no es JSON válido.", 502)

        return jsonify(payload), 200

    @app.post("/nlu/parse")
    def nlu_parse():
        """
        Body:
          { "text": "quiero reservar clase" }
        Respuesta: intent, entidades y confidencias del NLU.
        """
        try:
            data: Dict[str, Any] = request.get_json(force=True, silent=False)
        except Exception:
            return _error("JSON inválido", 400)

        text = str(data.get("text", "")).strip()
        if not text:
            return _error("El campo 'text' es obligatorio y no puede ir vacío.", 400)

        try:
            resp = requests.post(
                _rasa_url(app.config["RASA_PARSE_ENDPOINT"]),
                json={"text": text},
                timeout=10,
            )
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            return _error(f"No se pudo contactar a Rasa NLU: {e}", 502)

        try:
            payload = resp.json()
        except json.JSONDecodeError:
            return _error("Respuesta de Rasa NLU no es JSON válido.", 502)

        return jsonify(payload), 200

    return app


# -----------------------
# Modo ejecución directa
# -----------------------
if __name__ == "__main__":
    app = create_app()
    # Variables útiles para ejecución local
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, debug=debug)
