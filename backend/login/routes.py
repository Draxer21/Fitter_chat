# backend/login/routes.py
from flask import Blueprint, request, session, jsonify
from ..extensions import db

bp = Blueprint("login", __name__)

@bp.post("/login")
def do_login():
    data = request.get_json(force=True, silent=True) or {}
    user = data.get("user"); pwd = data.get("pwd")
    if user == "admin" and pwd == "admin123":   # ejemplo; en prod usa DB y hashing
        session["uid"] = user
        session["is_admin"] = True
        return jsonify({"ok": True, "user": user, "is_admin": True})
    return jsonify({"ok": False, "error": "Credenciales inválidas"}), 401

@bp.post("/logout")
def do_logout():
    session.clear()
    return jsonify({"ok": True})


@bp.get('/me')
def me():
    uid = session.get('uid')
    if not uid:
        return jsonify({'auth': False}), 200
    return jsonify({'auth': True, 'user': uid, 'is_admin': bool(session.get('is_admin'))}), 200



