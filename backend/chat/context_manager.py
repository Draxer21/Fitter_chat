"""Wrapper para encapsular la lógica de negocio del ChatUserContext."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .models import ChatUserContext


@dataclass
class ChatContextManager:
    context: ChatUserContext

    def set_last_routine(self, payload: Dict[str, Any]) -> None:
        self.context.set_last_routine(payload)

    def set_last_diet(self, payload: Dict[str, Any]) -> None:
        self.context.set_last_diet(payload)

    def touch(self) -> None:
        self.context.touch()

    def add_history_entry(self, entry: Dict[str, Any]) -> None:
        self.context.append_history(entry)

    def set_allergies(self, value: Optional[Any]) -> None:
        raw = value
        if raw is None:
            self.context.set_allergies(None)
        elif isinstance(raw, str):
            self.context.set_allergies(raw)
        else:
            self.context.set_allergies(str(raw))

    def set_medical_conditions(self, value: Optional[Any]) -> None:
        raw = value
        if raw is None:
            self.context.set_medical_conditions(None)
        elif isinstance(raw, str):
            self.context.set_medical_conditions(raw)
        else:
            self.context.set_medical_conditions(str(raw))

    def set_dislikes(self, value: Optional[Any]) -> None:
        raw = value
        if raw is None:
            self.context.set_dislikes(None)
        elif isinstance(raw, str):
            self.context.set_dislikes(raw)
        else:
            self.context.set_dislikes(str(raw))

    def set_notes(self, value: Optional[Any]) -> None:
        note = value
        if isinstance(note, str):
            self.context.notes = note.strip() or None
        elif note is None:
            self.context.notes = None
        else:
            self.context.notes = str(note).strip() or None

    def to_metadata(self) -> Dict[str, Any]:
        return self.context.to_metadata()

    def to_dict(self) -> Dict[str, Any]:
        return self.context.to_dict()
