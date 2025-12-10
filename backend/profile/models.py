# backend/profile/models.py
from datetime import datetime
from typing import Any, Dict, Optional

from ..extensions import db
from ..security.profile_crypto import (
    ProfileCipherError,
    decrypt_profile_payload,
    encrypt_profile_payload,
    profile_payload_checksum,
)


class UserProfile(db.Model):
    __tablename__ = "user_profile"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, unique=True)
    encrypted_payload = db.Column(db.LargeBinary, nullable=True)
    payload_checksum = db.Column(db.String(64), nullable=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User", back_populates="profile", uselist=False)

    _PAYLOAD_KEYS = (
        "weight_kg",
        "height_cm",
        "age_years",
        "sex",
        "activity_level",
        "primary_goal",
        "musculo_preferido",
        "allergies",
        "medical_conditions",
        "notes",
        "body_fat_percent",
        "fitness_goal",
        "dietary_preferences",
        "additional_notes",
    )

    def _empty_payload(self) -> Dict[str, Any]:
        return {key: None for key in self._PAYLOAD_KEYS}

    def _load_payload(self) -> Dict[str, Any]:
        """Descifra el payload. Si no existe, usa los campos legados como fallback."""
        if self.encrypted_payload:
            try:
                return decrypt_profile_payload(self.encrypted_payload)
            except ProfileCipherError:
                # Preferimos propagar el error: la API responderá 500 y evitamos servir datos corruptos.
                raise
        # Fallback para registros sin payload cifrado (se rellenan vacíos).
        return self._empty_payload()

    def _persist_payload(self, payload: Dict[str, Any]) -> None:
        snapshot = self._empty_payload()
        snapshot.update({k: payload.get(k) for k in self._PAYLOAD_KEYS})
        blob = encrypt_profile_payload(snapshot)
        self.encrypted_payload = blob
        self.payload_checksum = profile_payload_checksum(blob)

    def to_dict(self) -> Dict[str, Optional[str]]:
        data = self._load_payload()
        data["user_id"] = self.user_id
        data["created_at"] = self.created_at.isoformat() if self.created_at else None
        data["updated_at"] = self.updated_at.isoformat() if self.updated_at else None
        return data

    def update_from_payload(self, payload: Dict[str, object]) -> None:
        data = self._load_payload()

        def _clean_float(key: str, *, maximum: Optional[float] = None) -> Optional[float]:
            value = payload.get(key)
            if value in (None, ""):
                return None
            try:
                parsed = float(value)
            except (TypeError, ValueError):
                raise ValueError(f"{key} invalido")
            if parsed < 0:
                raise ValueError(f"{key} no puede ser negativo")
            if maximum is not None and parsed > maximum:
                raise ValueError(f"{key} no puede ser mayor a {maximum}")
            return parsed

        def _clean_int(key: str) -> Optional[int]:
            value = payload.get(key)
            if value in (None, ""):
                return None
            try:
                parsed = int(value)
            except (TypeError, ValueError):
                raise ValueError(f"{key} invalido")
            if parsed < 0:
                raise ValueError(f"{key} no puede ser negativo")
            return parsed

        def _clean_text(key: str, max_len: int = 255) -> Optional[str]:
            value = payload.get(key)
            if value in (None, ""):
                return None
            text = str(value).strip()
            if len(text) > max_len:
                raise ValueError(f"{key} excede {max_len} caracteres")
            return text

        if "weight_kg" in payload:
            data["weight_kg"] = _clean_float("weight_kg")
        if "height_cm" in payload:
            data["height_cm"] = _clean_float("height_cm")
        if "age_years" in payload:
            age = _clean_int("age_years")
            if age is not None and age > 120:
                raise ValueError("age_years no puede ser mayor a 120")
            data["age_years"] = age
        if "sex" in payload:
            text = _clean_text("sex", max_len=16)
            data["sex"] = text.lower() if text else None
        if "activity_level" in payload:
            data["activity_level"] = _clean_text("activity_level", max_len=32)
        if "primary_goal" in payload:
            data["primary_goal"] = _clean_text("primary_goal", max_len=64)
        if "musculo_preferido" in payload:
            text = _clean_text("musculo_preferido", max_len=32)
            data["musculo_preferido"] = text.lower() if text else None
        if "allergies" in payload:
            data["allergies"] = _clean_text("allergies", max_len=500)
        if "medical_conditions" in payload:
            data["medical_conditions"] = _clean_text("medical_conditions", max_len=500)
        if "notes" in payload:
            data["notes"] = _clean_text("notes", max_len=1000)
        if "body_fat_percent" in payload:
            data["body_fat_percent"] = _clean_float("body_fat_percent", maximum=100.0)
        if "fitness_goal" in payload:
            data["fitness_goal"] = _clean_text("fitness_goal", max_len=255)
        if "dietary_preferences" in payload:
            data["dietary_preferences"] = _clean_text("dietary_preferences", max_len=255)
        if "additional_notes" in payload:
            data["additional_notes"] = _clean_text("additional_notes", max_len=2000)

        self._persist_payload(data)

