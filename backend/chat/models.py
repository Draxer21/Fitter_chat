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
    chat_id = db.Column(db.String(80), nullable=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    allergies = db.Column(db.Text, nullable=True)
    dislikes = db.Column(db.Text, nullable=True)
    medical_conditions = db.Column(db.Text, nullable=True)
    last_routine = db.Column(db.JSON, nullable=True)
    last_diet = db.Column(db.JSON, nullable=True)
    history = db.Column(db.JSON, nullable=False, default=list)
    notes = db.Column(db.Text, nullable=True)
    consent_given = db.Column(db.Boolean, nullable=False, default=False)
    consent_version = db.Column(db.String(32), nullable=True)
    consent_timestamp = db.Column(db.DateTime, nullable=True)
    consent_revoked_at = db.Column(db.DateTime, nullable=True)
    last_interaction_result = db.Column(db.String(32), nullable=True)
    last_interaction_at = db.Column(db.DateTime, nullable=False, default=_now)
    created_at = db.Column(db.DateTime, nullable=False, default=_now)
    updated_at = db.Column(db.DateTime, nullable=False, default=_now, onupdate=_now)

    @classmethod
    def get_or_create(cls, sender_id: str, user_id: Optional[int] = None) -> "ChatUserContext":
        sender_id = (sender_id or "").strip()[:80]
        # If sender_id contains a chat separator '::', allow using it as chat_id
        chat_id = None
        if "::" in sender_id:
            parts = sender_id.split("::", 1)
            sender_id = parts[0][:80]
            chat_id = parts[1][:80]

        if chat_id:
            ctx: Optional["ChatUserContext"] = cls.query.filter_by(sender_id=sender_id, chat_id=chat_id).one_or_none()
        else:
            ctx: Optional["ChatUserContext"] = cls.query.filter_by(sender_id=sender_id).one_or_none()
        if ctx:
            if user_id and not ctx.user_id:
                ctx.user_id = user_id
            ctx.touch()
            return ctx

        ctx = cls(sender_id=sender_id, chat_id=chat_id, user_id=user_id or None)
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

    def set_dislikes(self, value: Optional[str]) -> None:
        self.dislikes = value.strip() if value else None
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

    def set_consent(self, *, given: bool, version: Optional[str] = None) -> None:
        prev_given = bool(self.consent_given)
        self.consent_given = bool(given)
        self.consent_version = version.strip()[:32] if isinstance(version, str) and version.strip() else None
        if self.consent_given and not prev_given:
            self.consent_timestamp = _now()
        self.consent_revoked_at = None if self.consent_given else self.consent_revoked_at
        self.touch()

    def revoke_consent(self) -> None:
        self.consent_given = False
        self.consent_revoked_at = _now()
        self.touch()

    def reset_sensitive_context(self) -> None:
        self.allergies = None
        self.dislikes = None
        self.medical_conditions = None
        self.last_routine = None
        self.last_diet = None
        self.notes = None
        self.history = []
        self.touch()

    def set_last_interaction_result(self, result: Optional[str]) -> None:
        self.last_interaction_result = result.strip()[:32] if isinstance(result, str) and result.strip() else None
        self.touch()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sender_id": self.sender_id,
            "user_id": self.user_id,
            "allergies": self.allergies,
            "dislikes": self.dislikes,
            "medical_conditions": self.medical_conditions,
            "last_routine": self.last_routine,
            "last_diet": self.last_diet,
            "history": self.history or [],
            "notes": self.notes,
            "consent_given": self.consent_given,
            "consent_version": self.consent_version,
            "consent_timestamp": (self.consent_timestamp.isoformat() if self.consent_timestamp else None),
            "consent_revoked_at": (self.consent_revoked_at.isoformat() if self.consent_revoked_at else None),
            "last_interaction_result": self.last_interaction_result,
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
            "dislikes": self.dislikes,
            "medical_conditions": self.medical_conditions,
            "last_routine": self.last_routine,
            "last_diet": self.last_diet,
            "consent_given": self.consent_given,
            "consent_version": self.consent_version,
            "recent_history": meta_history,
            "last_explanation": last_explanation,
        }


class ProgressLog(db.Model):
    """Registro persistente de métricas de progreso del usuario (peso, reps, notas)."""

    __tablename__ = "progress_log"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.String(80), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True, index=True)
    metric = db.Column(db.String(80), nullable=True)   # e.g. "peso", "sentadilla", "presion"
    value = db.Column(db.String(120), nullable=True)   # valor registrado (texto libre)
    note = db.Column(db.Text, nullable=True)           # nota adicional del usuario
    recorded_at = db.Column(db.DateTime, nullable=False, default=_now)
    created_at = db.Column(db.DateTime, nullable=False, default=_now)

    @classmethod
    def record(
        cls,
        sender_id: str,
        metric: Optional[str],
        value: Optional[str],
        note: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> "ProgressLog":
        entry = cls(
            sender_id=(sender_id or "")[:80],
            user_id=user_id,
            metric=(metric or "")[:80] if metric else None,
            value=str(value)[:120] if value is not None else None,
            note=note,
        )
        db.session.add(entry)
        return entry

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "metric": self.metric,
            "value": self.value,
            "note": self.note,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
        }
