# -*- coding: utf-8 -*-
from flask import Blueprint, current_app, jsonify, request
import requests
import uuid
from ..extensions import db
from .demo_service import process_demo_message

bp = Blueprint("chat", __name__)


@bp.post("/send")
def chat_send():
    data = request.get_json(force=True, silent=True) or {}
    sender = str(data.get("sender") or "web-unknown")
    message = str(data.get("message") or "").strip()
    if not message:
        return jsonify([{"text": "Mensaje vacío."}]), 200
    try:
        r = requests.post(
            f"{current_app.config['RASA_BASE_URL']}/webhooks/rest/webhook",
            json={"sender": sender, "message": message},
            timeout=5,
        )
        r.raise_for_status()
        return jsonify(r.json()), 200
    except requests.RequestException:
        # Rasa no disponible → usar planificador local como fallback
        try:
            result = process_demo_message(session_id=sender, message=message)
            return jsonify(result["responses"]), 200
        except Exception as exc:
            current_app.logger.exception("Error en fallback del planificador: %s", exc)
            return jsonify([{"text": "Lo siento, el asistente no está disponible en este momento. Intenta más tarde."}]), 200


@bp.post("/demo/send")
def demo_send():
    """Endpoint público de demo — sin autenticación.

    Body JSON:
      - message  (str, requerido): texto del usuario
      - session_id (str, opcional): ID de sesión del cliente; si no se envía se genera uno nuevo

    Response JSON:
      - responses    [list]  : mensajes del bot
      - session_id   (str)   : ID de sesión (el cliente debe guardarlo y reenviarlo)
      - turns_left   (int)   : mensajes restantes en esta sesión
      - exhausted    (bool)  : sesión agotada
    """
    data = request.get_json(force=True, silent=True) or {}
    message = str(data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Mensaje vacío."}), 400

    # Generar o reusar session_id
    session_id = str(data.get("session_id") or "").strip()
    if not session_id or len(session_id) > 64:
        session_id = str(uuid.uuid4())

    try:
        result = process_demo_message(session_id=session_id, message=message)
    except Exception as exc:
        current_app.logger.exception("Error en demo_send: %s", exc)
        return jsonify({"error": "Error interno en la demo."}), 500

    return jsonify({
        "responses": result["responses"],
        "session_id": session_id,
        "turns_left": result["turns_left"],
        "exhausted": result["exhausted"],
    }), 200


@bp.post("/parse")
def nlu_parse():
    data = request.get_json(force=True, silent=True) or {}
    text = str(data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "text vacío"}), 400
    try:
        r = requests.post(f"{current_app.config['RASA_BASE_URL']}/model/parse",
                          json={"text": text}, timeout=10)
        r.raise_for_status()
        return jsonify(r.json()), 200
    except requests.RequestException:
        return jsonify({"error": "no se pudo conectar a Rasa"}), 502
