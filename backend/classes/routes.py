from __future__ import annotations

from datetime import datetime
from typing import Optional

from flask import Blueprint, jsonify, request, session

from ..extensions import db
from .models import ClassSession, FitnessClass

bp = Blueprint("classes", __name__)


def _is_admin() -> bool:
    return bool(session.get("is_admin"))


def _require_admin():
    if not _is_admin():
        return jsonify({"error": "No autorizado"}), 403
    return None


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, str) and value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _parse_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_bool(value: Optional[object]) -> Optional[bool]:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "si"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
    return None


@bp.get("/public")
def list_public_classes():
    active = request.args.get("active")
    search = request.args.get("search")

    query = FitnessClass.query
    if active is None:
        query = query.filter_by(active=True)
    else:
        active_value = _parse_bool(active)
        if active_value is None:
            return jsonify({"error": "Parametro 'active' invalido."}), 400
        query = query.filter_by(active=active_value)
    if search:
        query = query.filter(FitnessClass.name.ilike(f"%{search}%"))

    classes = query.order_by(FitnessClass.name.asc()).all()
    return jsonify({"classes": [item.to_dict() for item in classes]}), 200


@bp.get("/public/sessions")
def list_public_sessions():
    class_id = request.args.get("class_id")
    start = _parse_datetime(request.args.get("start"))
    end = _parse_datetime(request.args.get("end"))

    query = ClassSession.query
    if class_id is not None:
        class_id_value = _parse_int(class_id)
        if class_id_value is None:
            return jsonify({"error": "class_id invalido."}), 400
        query = query.filter_by(class_id=class_id_value)
    if start:
        query = query.filter(ClassSession.start_time >= start)
    if end:
        query = query.filter(ClassSession.start_time <= end)

    sessions = query.order_by(ClassSession.start_time.asc()).all()
    return jsonify({"sessions": [item.to_dict() for item in sessions]}), 200


@bp.get("/")
def list_classes():
    auth = _require_admin()
    if auth:
        return auth

    active = request.args.get("active")
    search = request.args.get("search")

    query = FitnessClass.query
    if active is not None:
        active_value = _parse_bool(active)
        if active_value is None:
            return jsonify({"error": "Parametro 'active' invalido."}), 400
        query = query.filter_by(active=active_value)
    if search:
        query = query.filter(FitnessClass.name.ilike(f"%{search}%"))

    classes = query.order_by(FitnessClass.name.asc()).all()
    return jsonify({"classes": [item.to_dict() for item in classes]}), 200


@bp.post("/")
def create_class():
    auth = _require_admin()
    if auth:
        return auth

    data = request.get_json(force=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "El nombre es obligatorio."}), 400

    duration_min = _parse_int(data.get("duration_min"))
    capacity = _parse_int(data.get("capacity"))

    fitness_class = FitnessClass(
        name=name,
        description=data.get("description"),
        instructor=data.get("instructor"),
        duration_min=duration_min or 60,
        capacity=capacity if capacity is not None else 10,
        location=data.get("location"),
        active=_parse_bool(data.get("active")) if data.get("active") is not None else True,
    )

    db.session.add(fitness_class)
    db.session.commit()
    return jsonify({"class": fitness_class.to_dict()}), 201


@bp.get("/<int:class_id>")
def get_class(class_id: int):
    auth = _require_admin()
    if auth:
        return auth

    fitness_class = db.session.get(FitnessClass, class_id)
    if not fitness_class:
        return jsonify({"error": "Clase no encontrada."}), 404
    return jsonify({"class": fitness_class.to_dict()}), 200


@bp.patch("/<int:class_id>")
@bp.put("/<int:class_id>")
def update_class(class_id: int):
    auth = _require_admin()
    if auth:
        return auth

    fitness_class = db.session.get(FitnessClass, class_id)
    if not fitness_class:
        return jsonify({"error": "Clase no encontrada."}), 404

    data = request.get_json(force=True) or {}
    if "name" in data:
        name = (data.get("name") or "").strip()
        if not name:
            return jsonify({"error": "El nombre no puede estar vacio."}), 400
        fitness_class.name = name
    if "description" in data:
        fitness_class.description = data.get("description")
    if "instructor" in data:
        fitness_class.instructor = data.get("instructor")
    if "duration_min" in data:
        duration = _parse_int(data.get("duration_min"))
        if duration is None or duration <= 0:
            return jsonify({"error": "duration_min invalido."}), 400
        fitness_class.duration_min = duration
    if "capacity" in data:
        capacity = _parse_int(data.get("capacity"))
        if capacity is None or capacity < 0:
            return jsonify({"error": "capacity invalido."}), 400
        fitness_class.capacity = capacity
    if "location" in data:
        fitness_class.location = data.get("location")
    if "active" in data:
        active = _parse_bool(data.get("active"))
        if active is None:
            return jsonify({"error": "active invalido."}), 400
        fitness_class.active = active

    db.session.commit()
    return jsonify({"class": fitness_class.to_dict()}), 200


@bp.delete("/<int:class_id>")
def delete_class(class_id: int):
    auth = _require_admin()
    if auth:
        return auth

    fitness_class = db.session.get(FitnessClass, class_id)
    if not fitness_class:
        return jsonify({"error": "Clase no encontrada."}), 404

    db.session.delete(fitness_class)
    db.session.commit()
    return jsonify({"message": "Clase eliminada."}), 200


@bp.get("/<int:class_id>/sessions")
def list_sessions(class_id: int):
    auth = _require_admin()
    if auth:
        return auth

    fitness_class = db.session.get(FitnessClass, class_id)
    if not fitness_class:
        return jsonify({"error": "Clase no encontrada."}), 404

    start = _parse_datetime(request.args.get("start"))
    end = _parse_datetime(request.args.get("end"))

    query = ClassSession.query.filter_by(class_id=class_id)
    if start:
        query = query.filter(ClassSession.start_time >= start)
    if end:
        query = query.filter(ClassSession.start_time <= end)

    sessions = query.order_by(ClassSession.start_time.asc()).all()
    return jsonify({"sessions": [item.to_dict() for item in sessions]}), 200


@bp.post("/<int:class_id>/sessions")
def create_session(class_id: int):
    auth = _require_admin()
    if auth:
        return auth

    fitness_class = db.session.get(FitnessClass, class_id)
    if not fitness_class:
        return jsonify({"error": "Clase no encontrada."}), 404

    data = request.get_json(force=True) or {}
    start_time = _parse_datetime(data.get("start_time"))
    if not start_time:
        return jsonify({"error": "start_time es obligatorio (ISO-8601)."}), 400

    duration_override = _parse_int(data.get("duration_override"))
    capacity_override = _parse_int(data.get("capacity_override"))
    is_exclusive = _parse_bool(data.get("is_exclusive"))

    session = ClassSession(
        class_id=class_id,
        start_time=start_time,
        duration_override=duration_override,
        capacity_override=capacity_override,
        is_exclusive=is_exclusive if is_exclusive is not None else False,
        notes=data.get("notes"),
    )

    db.session.add(session)
    db.session.commit()
    return jsonify({"session": session.to_dict()}), 201


@bp.get("/sessions/<int:session_id>")
def get_session(session_id: int):
    auth = _require_admin()
    if auth:
        return auth

    session_item = db.session.get(ClassSession, session_id)
    if not session_item:
        return jsonify({"error": "Sesion no encontrada."}), 404
    return jsonify({"session": session_item.to_dict()}), 200


@bp.patch("/sessions/<int:session_id>")
@bp.put("/sessions/<int:session_id>")
def update_session(session_id: int):
    auth = _require_admin()
    if auth:
        return auth

    session_item = db.session.get(ClassSession, session_id)
    if not session_item:
        return jsonify({"error": "Sesion no encontrada."}), 404

    data = request.get_json(force=True) or {}
    if "start_time" in data:
        start_time = _parse_datetime(data.get("start_time"))
        if not start_time:
            return jsonify({"error": "start_time invalido."}), 400
        session_item.start_time = start_time
    if "duration_override" in data:
        duration_override = _parse_int(data.get("duration_override"))
        if duration_override is not None and duration_override <= 0:
            return jsonify({"error": "duration_override invalido."}), 400
        session_item.duration_override = duration_override
    if "capacity_override" in data:
        capacity_override = _parse_int(data.get("capacity_override"))
        if capacity_override is not None and capacity_override < 0:
            return jsonify({"error": "capacity_override invalido."}), 400
        session_item.capacity_override = capacity_override
    if "is_exclusive" in data:
        is_exclusive = _parse_bool(data.get("is_exclusive"))
        if is_exclusive is None:
            return jsonify({"error": "is_exclusive invalido."}), 400
        session_item.is_exclusive = is_exclusive
    if "notes" in data:
        session_item.notes = data.get("notes")

    db.session.commit()
    return jsonify({"session": session_item.to_dict()}), 200


@bp.delete("/sessions/<int:session_id>")
def delete_session(session_id: int):
    auth = _require_admin()
    if auth:
        return auth

    session_item = db.session.get(ClassSession, session_id)
    if not session_item:
        return jsonify({"error": "Sesion no encontrada."}), 404

    db.session.delete(session_item)
    db.session.commit()
    return jsonify({"message": "Sesion eliminada."}), 200
