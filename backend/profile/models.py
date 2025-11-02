# backend/profile/models.py
from datetime import datetime
from typing import Dict, Optional

from ..extensions import db


class UserProfile(db.Model):
    __tablename__ = "user_profile"

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    weight_kg = db.Column(db.Float, nullable=True)
    height_cm = db.Column(db.Float, nullable=True)
    age_years = db.Column(db.Integer, nullable=True)
    sex = db.Column(db.String(16), nullable=True)
    activity_level = db.Column(db.String(32), nullable=True)
    primary_goal = db.Column(db.String(64), nullable=True)
    allergies = db.Column(db.Text, nullable=True)
    medical_conditions = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User", back_populates="profile", uselist=False)

    def to_dict(self) -> Dict[str, Optional[str]]:
        return {
            "user_id": self.user_id,
            "weight_kg": self.weight_kg,
            "height_cm": self.height_cm,
            "age_years": self.age_years,
            "sex": self.sex,
            "activity_level": self.activity_level,
            "primary_goal": self.primary_goal,
            "allergies": self.allergies,
            "medical_conditions": self.medical_conditions,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def update_from_payload(self, payload: Dict[str, object]) -> None:
        def _clean_float(key: str) -> Optional[float]:
            value = payload.get(key)
            if value in (None, ""):
                return None
            try:
                parsed = float(value)
            except (TypeError, ValueError):
                raise ValueError(f"{key} invalido")
            if parsed < 0:
                raise ValueError(f"{key} no puede ser negativo")
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
            self.weight_kg = _clean_float("weight_kg")
        if "height_cm" in payload:
            self.height_cm = _clean_float("height_cm")
        if "age_years" in payload:
            age = _clean_int("age_years")
            if age is not None and age > 120:
                raise ValueError("age_years no puede ser mayor a 120")
            self.age_years = age
        if "sex" in payload:
            text = _clean_text("sex", max_len=16)
            self.sex = text.lower() if text else None
        if "activity_level" in payload:
            self.activity_level = _clean_text("activity_level", max_len=32)
        if "primary_goal" in payload:
            self.primary_goal = _clean_text("primary_goal", max_len=64)
        if "allergies" in payload:
            self.allergies = _clean_text("allergies", max_len=500)
        if "medical_conditions" in payload:
            self.medical_conditions = _clean_text("medical_conditions", max_len=500)
        if "notes" in payload:
            self.notes = _clean_text("notes", max_len=1000)

