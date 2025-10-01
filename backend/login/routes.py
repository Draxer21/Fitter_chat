# backend/login/routes.py
from flask import Blueprint, request, session, jsonify
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from .models import User

bp = Blueprint("login", __name__)


def _normalize_email(value: str) -> str:
    return (value or "").strip().lower()


@bp.post("/register")
def register():
    data = request.get_json(force=True, silent=True) or {}
    full_name = (data.get("full_name") or "").strip()
    email = _normalize_email(data.get("email"))
    password = data.get("password") or ""
    is_admin = bool(data.get("is_admin"))

    if not full_name or not email or not password:
        return jsonify({"error": "Nombre, correo y password son obligatorios"}), 400

    if "@" not in email:
        return jsonify({"error": "Correo no es valido"}), 400

    try:
        user = User.create(email=email, password=password, full_name=full_name, is_admin=is_admin)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "El correo ya esta registrado"}), 409

    session["uid"] = user.id
    session["is_admin"] = user.is_admin
    return jsonify({"ok": True, "user": user.to_dict()}), 201


@bp.post("/login")
def do_login():
    data = request.get_json(force=True, silent=True) or {}
    email = _normalize_email(data.get("user") or data.get("email"))
    password = data.get("pwd") or data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Credenciales invalidas"}), 401

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Credenciales invalidas"}), 401

    session["uid"] = user.id
    session["is_admin"] = user.is_admin
    return jsonify({"ok": True, "user": user.to_dict()}), 200


@bp.post("/logout")
def do_logout():
    session.clear()
    return jsonify({"ok": True}), 200


@bp.get('/me')
def me():
    uid = session.get('uid')
    if not uid:
        return jsonify({'auth': False}), 200
    user = User.query.get(uid)
    if not user:
        session.clear()
        return jsonify({'auth': False}), 200
    return jsonify({'auth': True, 'user': user.to_dict(), 'is_admin': bool(user.is_admin)}), 200
