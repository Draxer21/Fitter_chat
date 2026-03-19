from __future__ import annotations

from datetime import datetime

from flask import Blueprint, jsonify, request, session

from ..extensions import db
from ..login.models import User
from .models import HandoffRequest

bp = Blueprint("handoff", __name__)


def _get_admin_user():
    """Return the current user if they are an admin, else None."""
    uid = session.get("uid")
    if not uid:
        return None
    user = db.session.get(User, uid)
    if not user or not user.is_admin:
        return None
    return user


@bp.get("/")
def list_handoff_requests():
    admin = _get_admin_user()
    if not admin:
        return jsonify({"error": "No autorizado."}), 403

    status_filter = request.args.get("status")
    query = HandoffRequest.query
    if status_filter:
        query = query.filter_by(status=status_filter)

    requests_list = query.order_by(HandoffRequest.created_at.desc()).all()
    return jsonify({"requests": [r.to_dict() for r in requests_list]}), 200


@bp.post("/")
def create_handoff_request():
    uid = session.get("uid")
    data = request.get_json(force=True) or {}

    sender_id = (data.get("sender_id") or "").strip()
    if not sender_id:
        return jsonify({"error": "sender_id es obligatorio."}), 400

    reason = (data.get("reason") or "otro").strip()
    user_id = data.get("user_id") or uid

    handoff = HandoffRequest(
        user_id=user_id,
        sender_id=sender_id,
        reason=reason,
    )
    db.session.add(handoff)
    db.session.commit()
    return jsonify({"request": handoff.to_dict()}), 201


@bp.patch("/<int:id>/assign")
def assign_handoff(id: int):
    admin = _get_admin_user()
    if not admin:
        return jsonify({"error": "No autorizado."}), 403

    handoff = db.session.get(HandoffRequest, id)
    if not handoff:
        return jsonify({"error": "Solicitud no encontrada."}), 404

    handoff.assigned_admin_id = admin.id
    handoff.status = "assigned"
    db.session.commit()
    return jsonify({"request": handoff.to_dict()}), 200


@bp.patch("/<int:id>/resolve")
def resolve_handoff(id: int):
    admin = _get_admin_user()
    if not admin:
        return jsonify({"error": "No autorizado."}), 403

    handoff = db.session.get(HandoffRequest, id)
    if not handoff:
        return jsonify({"error": "Solicitud no encontrada."}), 404

    data = request.get_json(force=True) or {}
    handoff.notes = data.get("notes")
    handoff.status = "resolved"
    handoff.resolved_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"request": handoff.to_dict()}), 200


@bp.get("/pending/count")
def pending_count():
    uid = session.get("uid")
    if not uid:
        return jsonify({"error": "Inicio de sesion requerido."}), 401

    count = HandoffRequest.query.filter_by(status="pending").count()
    return jsonify({"count": count}), 200
