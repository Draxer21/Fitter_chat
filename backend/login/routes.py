# backend/login/routes.py
from flask import Blueprint, request, session, jsonify
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from .models import User

bp = Blueprint("login", __name__)


def _normalize_email(value: str) -> str:
    return (value or "").strip().lower()

def _normalize_username(value: str) -> str:
    return (value or "").strip().lower()


@bp.post("/register")
def register():
    data = request.get_json(force=True, silent=True) or {}
    full_name = (data.get("full_name") or "").strip()
    email = _normalize_email(data.get("email"))
    username = _normalize_username(data.get("username") or data.get("user"))
    password = data.get("password") or ""
    is_admin = bool(data.get("is_admin"))

    if not full_name or not email or not username or not password:
        return jsonify({"error": "Nombre, usuario, correo y password son obligatorios"}), 400

    if "@" not in email:
        return jsonify({"error": "Correo no es valido"}), 400
    if not 3 <= len(username) <= 32:
        return jsonify({"error": "El usuario debe tener entre 3 y 32 caracteres"}), 400
    if not username.replace("-", "").replace("_", "").isalnum():
        return jsonify({"error": "El usuario solo acepta letras, numeros, guion y guion bajo"}), 400

    try:
        user = User.create(email=email, username=username, password=password, full_name=full_name, is_admin=is_admin)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "El correo o usuario ya esta registrado"}), 409

    session["uid"] = user.id
    session["is_admin"] = user.is_admin
    return jsonify({"ok": True, "user": user.to_dict()}), 201


@bp.post("/login")
def do_login():
    data = request.get_json(force=True, silent=True) or {}
    identifier = (data.get("username") or data.get("user") or data.get("email") or "").strip().lower()
    password = data.get("pwd") or data.get("password") or ""

    if not identifier or not password:
        return jsonify({"error": "Credenciales invalidas"}), 401

    if "@" in identifier:
        user = User.query.filter_by(email=identifier).first()
    else:
        user = User.query.filter_by(username=identifier).first()

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
