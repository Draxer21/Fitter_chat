"""Validation and serialization helpers for plan CRUD."""
from __future__ import annotations

from typing import Any, Dict, Iterable, Tuple


def require_fields(payload: Dict[str, Any], fields: Iterable[str]) -> Tuple[bool, Dict[str, Any] | None]:
    missing = [f for f in fields if f not in payload]
    if missing:
        return False, {"error": "missing_fields", "fields": missing}
    return True, None


def is_json_object(value: Any) -> bool:
    return isinstance(value, dict)


def dietplan_to_dict(plan) -> Dict[str, Any]:
    return {
        "id": str(plan.id),
        "user_id": plan.user_id,
        "title": plan.title,
        "goal": plan.goal or "",
        "content": plan.content,
        "version": plan.version,
        "created_at": plan.created_at.isoformat() + "Z" if plan.created_at else None,
        "updated_at": plan.updated_at.isoformat() + "Z" if plan.updated_at else None,
    }


def routineplan_to_dict(plan) -> Dict[str, Any]:
    return {
        "id": str(plan.id),
        "user_id": plan.user_id,
        "title": plan.title,
        "objective": plan.objective or "",
        "content": plan.content,
        "version": plan.version,
        "created_at": plan.created_at.isoformat() + "Z" if plan.created_at else None,
        "updated_at": plan.updated_at.isoformat() + "Z" if plan.updated_at else None,
    }
