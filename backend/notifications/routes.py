# backend/notifications/routes.py
from __future__ import annotations

import os
from typing import Optional

from flask import Blueprint, jsonify, request, session, send_file

from ..extensions import db
from ..login.models import User
from .email import send_email
from .document_generator import (
    generate_routine_pdf,
    generate_routine_docx,
    generate_diet_pdf,
    generate_diet_docx,
)

bp = Blueprint("notifications", __name__)

# API key para permitir llamadas desde action server sin sesión web
CONTEXT_API_KEY = os.getenv("BACKEND_CONTEXT_KEY", "").strip()


def _current_user() -> Optional[User]:
    uid = session.get("uid")
    if not uid:
        return None
    user = User.query.get(uid)
    if user is None:
        session.clear()
    return user


def _validate_api_key() -> bool:
    """Valida si la petición tiene una API key válida."""
    if not CONTEXT_API_KEY:
        return False
    provided_key = request.headers.get("X-Context-Key", "").strip()
    return provided_key == CONTEXT_API_KEY


@bp.post("/daily-routine")
def send_daily_routine():
    """
    Envía un correo con la rutina diaria a un usuario específico.

    Requiere sesión activa O API key válida. Usuarios no administradores solo 
    pueden enviarse correos a sí mismos (cuando usan sesión web).
    """
    # Intentar autenticación por sesión
    actor = _current_user()
    
    # Si no hay sesión, intentar validar por API key
    has_valid_api_key = False
    if not actor:
        has_valid_api_key = _validate_api_key()
        if not has_valid_api_key:
            return jsonify({"error": "No autenticado"}), 401

    data = request.get_json(force=True, silent=True) or {}

    # user_id optional: if caller is a logged-in user and user_id is omitted,
    # send to the actor user.
    user_id_raw = data.get("user_id")
    target = None
    if user_id_raw is None and actor:
        target = actor
    else:
        try:
            user_id = int(user_id_raw)
        except (TypeError, ValueError):
            return jsonify({"error": "user_id inválido"}), 400
        target = User.query.get(user_id)
        if not target:
            return jsonify({"error": "Usuario no encontrado"}), 404

    # If actor is present and we're using session, validate permissions
    if actor and not has_valid_api_key:
        if not actor.is_admin and actor.id != target.id:
            return jsonify({"error": "No autorizado"}), 403

    body = (data.get("body") or "").strip()
    if not body:
        # if routine_data provided, build a reasonable body from it
        routine_data = data.get("routine_data") or {}
        if routine_data and isinstance(routine_data, dict):
            # Simple text fallback
            lines = [routine_data.get("header", "Tu rutina Fitter"), "", "Detalle de ejercicios:"]
            for ex in routine_data.get("exercises", []):
                name = ex.get("nombre") or ex.get("name") or "Ejercicio"
                series = ex.get("series") or "-"
                reps = ex.get("repeticiones") or ex.get("reps") or "-"
                lines.append(f"- {name} | {series} x {reps}")
            body = "\n".join(lines).strip()
    if not body:
        return jsonify({"error": "body es obligatorio"}), 400

    subject = (data.get("subject") or "Tu rutina diaria Fitter").strip()
    if not subject:
        subject = "Tu rutina diaria Fitter"

    # handle attachment request
    attach = bool(data.get("attach", False))
    try:
        if attach:
            routine_data = data.get("routine_data") or {}
            # allow the caller to request PDF or docx
            fmt = (data.get("format") or "pdf").lower()
            if fmt == "docx":
                buf = generate_routine_docx(routine_data)
                filename = f"{routine_data.get('routine_id', 'rutina')}.docx"
            else:
                buf = generate_routine_pdf(routine_data)
                filename = f"{routine_data.get('routine_id', 'rutina')}.pdf"
            attachment_bytes = buf.getvalue()
        else:
            attachment_bytes = None
            filename = None

        send_email(
            to_email=target.email,
            subject=subject,
            body=body,
            from_name="Fitter",
            attachment_bytes=attachment_bytes,
            attachment_filename=filename,
        )
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 500
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": "No se pudo enviar el correo", "details": str(exc)}), 502

    return jsonify({"ok": True}), 200


@bp.post("/download-routine")
def download_routine():
    """
    Genera y descarga una rutina en formato PDF o DOCX.
    
    Body:
        - format: "pdf" o "docx"
        - routine_data: estructura completa de routine_detail
    """
    data = request.get_json(force=True, silent=True) or {}
    
    format_type = (data.get("format") or "pdf").lower()
    if format_type not in {"pdf", "docx"}:
        return jsonify({"error": "Formato inválido, usa 'pdf' o 'docx'"}), 400
    
    routine_data = data.get("routine_data")
    if not routine_data or not isinstance(routine_data, dict):
        return jsonify({"error": "routine_data es obligatorio y debe ser un objeto"}), 400
    
    try:
        if format_type == "pdf":
            buffer = generate_routine_pdf(routine_data)
            mimetype = "application/pdf"
            extension = "pdf"
        else:
            buffer = generate_routine_docx(routine_data)
            mimetype = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            extension = "docx"
        
        # Nombre del archivo
        routine_id = routine_data.get("routine_id", "rutina")
        filename = f"{routine_id}.{extension}"
        
        return send_file(
            buffer,
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
    except Exception as exc:
        return jsonify({"error": "No se pudo generar el documento", "details": str(exc)}), 500


@bp.get('/catalog')
def get_food_catalog():
    """Endpoint simple para consultar el catálogo local de alimentos.
    Query params:
      - category: filtro por categoría/tag parcial
      - kcal: número (target kcal, se usa rango por defecto)
      - exclude_allergens: comma-separated list
      - limit: máximo items
    """
    params = request.args or {}
    category = params.get('category')
    kcal_raw = params.get('kcal')
    exclude_raw = params.get('exclude_allergens')
    limit_raw = params.get('limit')

    try:
        limit = int(limit_raw) if limit_raw else 50
    except Exception:
        limit = 50

    try:
        kcal = float(kcal_raw) if kcal_raw else None
    except Exception:
        kcal = None

    exclude = [s.strip().lower() for s in (exclude_raw or '').split(',') if s.strip()]

    # localizar archivo de catálogo
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    candidates = [
        os.path.join(base_dir, 'data', 'food_catalog.json'),
        os.path.join(base_dir, 'data', 'food_catalog_sample.json')
    ]
    catalog_path = None
    for p in candidates:
        if os.path.exists(p):
            catalog_path = p
            break
    if not catalog_path:
        return jsonify({'items': []})

    try:
        with open(catalog_path, 'r', encoding='utf-8') as f:
            items = json.load(f)
    except Exception:
        return jsonify({'items': []})

    # apply filters
    def item_ok(it):
        if category:
            cats = [c.lower() for c in (it.get('categories') or [])]
            if not any(category.lower() in c for c in cats):
                return False
        if exclude:
            item_all = [a.lower() for a in (it.get('allergens') or [])]
            if any(e in item_all for e in exclude):
                return False
        return True

    filtered = [it for it in items if item_ok(it)]

    if kcal is not None:
        # approximate match within 30%
        tol = 0.3
        out = []
        for it in filtered:
            ek = it.get('energy_kcal_100g')
            if ek is None:
                continue
            if kcal * (1 - tol) <= ek <= kcal * (1 + tol):
                out.append(it)
        filtered = out

    return jsonify({'items': filtered[:limit]})


@bp.post("/diet")
def send_diet():
    """
    Envía una dieta por correo (similar a /daily-routine).
    Body:
      - user_id (opcional)
      - body (texto del correo, opcional)
      - diet_data (estructura de la dieta)
      - attach: bool (adjuntar documento)
      - format: 'pdf' o 'docx'
    """
    actor = _current_user()
    has_valid_api_key = False
    if not actor:
        has_valid_api_key = _validate_api_key()
        if not has_valid_api_key:
            return jsonify({"error": "No autenticado"}), 401

    data = request.get_json(force=True, silent=True) or {}
    user_id_raw = data.get("user_id")
    target = None
    if user_id_raw is None and actor:
        target = actor
    else:
        try:
            user_id = int(user_id_raw)
        except (TypeError, ValueError):
            return jsonify({"error": "user_id inválido"}), 400
        target = User.query.get(user_id)
        if not target:
            return jsonify({"error": "Usuario no encontrado"}), 404

    if actor and not has_valid_api_key:
        if not actor.is_admin and actor.id != target.id:
            return jsonify({"error": "No autorizado"}), 403

    body = (data.get("body") or "").strip()
    if not body:
        diet_data = data.get("diet_data") or {}
        if diet_data and isinstance(diet_data, dict):
            lines = [diet_data.get('header', 'Tu dieta Fitter'), '']
            for meal in diet_data.get('meals', []):
                lines.append(f"{meal.get('name','Comida')}:")
                for it in meal.get('items', []):
                    # Handle both string format and object format
                    if isinstance(it, str):
                        lines.append(f" - {it}")
                    elif isinstance(it, dict):
                        name = it.get('name', '')
                        qty = it.get('qty', '')
                        kcal = it.get('kcal', '')
                        item_text = f" - {name}"
                        if qty:
                            item_text += f" ({qty}"
                            if kcal:
                                item_text += f", {kcal} kcal"
                            item_text += ")"
                        lines.append(item_text)
            body = "\n".join(lines)

    if not body:
        return jsonify({"error": "body es obligatorio"}), 400

    subject = (data.get("subject") or "Tu plan de alimentación Fitter").strip()
    if not subject:
        subject = "Tu plan de alimentación Fitter"

    attach = bool(data.get("attach", False))
    try:
        if attach:
            diet_data = data.get('diet_data') or {}
            fmt = (data.get('format') or 'pdf').lower()
            if fmt == 'docx':
                buf = generate_diet_docx(diet_data)
                filename = f"{diet_data.get('diet_id','dieta')}.docx"
            else:
                buf = generate_diet_pdf(diet_data)
                filename = f"{diet_data.get('diet_id','dieta')}.pdf"
            attachment_bytes = buf.getvalue()
        else:
            attachment_bytes = None
            filename = None

        send_email(
            to_email=target.email,
            subject=subject,
            body=body,
            from_name="Fitter",
            attachment_bytes=attachment_bytes,
            attachment_filename=filename,
        )
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": "No se pudo enviar el correo", "details": str(exc)}), 502

    return jsonify({"ok": True}), 200


@bp.post('/download-diet')
def download_diet():
    data = request.get_json(force=True, silent=True) or {}
    format_type = (data.get('format') or 'pdf').lower()
    if format_type not in {'pdf', 'docx'}:
        return jsonify({'error': "Formato inválido, usa 'pdf' o 'docx'"}), 400
    diet_data = data.get('diet_data')
    if not diet_data or not isinstance(diet_data, dict):
        return jsonify({'error': 'diet_data es obligatorio y debe ser un objeto'}), 400
    try:
        if format_type == 'pdf':
            buffer = generate_diet_pdf(diet_data)
            mimetype = 'application/pdf'
            extension = 'pdf'
        else:
            buffer = generate_diet_docx(diet_data)
            mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            extension = 'docx'
        diet_id = diet_data.get('diet_id', 'dieta')
        filename = f"{diet_id}.{extension}"
        return send_file(buffer, mimetype=mimetype, as_attachment=True, download_name=filename)
    except Exception as exc:
        return jsonify({'error': 'No se pudo generar el documento', 'details': str(exc)}), 500


