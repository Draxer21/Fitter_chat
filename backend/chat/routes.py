# -*- coding: utf-8 -*-
from flask import Blueprint, current_app, jsonify, request
import requests

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
            timeout=15
        )
        r.raise_for_status()
        return jsonify(r.json()), 200
    except requests.RequestException:
        return jsonify([{"text": "No se pudo conectar al motor conversacional."}]), 502

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
