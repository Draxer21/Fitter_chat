"""Persistence helpers for chat user context."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, Optional

from ..extensions import db


def _now() -> datetime:
    return datetime.utcnow()


class ChatUserContext(db.Model):
    __tablename__ = "chat_user_context"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.String(80), nullable=False, unique=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    allergies = db.Column(db.Text, nullable=True)
    medical_conditions = db.Column(db.Text, nullable=True)
    last_routine = db.Column(db.JSON, nullable=True)
    last_diet = db.Column(db.JSON, nullable=True)
    history = db.Column(db.JSON, nullable=False, default=list)
    notes = db.Column(db.Text, nullable=True)
    last_interaction_at = db.Column(db.DateTime, nullable=False, default=_now)
    created_at = db.Column(db.DateTime, nullable=False, default=_now)
    updated_at = db.Column(db.DateTime, nullable=False, default=_now, onupdate=_now)

    @classmethod
    def get_or_create(cls, sender_id: str, user_id: Optional[int] = None) -> "ChatUserContext":
        sender_id = (sender_id or "").strip()[:80]
        ctx: Optional["ChatUserContext"] = cls.query.filter_by(sender_id=sender_id).one_or_none()
        if ctx:
            if user_id and not ctx.user_id:
                ctx.user_id = user_id
            ctx.touch()
            return ctx

        ctx = cls(sender_id=sender_id, user_id=user_id or None)
        db.session.add(ctx)
        return ctx

    def touch(self) -> None:
        self.last_interaction_at = _now()

    def set_allergies(self, value: Optional[str]) -> None:
        self.allergies = value.strip() if value else None
        self.touch()

    def set_medical_conditions(self, value: Optional[str]) -> None:
        self.medical_conditions = value.strip() if value else None
        self.touch()

    def set_last_routine(self, routine_payload: Dict[str, Any]) -> None:
        self.last_routine = routine_payload or None
        self.append_history(
            {
                "type": "routine",
                "data": routine_payload,
                "timestamp": _now().isoformat(),
            }
        )

    def set_last_diet(self, diet_payload: Dict[str, Any]) -> None:
        self.last_diet = diet_payload or None
        self.append_history(
            {
                "type": "diet",
                "data": diet_payload,
                "timestamp": _now().isoformat(),
            }
        )

    def append_history(self, entry: Dict[str, Any], *, max_items: int = 20) -> None:
        history: Iterable[Dict[str, Any]] = self.history or []
        items = list(history)
        if "timestamp" not in entry:
            entry["timestamp"] = _now().isoformat()
        items.append(entry)
        if len(items) > max_items:
            items = items[-max_items:]
        self.history = items
        self.touch()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sender_id": self.sender_id,
            "user_id": self.user_id,
            "allergies": self.allergies,
            "medical_conditions": self.medical_conditions,
            "last_routine": self.last_routine,
            "last_diet": self.last_diet,
            "history": self.history or [],
            "notes": self.notes,
            "last_interaction_at": (self.last_interaction_at.isoformat() if self.last_interaction_at else None),
            "updated_at": (self.updated_at.isoformat() if self.updated_at else None),
        }

    def to_metadata(self) -> Dict[str, Any]:
        # Keep metadata compact to avoid inflating Rasa payloads.
        meta_history = []
        last_explanation = None
        for item in reversed(self.history or []):
            if last_explanation:
                break
            if isinstance(item, dict) and "explanation" in item:
                exp = item.get("explanation")
                if isinstance(exp, str) and exp.strip():
                    last_explanation = exp.strip()[:300]
        for item in (self.history or [])[-5:]:
            meta_history.append(
                {
                    "type": item.get("type"),
                    "timestamp": item.get("timestamp"),
                }
            )
        return {
            "allergies": self.allergies,
            "medical_conditions": self.medical_conditions,
            "last_routine": self.last_routine,
            "last_diet": self.last_diet,
            "recent_history": meta_history,
            "last_explanation": last_explanation,
        }
