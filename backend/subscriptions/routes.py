from __future__ import annotations

from datetime import datetime

from flask import Blueprint, jsonify, request, session

from ..extensions import db
from .models import Subscription

bp = Blueprint("subscriptions", __name__)

VALID_PLANS = {"basic", "premium", "black"}


@bp.get("/")
def get_active_subscription():
    uid = session.get("uid")
    if not uid:
        return jsonify({"error": "Inicio de sesion requerido."}), 401

    sub = (
        Subscription.query
        .filter_by(user_id=uid, status="active")
        .order_by(Subscription.created_at.desc())
        .first()
    )
    if not sub:
        return jsonify({"subscription": None}), 200
    return jsonify({"subscription": sub.to_dict()}), 200


@bp.post("/")
def create_subscription():
    uid = session.get("uid")
    if not uid:
        return jsonify({"error": "Inicio de sesion requerido."}), 401

    data = request.get_json(force=True) or {}
    plan_type = (data.get("plan_type") or "").strip().lower()
    if plan_type not in VALID_PLANS:
        return jsonify({"error": "Plan invalido. Opciones: basic, premium, black."}), 400

    existing = Subscription.query.filter_by(user_id=uid, status="active").first()
    if existing:
        return jsonify({"error": "Ya tienes una suscripcion activa."}), 409

    sub = Subscription(user_id=uid, plan_type=plan_type)
    db.session.add(sub)
    db.session.commit()
    return jsonify({"subscription": sub.to_dict()}), 201


@bp.put("/<int:sub_id>")
def change_plan(sub_id: int):
    uid = session.get("uid")
    if not uid:
        return jsonify({"error": "Inicio de sesion requerido."}), 401

    sub = db.session.get(Subscription, sub_id)
    if not sub:
        return jsonify({"error": "Suscripcion no encontrada."}), 404
    if sub.user_id != uid:
        return jsonify({"error": "No autorizado."}), 403
    if sub.status != "active":
        return jsonify({"error": "Solo se puede cambiar una suscripcion activa."}), 400

    data = request.get_json(force=True) or {}
    plan_type = (data.get("plan_type") or "").strip().lower()
    if plan_type not in VALID_PLANS:
        return jsonify({"error": "Plan invalido. Opciones: basic, premium, black."}), 400

    sub.plan_type = plan_type
    db.session.commit()
    return jsonify({"subscription": sub.to_dict()}), 200


@bp.delete("/<int:sub_id>")
def cancel_subscription(sub_id: int):
    uid = session.get("uid")
    if not uid:
        return jsonify({"error": "Inicio de sesion requerido."}), 401

    sub = db.session.get(Subscription, sub_id)
    if not sub:
        return jsonify({"error": "Suscripcion no encontrada."}), 404
    if sub.user_id != uid:
        return jsonify({"error": "No autorizado."}), 403
    if sub.status == "cancelled":
        return jsonify({"error": "Suscripcion ya cancelada."}), 400

    sub.status = "cancelled"
    sub.cancelled_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"subscription": sub.to_dict()}), 200


@bp.get("/history")
def subscription_history():
    uid = session.get("uid")
    if not uid:
        return jsonify({"error": "Inicio de sesion requerido."}), 401

    subs = (
        Subscription.query
        .filter_by(user_id=uid)
        .order_by(Subscription.created_at.desc())
        .all()
    )
    return jsonify({"subscriptions": [s.to_dict() for s in subs]}), 200
