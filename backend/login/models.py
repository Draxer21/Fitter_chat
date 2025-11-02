from datetime import datetime
from typing import Any, Dict, List, Optional
import secrets

import pyotp
from flask import current_app
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db
from ..security.profile_crypto import (
    ProfileCipherError,
    decrypt_profile_payload,
    encrypt_profile_payload,
    profile_payload_checksum,
)


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    totp_secret = db.Column(db.String(64), nullable=True)
    totp_enabled = db.Column(db.Boolean, nullable=False, default=False)
    totp_enabled_at = db.Column(db.DateTime, nullable=True)
    totp_backup_codes = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    profile_record = db.relationship(
        "UserProfile",
        uselist=False,
        back_populates="user",
        cascade="all, delete-orphan",
    )

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

    def get_profile_defaults(self) -> Dict[str, Any]:
        return {
            "weight_kg": None,
            "height_cm": None,
            "body_fat_percent": None,
            "fitness_goal": None,
            "dietary_preferences": None,
            "health_conditions": [],
            "additional_notes": None,
            "last_updated_at": None,
        }

    def get_profile_data(self) -> Dict[str, Any]:
        defaults = self.get_profile_defaults()
        if not self.profile_record:
            return defaults
        try:
            payload = self.profile_record.get_payload()
        except ProfileCipherError:
            current_app.logger.exception("No se pudo desencriptar el perfil del usuario %s", self.id)
            return defaults
        merged = {**defaults, **payload}
        if not isinstance(merged.get("health_conditions"), list):
            merged["health_conditions"] = []
        return merged

    def ensure_profile_record(self) -> "UserProfile":
        if not self.profile_record:
            self.profile_record = UserProfile(user=self)
        return self.profile_record

    def to_dict(self, *, include_profile: bool = True) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "full_name": self.full_name,
            "is_admin": self.is_admin,
            "totp_enabled": bool(self.totp_enabled),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if include_profile:
            profile = self.get_profile_data()
            data.update(profile)
        return data

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


class UserProfile(db.Model):
    __tablename__ = "user_profile"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, unique=True)
    encrypted_payload = db.Column(db.LargeBinary, nullable=False)
    payload_checksum = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", back_populates="profile_record")

    def set_payload(self, data: Dict[str, Any]) -> None:
        encrypted = encrypt_profile_payload(data)
        self.encrypted_payload = encrypted
        self.payload_checksum = profile_payload_checksum(encrypted)

    def get_payload(self) -> Dict[str, Any]:
        if not self.encrypted_payload:
            return {}
        payload = decrypt_profile_payload(self.encrypted_payload)
        if not isinstance(payload, dict):
            raise ProfileCipherError("El perfil desencriptado no es un objeto valido")
        return payload

    def verify_integrity(self) -> bool:
        if not self.encrypted_payload:
            return False
        expected = profile_payload_checksum(self.encrypted_payload)
        return secrets.compare_digest(expected, self.payload_checksum)
