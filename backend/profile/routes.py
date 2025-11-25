# backend/profile/routes.py
from __future__ import annotations

from typing import Dict, Optional

from flask import Blueprint, jsonify, request, session, current_app

from ..extensions import db
from ..chat.models import ChatUserContext
from ..login.models import User
from .models import UserProfile

bp = Blueprint("profile", __name__)


def _current_user() -> Optional[User]:
    uid = session.get("uid")
    if not uid:
        return None
    user = User.query.get(uid)
    if user is None:
        session.clear()
    return user


def _context_api_key_valid() -> bool:
    expected = (current_app.config.get("CHAT_CONTEXT_API_KEY") or "").strip()
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


def _get_profile(user: User, create_if_missing: bool = True) -> Optional[UserProfile]:
    if not user:
        return None
    if user.profile:
        return user.profile
    if not create_if_missing:
        return None
    return user.ensure_profile()


def _profile_to_response(profile: UserProfile) -> Dict[str, object]:
    data = profile.to_dict()
    data["weight_bmi"] = None
    try:
        height_cm = float(data.get("height_cm") or 0)
        weight_kg = float(data.get("weight_kg") or 0)
    except (TypeError, ValueError):
        height_cm = 0
        weight_kg = 0
    if height_cm > 0 and weight_kg > 0:
        m = height_cm / 100
        data["weight_bmi"] = round(weight_kg / (m * m), 2)
    return data


@bp.get("/me")
def profile_me():
    user = _current_user()
    if not user and _context_api_key_valid():
        user_id = request.args.get("user_id", type=int)
        if not user_id:
            return jsonify({"error": "user_id requerido"}), 400
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404
        profile = _get_profile(user, create_if_missing=False)
        if not profile:
            return jsonify({"profile": None}), 200
        return jsonify({"profile": _profile_to_response(profile)}), 200

    if not user:
        return jsonify({"error": "No autenticado"}), 401

    profile = _get_profile(user, create_if_missing=True)
    if profile is None:
        return jsonify({"profile": None}), 200
    db.session.flush()
    return jsonify({"profile": _profile_to_response(profile)}), 200


@bp.put("/me")
def profile_update():
    user = _current_user()
    if not user:
        return jsonify({"error": "No autenticado"}), 401
    profile = user.profile or user.ensure_profile()
    payload = request.get_json(force=True, silent=True) or {}
    try:
        profile.update_from_payload(payload)
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 400

    contexts = ChatUserContext.query.filter_by(user_id=user.id).all()
    for ctx in contexts:
        changed = False
        snapshot = profile.to_dict()
        allergies = snapshot.get("allergies")
        medical_conditions = snapshot.get("medical_conditions")
        if allergies is not None and ctx.allergies != allergies:
            ctx.allergies = allergies
            changed = True
        if medical_conditions is not None and ctx.medical_conditions != medical_conditions:
            ctx.medical_conditions = medical_conditions
            changed = True
        if changed:
            ctx.touch()

    db.session.commit()
    return jsonify({"profile": _profile_to_response(profile)}), 200

