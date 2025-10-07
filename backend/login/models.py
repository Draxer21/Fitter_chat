from datetime import datetime
from typing import Dict

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
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, raw_password: str) -> None:
        if not raw_password or not raw_password.strip():
            raise ValueError("Password can not be empty")
        self.password_hash = generate_password_hash(raw_password.strip())

    def check_password(self, raw_password: str) -> bool:
        if not raw_password:
            return False
        return check_password_hash(self.password_hash, raw_password)

    def to_dict(self) -> Dict[str, str]:
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "full_name": self.full_name,
            "is_admin": self.is_admin,
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
