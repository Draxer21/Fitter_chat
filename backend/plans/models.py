"""SQLAlchemy models for diet and routine plans."""
from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from ..extensions import db


JSON_TYPE = postgresql.JSONB().with_variant(sa.JSON, "sqlite")
UUID_TYPE = postgresql.UUID(as_uuid=True).with_variant(sa.String(36), "sqlite")


class DietPlan(db.Model):
    __tablename__ = "diet_plans"

    id = db.Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)

    title = db.Column(db.String(120), nullable=False)
    goal = db.Column(db.String(120), nullable=True, default="")
    content = db.Column(JSON_TYPE, nullable=False)

    version = db.Column(db.Integer, nullable=False, default=1)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.Index("ix_diet_plans_user_created", "user_id", "created_at"),
    )


class RoutinePlan(db.Model):
    __tablename__ = "routine_plans"

    id = db.Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)

    title = db.Column(db.String(120), nullable=False)
    objective = db.Column(db.String(120), nullable=True, default="")
    content = db.Column(JSON_TYPE, nullable=False)

    version = db.Column(db.Integer, nullable=False, default=1)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.Index("ix_routine_plans_user_created", "user_id", "created_at"),
    )
