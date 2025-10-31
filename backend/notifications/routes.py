# backend/notifications/routes.py
from __future__ import annotations

from typing import Optional

from flask import Blueprint, jsonify, request, session

from ..extensions import db
from ..login.models import User
from .email import send_email

bp = Blueprint("notifications", __name__)


def _current_user() -> Optional[User]:
    uid = session.get("uid")
    if not uid:
        return None
    user = User.query.get(uid)
    if user is None:
        session.clear()
    return user


@bp.post("/daily-routine")
def send_daily_routine():
    """
    Envía un correo con la rutina diaria a un usuario específico.

    Requiere sesión activa. Usuarios no administradores solo pueden enviarse
    correos a sí mismos.
    """
    actor = _current_user()
    if not actor:
        return jsonify({"error": "No autenticado"}), 401

    data = request.get_json(force=True, silent=True) or {}
    try:
        user_id = int(data.get("user_id"))
    except (TypeError, ValueError):
        return jsonify({"error": "user_id inválido"}), 400

    body = (data.get("body") or "").strip()
    if not body:
        return jsonify({"error": "body es obligatorio"}), 400

    subject = (data.get("subject") or "Tu rutina diaria Fitter").strip()
    if not subject:
        subject = "Tu rutina diaria Fitter"

    target = User.query.get(user_id)
    if not target:
        return jsonify({"error": "Usuario no encontrado"}), 404

    if not actor.is_admin and actor.id != target.id:
        return jsonify({"error": "No autorizado"}), 403

    try:
        send_email(
            to_email=target.email,
            subject=subject,
            body=body,
            from_name="Fitter",
        )
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 500
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": "No se pudo enviar el correo", "details": str(exc)}), 502

    return jsonify({"ok": True}), 200

