"""CRUD endpoints for diet and routine plans."""
from __future__ import annotations

import uuid
from typing import Optional

from flask import Blueprint, current_app, jsonify, request, session
from sqlalchemy.exc import IntegrityError, ProgrammingError

from ..extensions import db
from ..login.models import User
from ..security.session import context_api_key_valid, session_uid
from .models import DietPlan, RoutinePlan
from .schemas import (
    require_fields,
    is_json_object,
    dietplan_to_dict,
    routineplan_to_dict,
)

plans_bp = Blueprint("plans", __name__)


def _resolve_user_for_request() -> Optional[User]:
    uid = session_uid(session)
    if uid:
        return User.query.get(uid)

    expected = current_app.config.get("CHAT_CONTEXT_API_KEY", "")
    if not context_api_key_valid(request.headers, expected):
        return None

    user_id = request.args.get("user_id", type=int)
    if not user_id:
        payload = request.get_json(silent=True) or {}
        if isinstance(payload, dict):
            user_id = payload.get("user_id")
    if not user_id:
        return None
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return None
    return User.query.get(user_id)


# ---------------------------
# Diet Plans
# ---------------------------


@plans_bp.post("/diet-plans")
def create_diet_plan():
    user = _resolve_user_for_request()
    if not user:
        return jsonify({"error": "No autenticado"}), 401

    payload = request.get_json(silent=True) or {}
    ok, err = require_fields(payload, ["title", "content"])
    if not ok:
        return jsonify(err), 400

    title = payload.get("title")
    if not isinstance(title, str) or not title.strip():
        return jsonify({"error": "invalid_title"}), 400
    if not is_json_object(payload.get("content")):
        return jsonify({"error": "content_must_be_object"}), 400

    plan = DietPlan(
        user_id=user.id,
        title=title.strip(),
        goal=(payload.get("goal") or "").strip(),
        content=payload["content"],
    )

    db.session.add(plan)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "db_error"}), 500

    return jsonify(dietplan_to_dict(plan)), 201


@plans_bp.get("/diet-plans")
def list_diet_plans():
    user = _resolve_user_for_request()
    if not user:
        return jsonify({"error": "No autenticado"}), 401

    try:
        plans = (
            DietPlan.query
            .filter(DietPlan.user_id == user.id)
            .order_by(DietPlan.created_at.desc())
            .all()
        )
    except ProgrammingError:
        current_app.logger.warning("Tabla diet_plans no existe. Ejecuta migraciones.")
        return jsonify([]), 200
    summaries = [
        {
            "id": str(p.id),
            "user_id": p.user_id,
            "title": p.title,
            "goal": p.goal or "",
            "version": p.version,
            "created_at": p.created_at.isoformat() + "Z" if p.created_at else None,
            "updated_at": p.updated_at.isoformat() + "Z" if p.updated_at else None,
        }
        for p in plans
    ]
    return jsonify(summaries), 200


@plans_bp.get("/diet-plans/<string:plan_id>")
def get_diet_plan(plan_id: str):
    user = _resolve_user_for_request()
    if not user:
        return jsonify({"error": "No autenticado"}), 401

    try:
        pid = uuid.UUID(plan_id)
    except ValueError:
        return jsonify({"error": "invalid_id"}), 400

    plan = DietPlan.query.filter(DietPlan.id == pid, DietPlan.user_id == user.id).first()
    if not plan:
        return jsonify({"error": "not_found"}), 404

    return jsonify(dietplan_to_dict(plan)), 200


@plans_bp.patch("/diet-plans/<string:plan_id>")
def update_diet_plan(plan_id: str):
    user = _resolve_user_for_request()
    if not user:
        return jsonify({"error": "No autenticado"}), 401

    try:
        pid = uuid.UUID(plan_id)
    except ValueError:
        return jsonify({"error": "invalid_id"}), 400

    plan = DietPlan.query.filter(DietPlan.id == pid, DietPlan.user_id == user.id).first()
    if not plan:
        return jsonify({"error": "not_found"}), 404

    payload = request.get_json(silent=True) or {}

    if "title" in payload:
        title = payload.get("title")
        if not isinstance(title, str) or not title.strip():
            return jsonify({"error": "invalid_title"}), 400
        plan.title = title.strip()

    if "goal" in payload:
        goal = payload.get("goal")
        if goal is None:
            plan.goal = ""
        elif not isinstance(goal, str):
            return jsonify({"error": "invalid_goal"}), 400
        else:
            plan.goal = goal.strip()

    if "content" in payload:
        if not is_json_object(payload.get("content")):
            return jsonify({"error": "content_must_be_object"}), 400
        plan.content = payload["content"]

    plan.version = (plan.version or 1) + 1

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "db_error"}), 500

    return jsonify(dietplan_to_dict(plan)), 200


@plans_bp.delete("/diet-plans/<string:plan_id>")
def delete_diet_plan(plan_id: str):
    user = _resolve_user_for_request()
    if not user:
        return jsonify({"error": "No autenticado"}), 401

    try:
        pid = uuid.UUID(plan_id)
    except ValueError:
        return jsonify({"error": "invalid_id"}), 400

    plan = DietPlan.query.filter(DietPlan.id == pid, DietPlan.user_id == user.id).first()
    if not plan:
        return jsonify({"error": "not_found"}), 404

    db.session.delete(plan)
    db.session.commit()
    return ("", 204)


# ---------------------------
# Routine Plans
# ---------------------------


@plans_bp.post("/routine-plans")
def create_routine_plan():
    user = _resolve_user_for_request()
    if not user:
        return jsonify({"error": "No autenticado"}), 401

    payload = request.get_json(silent=True) or {}
    ok, err = require_fields(payload, ["title", "content"])
    if not ok:
        return jsonify(err), 400

    title = payload.get("title")
    if not isinstance(title, str) or not title.strip():
        return jsonify({"error": "invalid_title"}), 400
    if not is_json_object(payload.get("content")):
        return jsonify({"error": "content_must_be_object"}), 400

    plan = RoutinePlan(
        user_id=user.id,
        title=title.strip(),
        objective=(payload.get("objective") or "").strip(),
        content=payload["content"],
    )

    db.session.add(plan)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "db_error"}), 500

    return jsonify(routineplan_to_dict(plan)), 201


@plans_bp.get("/routine-plans")
def list_routine_plans():
    user = _resolve_user_for_request()
    if not user:
        return jsonify({"error": "No autenticado"}), 401

    try:
        plans = (
            RoutinePlan.query
            .filter(RoutinePlan.user_id == user.id)
            .order_by(RoutinePlan.created_at.desc())
            .all()
        )
    except ProgrammingError:
        current_app.logger.warning("Tabla routine_plans no existe. Ejecuta migraciones.")
        return jsonify([]), 200
    summaries = [
        {
            "id": str(p.id),
            "user_id": p.user_id,
            "title": p.title,
            "objective": p.objective or "",
            "version": p.version,
            "created_at": p.created_at.isoformat() + "Z" if p.created_at else None,
            "updated_at": p.updated_at.isoformat() + "Z" if p.updated_at else None,
        }
        for p in plans
    ]
    return jsonify(summaries), 200


@plans_bp.get("/routine-plans/<string:plan_id>")
def get_routine_plan(plan_id: str):
    user = _resolve_user_for_request()
    if not user:
        return jsonify({"error": "No autenticado"}), 401

    try:
        pid = uuid.UUID(plan_id)
    except ValueError:
        return jsonify({"error": "invalid_id"}), 400

    plan = RoutinePlan.query.filter(RoutinePlan.id == pid, RoutinePlan.user_id == user.id).first()
    if not plan:
        return jsonify({"error": "not_found"}), 404

    return jsonify(routineplan_to_dict(plan)), 200


@plans_bp.patch("/routine-plans/<string:plan_id>")
def update_routine_plan(plan_id: str):
    user = _resolve_user_for_request()
    if not user:
        return jsonify({"error": "No autenticado"}), 401

    try:
        pid = uuid.UUID(plan_id)
    except ValueError:
        return jsonify({"error": "invalid_id"}), 400

    plan = RoutinePlan.query.filter(RoutinePlan.id == pid, RoutinePlan.user_id == user.id).first()
    if not plan:
        return jsonify({"error": "not_found"}), 404

    payload = request.get_json(silent=True) or {}

    if "title" in payload:
        title = payload.get("title")
        if not isinstance(title, str) or not title.strip():
            return jsonify({"error": "invalid_title"}), 400
        plan.title = title.strip()

    if "objective" in payload:
        objective = payload.get("objective")
        if objective is None:
            plan.objective = ""
        elif not isinstance(objective, str):
            return jsonify({"error": "invalid_objective"}), 400
        else:
            plan.objective = objective.strip()

    if "content" in payload:
        if not is_json_object(payload.get("content")):
            return jsonify({"error": "content_must_be_object"}), 400
        plan.content = payload["content"]

    plan.version = (plan.version or 1) + 1

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "db_error"}), 500

    return jsonify(routineplan_to_dict(plan)), 200


@plans_bp.delete("/routine-plans/<string:plan_id>")
def delete_routine_plan(plan_id: str):
    user = _resolve_user_for_request()
    if not user:
        return jsonify({"error": "No autenticado"}), 401

    try:
        pid = uuid.UUID(plan_id)
    except ValueError:
        return jsonify({"error": "invalid_id"}), 400

    plan = RoutinePlan.query.filter(RoutinePlan.id == pid, RoutinePlan.user_id == user.id).first()
    if not plan:
        return jsonify({"error": "not_found"}), 404

    db.session.delete(plan)
    db.session.commit()
    return ("", 204)
