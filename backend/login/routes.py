# backend/login/routes.py
from datetime import datetime
from typing import Optional

from flask import Blueprint, request, session, jsonify
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from .models import User

bp = Blueprint("login", __name__)


def _normalize_email(value: str) -> str:
    return (value or "").strip().lower()


def _normalize_username(value: str) -> str:
    return (value or "").strip().lower()


def _current_user() -> Optional[User]:
    uid = session.get("uid")
    if not uid:
        return None
    user = User.query.get(uid)
    if user is None:
        session.clear()
    return user


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

    backup_consumed = False
    if user.has_totp_enabled():
        totp_code = (data.get("totp") or data.get("otp") or data.get("code") or data.get("token") or "").strip()
        backup_code = (data.get("backup_code") or data.get("recovery_code") or "").strip()
        verified = False

        if totp_code:
            verified = user.verify_totp_token(totp_code)
        if not verified and backup_code:
            verified = user.consume_backup_code(backup_code)
            backup_consumed = verified

        if not verified:
            db.session.rollback()
            return jsonify({"error": "Se requiere codigo MFA", "mfa_required": True}), 401

    session["uid"] = user.id
    session["is_admin"] = user.is_admin
    if backup_consumed:
        db.session.commit()
    return jsonify({"ok": True, "user": user.to_dict()}), 200


@bp.post("/logout")
def do_logout():
    session.clear()
    return jsonify({"ok": True}), 200


@bp.get('/me')
def me():
    user = _current_user()
    if not user:
        return jsonify({'auth': False}), 200
    return jsonify({'auth': True, 'user': user.to_dict(), 'is_admin': bool(user.is_admin)}), 200


@bp.get("/mfa/status")
def mfa_status():
    user = _current_user()
    if not user:
        return jsonify({"auth": False}), 401
    return jsonify({
        "auth": True,
        "enabled": user.has_totp_enabled(),
        "backup_codes_left": len(user.totp_backup_codes or []),
        "enabled_at": user.totp_enabled_at.isoformat() if user.totp_enabled_at else None,
    }), 200


@bp.post("/mfa/setup")
def mfa_setup():
    user = _current_user()
    if not user:
        return jsonify({"error": "No autenticado"}), 401

    secret = user.reset_totp_secret()
    uri = user.provisioning_uri()
    db.session.commit()
    return jsonify({"secret": secret, "otpauth_url": uri, "enabled": False}), 200


@bp.post("/mfa/confirm")
def mfa_confirm():
    user = _current_user()
    if not user:
        return jsonify({"error": "No autenticado"}), 401
    if not user.totp_secret:
        return jsonify({"error": "No hay configuracion pendiente"}), 400

    data = request.get_json(force=True, silent=True) or {}
    code = (data.get("code") or data.get("totp") or data.get("token") or data.get("otp") or "").strip()
    if not code:
        return jsonify({"error": "Codigo requerido"}), 400

    if not user.verify_totp_token(code):
        db.session.rollback()
        return jsonify({"error": "Codigo MFA invalido"}), 400

    backup_codes = user.generate_backup_codes()
    user.totp_enabled = True
    user.totp_enabled_at = datetime.utcnow()
    db.session.commit()
    return jsonify({
        "enabled": True,
        "backup_codes": backup_codes,
        "recovery_codes": backup_codes,
    }), 200


@bp.post("/mfa/disable")
def mfa_disable():
    user = _current_user()
    if not user:
        return jsonify({"error": "No autenticado"}), 401
    if not user.has_totp_enabled():
        return jsonify({"disabled": False, "enabled": False}), 200

    data = request.get_json(force=True, silent=True) or {}
    code = (data.get("code") or data.get("totp") or data.get("token") or data.get("otp") or "").strip()
    backup_code = (data.get("backup_code") or data.get("recovery_code") or "").strip()

    authorized = False
    if code and user.verify_totp_token(code):
        authorized = True
    elif backup_code and user.consume_backup_code(backup_code):
        authorized = True

    if not authorized:
        db.session.rollback()
        return jsonify({"error": "Codigo MFA invalido"}), 401

    user.disable_totp()
    db.session.commit()
    return jsonify({"disabled": True, "enabled": False}), 200
