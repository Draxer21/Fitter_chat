from datetime import datetime
from typing import Any, Dict, List, Optional
import secrets

import pyotp
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    weight_kg = db.Column(db.Float, nullable=True)
    height_cm = db.Column(db.Float, nullable=True)
    body_fat_percent = db.Column(db.Float, nullable=True)
    fitness_goal = db.Column(db.String(255), nullable=True)
    dietary_preferences = db.Column(db.String(255), nullable=True)
    health_conditions = db.Column(db.JSON, nullable=True)
    additional_notes = db.Column(db.Text, nullable=True)
    totp_secret = db.Column(db.String(64), nullable=True)
    totp_enabled = db.Column(db.Boolean, nullable=False, default=False)
    totp_enabled_at = db.Column(db.DateTime, nullable=True)
    totp_backup_codes = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    profile = db.relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def set_password(self, raw_password: str) -> None:
        if not raw_password or not raw_password.strip():
            raise ValueError("Password can not be empty")
        self.password_hash = generate_password_hash(raw_password.strip())

    def check_password(self, raw_password: str) -> bool:
        if not raw_password:
            return False
        return check_password_hash(self.password_hash, raw_password)

    def has_totp_enabled(self) -> bool:
        return bool(self.totp_enabled and self.totp_secret)

    def reset_totp_secret(self) -> str:
        secret = pyotp.random_base32()
        self.totp_secret = secret
        self.totp_enabled = False
        self.totp_enabled_at = None
        self.totp_backup_codes = None
        return secret

    def provisioning_uri(self, issuer: str = "Fitter") -> Optional[str]:
        if not self.totp_secret:
            return None
        label = self.email or self.username
        totp = pyotp.TOTP(self.totp_secret)
        return totp.provisioning_uri(name=label, issuer_name=issuer)

    def verify_totp_token(self, code: str, valid_window: int = 1) -> bool:
        if not self.totp_secret or not code:
            return False
        try:
            totp = pyotp.TOTP(self.totp_secret)
            return bool(totp.verify(code.strip(), valid_window=valid_window))
        except Exception:
            return False

    def generate_backup_codes(self, count: int = 6) -> List[str]:
        count = max(1, min(count, 10))
        codes = [secrets.token_hex(4) for _ in range(count)]
        self.totp_backup_codes = [generate_password_hash(code) for code in codes]
        return codes

    def consume_backup_code(self, code: str) -> bool:
        if not code or not self.totp_backup_codes:
            return False
        normalized = code.strip()
        remaining = list(self.totp_backup_codes or [])
        for stored in list(remaining):
            if check_password_hash(stored, normalized):
                remaining.remove(stored)
                self.totp_backup_codes = remaining
                return True
        return False

    def disable_totp(self) -> None:
        self.totp_secret = None
        self.totp_enabled = False
        self.totp_enabled_at = None
        self.totp_backup_codes = None

    def ensure_profile(self):
        if self.profile:
            return self.profile
        from ..profile.models import UserProfile  # import local para evitar ciclos

        self.profile = UserProfile(user_id=self.id)
        db.session.add(self.profile)
        return self.profile

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "full_name": self.full_name,
            "is_admin": self.is_admin,
            "weight_kg": self.weight_kg,
            "height_cm": self.height_cm,
            "body_fat_percent": self.body_fat_percent,
            "fitness_goal": self.fitness_goal,
            "dietary_preferences": self.dietary_preferences,
            "health_conditions": self.health_conditions or [],
            "additional_notes": self.additional_notes,
            "totp_enabled": bool(self.totp_enabled),
            "profile": self.profile.to_dict() if self.profile else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def create(
        cls,
        *,
        email: str,
        username: str,
        password: str,
        full_name: str,
        is_admin: bool = False,
    ) -> "User":
        user = cls(
            email=email.lower().strip(),
            username=username.strip().lower(),
            full_name=full_name.strip(),
            is_admin=is_admin,
        )
        user.set_password(password)
        db.session.add(user)
        return user
