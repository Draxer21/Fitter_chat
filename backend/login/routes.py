# backend/login/routes.py
from datetime import datetime
import re
import secrets
from typing import Dict, List, Optional, Tuple

from flask import Blueprint, request, session, jsonify, current_app
from sqlalchemy.exc import IntegrityError
import jwt
from jwt import PyJWTError
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_auth_requests

from ..extensions import db
from .models import User
bp = Blueprint("login", __name__)

from ..security.csrf import (
    get_or_create_csrf_token,
    set_csrf_cookie,
    validate_csrf,
)

USERNAME_PATTERN = re.compile(r"^[a-z0-9_-]{3,32}$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


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


def _require_csrf():
    if not validate_csrf():
        return jsonify({"error": "CSRF token invalido"}), 400
    return None


def _validate_username(value: Optional[str], *, required: bool = True) -> Tuple[Optional[str], Optional[str]]:
    username = _normalize_username(value)
    if not username:
        if required:
            return None, "El usuario debe tener entre 3 y 32 caracteres"
        return None, None
    if not 3 <= len(username) <= 32:
        return None, "El usuario debe tener entre 3 y 32 caracteres"
    if not USERNAME_PATTERN.match(username):
        return None, "El usuario solo acepta letras, numeros, guion y guion bajo"
    return username, None


def _validate_email(value: Optional[str], *, required: bool = True) -> Tuple[Optional[str], Optional[str]]:
    email = _normalize_email(value or "")
    if not email:
        if required:
            return None, "El correo es obligatorio"
        return None, None
    if not EMAIL_PATTERN.match(email):
        return None, "Correo no es valido"
    return email, None


def _sanitize_username_seed(seed: Optional[str]) -> str:
    value = (seed or "fitter").lower()
    filtered = "".join(ch for ch in value if ch.isalnum() or ch in ("-", "_"))
    filtered = filtered.strip("-_")
    if len(filtered) < 3:
        filtered = f"{filtered}fit"
    return filtered[:20] or "fitter"


def _generate_unique_username(seed: Optional[str] = None, attempts: int = 8) -> str:
    base = _sanitize_username_seed(seed)
    for _ in range(attempts):
        suffix = secrets.token_hex(2)
        candidate = f"{base}-{suffix}"
        candidate = candidate[:32]
        candidate = _normalize_username(candidate)
        if not USERNAME_PATTERN.match(candidate):
            continue
        exists = User.query.filter_by(username=candidate).first()
        if not exists:
            return candidate
    raise ValueError("No se pudo generar un usuario disponible")


def _get_google_client_ids() -> List[str]:
    configured = current_app.config.get("GOOGLE_CLIENT_IDS") or []
    if isinstance(configured, str):
        configured = [item.strip() for item in configured.split(",") if item.strip()]
    return [value for value in configured if value]


def _validate_google_issuer(payload: Dict[str, object]) -> None:
    issuer = (payload.get("iss") or "").strip()
    allowed = {"https://accounts.google.com", "accounts.google.com"}
    if issuer not in allowed:
        raise ValueError("Issuer de Google no permitido")


def _verify_google_credential(credential: str) -> Dict[str, object]:
    if not credential:
        raise ValueError("Token de Google requerido")
    verify_mode = (current_app.config.get("GOOGLE_AUTH_VERIFY_MODE") or "google").strip().lower()
    if verify_mode == "mock":
        try:
            payload = jwt.decode(
                credential,
                options={
                    "verify_signature": False,
                    "verify_aud": False,
                    "verify_exp": True,
                },
            )
        except PyJWTError as exc:
            raise ValueError("Token de Google invalido") from exc
    else:
        request_adapter = google_auth_requests.Request()
        payload = google_id_token.verify_oauth2_token(
            credential,
            request_adapter,
            clock_skew_in_seconds=10,
        )
    _validate_google_issuer(payload)
    allowed = set(_get_google_client_ids())
    audience = payload.get("aud")
    if not audience:
        raise ValueError("Token de Google sin audience")
    if allowed and audience not in allowed:
        raise ValueError("Cliente de Google no permitido")
    if not payload.get("email_verified"):
        raise ValueError("El correo de Google no esta verificado")
    return payload


@bp.get("/csrf-token")
def csrf_token():
    token = get_or_create_csrf_token()
    response = jsonify({"csrf_token": token})
    response.headers["Cache-Control"] = "no-store"
    return set_csrf_cookie(response)


@bp.post("/register")
def register():
    if (error := _require_csrf()) is not None:
        return error
    data = request.get_json(force=True, silent=True) or {}
    full_name = (data.get("full_name") or "").strip()
    email = _normalize_email(data.get("email"))
    username_input = data.get("username") or data.get("user")
    username, username_error = _validate_username(username_input, required=True)
    password = data.get("password") or ""
    is_admin = bool(data.get("is_admin"))

    if not full_name or not email or not password:
        return jsonify({"error": "Nombre, usuario, correo y password son obligatorios"}), 400

    if "@" not in email:
        return jsonify({"error": "Correo no es valido"}), 400
    if username_error:
        return jsonify({"error": username_error}), 400

    try:
        user = User.create(email=email, username=username, password=password, full_name=full_name, is_admin=is_admin)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "El correo o usuario ya esta registrado"}), 409

    session["uid"] = user.id
    session["is_admin"] = user.is_admin
    session["email"] = user.email
    session["full_name"] = user.full_name
    session["username"] = user.username
    return jsonify({"ok": True, "user": user.to_dict()}), 201


@bp.post("/login")
def do_login():
    if (error := _require_csrf()) is not None:
        return error
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
    session["email"] = user.email
    session["full_name"] = user.full_name
    session["username"] = user.username
    if backup_consumed:
        db.session.commit()
    return jsonify({"ok": True, "user": user.to_dict()}), 200


@bp.post("/google")
def google_login():
    if (error := _require_csrf()) is not None:
        return error
    if not _get_google_client_ids():
        return jsonify({"error": "Inicio de sesion con Google no esta configurado"}), 503
    payload = request.get_json(force=True, silent=True) or {}
    credential = (payload.get("credential") or payload.get("token") or payload.get("id_token") or "").strip()
    preferred_username = payload.get("username") or payload.get("preferred_username")
    desired_username = None
    username_confirmed = False
    if preferred_username:
        desired_username, username_error = _validate_username(preferred_username, required=True)
        if username_error:
            return jsonify({"error": username_error}), 400
        username_confirmed = True
    try:
        google_info = _verify_google_credential(credential)
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 401
    except Exception:
        current_app.logger.exception("Error verificando token de Google")
        db.session.rollback()
        return jsonify({"error": "No se pudo validar credenciales de Google"}), 502

    email = _normalize_email(google_info.get("email"))
    sub = (google_info.get("sub") or "").strip()
    full_name = (google_info.get("name") or google_info.get("given_name") or google_info.get("family_name") or "").strip() or email

    if not email or not sub:
        return jsonify({"error": "Respuesta de Google incompleta"}), 400

    user = User.query.filter_by(google_sub=sub).first()
    if not user:
        user = User.query.filter_by(email=email).first()
        if user and not user.google_sub:
            user.google_sub = sub
    if desired_username:
        existing_username = (
            User.query.filter_by(username=desired_username).first()
        )
        if existing_username and (not user or existing_username.id != user.id):
            db.session.rollback()
            return jsonify({"error": "El usuario ya esta registrado"}), 409
    if user:
        if desired_username and not user.username_confirmed:
            user.username = desired_username
            user.username_confirmed = True
        if user.auth_provider != "google":
            user.auth_provider = "google"
        if not user.full_name and full_name:
            user.full_name = full_name
    else:
        if not desired_username:
            try:
                desired_username = _generate_unique_username(full_name or email)
            except ValueError:
                desired_username = _generate_unique_username("fitter")
        user = User.create_from_google(
            email=email,
            username=desired_username,
            full_name=full_name or email,
            google_sub=sub,
            username_confirmed=username_confirmed,
        )

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "El usuario ya esta registrado"}), 409
    session["uid"] = user.id
    session["is_admin"] = user.is_admin
    session["email"] = user.email
    session["full_name"] = user.full_name
    session["username"] = user.username
    return jsonify({"ok": True, "user": user.to_dict()}), 200


@bp.post("/logout")
def do_logout():
    if (error := _require_csrf()) is not None:
        return error
    session.clear()
    return jsonify({"ok": True}), 200


@bp.get('/me')
def me():
    user = _current_user()
    if not user:
        return jsonify({'auth': False}), 200
    return jsonify({'auth': True, 'user': user.to_dict(), 'is_admin': bool(user.is_admin)}), 200


@bp.put("/username")
def update_username():
    if (error := _require_csrf()) is not None:
        return error
    user = _current_user()
    if not user:
        return jsonify({"error": "No autenticado"}), 401
    data = request.get_json(force=True, silent=True) or {}
    desired_username, username_error = _validate_username(data.get("username"), required=True)
    if username_error:
        return jsonify({"error": username_error}), 400
    if desired_username == user.username:
        user.username_confirmed = True
        db.session.commit()
        session["username"] = user.username
        return jsonify({"ok": True, "user": user.to_dict()}), 200
    # Ensure username uniqueness
    if User.query.filter_by(username=desired_username).first():
        return jsonify({"error": "El usuario ya esta registrado"}), 409
    user.username = desired_username
    user.username_confirmed = True
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "El usuario ya esta registrado"}), 409
    session["username"] = user.username
    return jsonify({"ok": True, "user": user.to_dict()}), 200


@bp.put("/email")
def update_email():
    if (error := _require_csrf()) is not None:
        return error
    user = _current_user()
    if not user:
        return jsonify({"error": "No autenticado"}), 401
    data = request.get_json(force=True, silent=True) or {}
    desired_email, email_error = _validate_email(data.get("email") or data.get("new_email"), required=True)
    if email_error:
        return jsonify({"error": email_error}), 400
    if desired_email == user.email:
        session["email"] = user.email
        return jsonify({"ok": True, "user": user.to_dict()}), 200
    existing = User.query.filter(User.email == desired_email, User.id != user.id).first()
    if existing:
        return jsonify({"error": "El correo ya esta registrado"}), 409
    user.email = desired_email
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "El correo ya esta registrado"}), 409
    session["email"] = user.email
    return jsonify({"ok": True, "user": user.to_dict()}), 200


@bp.put("/password")
def update_password():
    if (error := _require_csrf()) is not None:
        return error
    user = _current_user()
    if not user:
        return jsonify({"error": "No autenticado"}), 401
    data = request.get_json(force=True, silent=True) or {}
    current_password = (
        data.get("current_password")
        or data.get("password_current")
        or data.get("old_password")
        or data.get("currentPassword")
    )
    new_password = (
        data.get("new_password")
        or data.get("password_new")
        or data.get("newPassword")
        or data.get("password")
    )
    confirm_password = data.get("confirm_password") or data.get("password_confirm") or data.get("confirm")

    if not new_password or not str(new_password).strip():
        return jsonify({"error": "Nueva contraseña requerida"}), 400
    if len(str(new_password).strip()) < 6:
        return jsonify({"error": "La contraseña debe tener al menos 6 caracteres"}), 400
    if confirm_password and str(new_password).strip() != str(confirm_password).strip():
        return jsonify({"error": "Las contraseñas no coinciden"}), 400
    if user.password_hash:
        if not current_password or not user.check_password(current_password):
            return jsonify({"error": "Contraseña actual incorrecta"}), 400

    try:
        user.set_password(str(new_password))
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 400
    return jsonify({"ok": True, "user": user.to_dict()}), 200


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
    if (error := _require_csrf()) is not None:
        return error
    user = _current_user()
    if not user:
        return jsonify({"error": "No autenticado"}), 401

    secret = user.reset_totp_secret()
    uri = user.provisioning_uri()
    db.session.commit()
    return jsonify({"secret": secret, "otpauth_url": uri, "enabled": False}), 200


@bp.post("/mfa/confirm")
def mfa_confirm():
    if (error := _require_csrf()) is not None:
        return error
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
    if (error := _require_csrf()) is not None:
        return error
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


def _sanitize_optional_string(value: Optional[object], *, max_length: Optional[int] = None) -> Optional[str]:
    if value is None:
        return None
    normalized = str(value).strip()
    if not normalized:
        return None
    if max_length is not None and len(normalized) > max_length:
        return normalized[:max_length]
    return normalized


def _parse_optional_float(
    value: Optional[object],
    *,
    field: str,
    minimum: Optional[float] = None,
    maximum: Optional[float] = None,
):
    if value is None or value == "":
        return None, None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None, f"{field} debe ser un numero"
    if minimum is not None and parsed < minimum:
        return None, f"{field} debe ser mayor o igual a {minimum}"
    if maximum is not None and parsed > maximum:
        return None, f"{field} debe ser menor o igual a {maximum}"
    return parsed, None


def _parse_health_conditions(value: Optional[object]):
    if value is None:
        return None, None
    items: List[str]
    if isinstance(value, str):
        parts = [part.strip() for part in value.split(",")]
        items = [part for part in parts if part]
    elif isinstance(value, list):
        cleaned: List[str] = []
        for item in value:
            item_str = str(item).strip()
            if item_str:
                cleaned.append(item_str)
        items = cleaned
    else:
        return None, "health_conditions debe ser una lista o una cadena"
    if not items:
        return [], None
    return items, None


@bp.get("/profile")
def profile_detail():
    user = _current_user()
    if not user:
        return jsonify({"error": "No autenticado"}), 401
    return jsonify({"profile": user.to_dict()}), 200


@bp.put("/profile")
def profile_update():
    user = _current_user()
    if not user:
        return jsonify({"error": "No autenticado"}), 401

    data = request.get_json(force=True, silent=True) or {}
    errors: List[str] = []
    profile_payload = {}
    if "full_name" in data:
        new_name = _sanitize_optional_string(data.get("full_name"), max_length=120)
        if not new_name:
            errors.append("full_name no puede estar vacio")
        else:
            user.full_name = new_name

    weight, error = _parse_optional_float(data.get("weight_kg"), field="weight_kg", minimum=0.0)
    if error:
        errors.append(error)
    elif "weight_kg" in data:
        profile_payload["weight_kg"] = weight

    height, error = _parse_optional_float(data.get("height_cm"), field="height_cm", minimum=0.0)
    if error:
        errors.append(error)
    elif "height_cm" in data:
        profile_payload["height_cm"] = height

    body_fat, error = _parse_optional_float(
        data.get("body_fat_percent"), field="body_fat_percent", minimum=0.0, maximum=100.0
    )
    if error:
        errors.append(error)
    elif "body_fat_percent" in data:
        profile_payload["body_fat_percent"] = body_fat

    if "fitness_goal" in data:
        profile_payload["fitness_goal"] = _sanitize_optional_string(data.get("fitness_goal"), max_length=255)

    if "dietary_preferences" in data:
        profile_payload["dietary_preferences"] = _sanitize_optional_string(
            data.get("dietary_preferences"), max_length=255
        )

    if "additional_notes" in data:
        profile_payload["additional_notes"] = _sanitize_optional_string(
            data.get("additional_notes"), max_length=2000
        )

    if "somatotipo" in data:
        profile_payload["somatotipo"] = _sanitize_optional_string(data.get("somatotipo"), max_length=32)

    if "health_conditions" in data:
        conditions, error = _parse_health_conditions(data.get("health_conditions"))
        if error:
            errors.append(error)
        else:
            # Se almacena como texto simplificado para el perfil cifrado.
            profile_payload["medical_conditions"] = ", ".join(conditions) if conditions else None

    if errors:
        db.session.rollback()
        return jsonify({"error": "; ".join(errors)}), 400

    profile = user.ensure_profile()
    try:
        profile.update_from_payload(profile_payload)
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 400

    # Limpiamos campos de salud en texto plano en el modelo User.
    user.weight_kg = None
    user.height_cm = None
    user.body_fat_percent = None
    user.fitness_goal = None
    user.dietary_preferences = None
    user.health_conditions = None
    user.additional_notes = None

    db.session.commit()
    return jsonify({"ok": True, "profile": user.to_dict()}), 200
