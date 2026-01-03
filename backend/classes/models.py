from __future__ import annotations

from datetime import datetime

from ..extensions import db


class FitnessClass(db.Model):
    __tablename__ = "fitness_class"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    description = db.Column(db.Text)
    instructor = db.Column(db.String(120))
    duration_min = db.Column(db.Integer, nullable=False, default=60)
    capacity = db.Column(db.Integer, nullable=False, default=10)
    location = db.Column(db.String(120))
    active = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    sessions = db.relationship(
        "ClassSession",
        back_populates="fitness_class",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        db.CheckConstraint("duration_min > 0", name="ck_fitness_class_duration_positive"),
        db.CheckConstraint("capacity >= 0", name="ck_fitness_class_capacity_nonneg"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "instructor": self.instructor,
            "duration_min": self.duration_min,
            "capacity": self.capacity,
            "location": self.location,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ClassSession(db.Model):
    __tablename__ = "class_session"

    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey("fitness_class.id"), nullable=False, index=True)
    start_time = db.Column(db.DateTime, nullable=False, index=True)
    duration_override = db.Column(db.Integer)
    capacity_override = db.Column(db.Integer)
    is_exclusive = db.Column(db.Boolean, nullable=False, default=False)
    notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    fitness_class = db.relationship("FitnessClass", back_populates="sessions")

    __table_args__ = (
        db.CheckConstraint("duration_override IS NULL OR duration_override > 0", name="ck_class_session_duration_positive"),
        db.CheckConstraint("capacity_override IS NULL OR capacity_override >= 0", name="ck_class_session_capacity_nonneg"),
    )

    def effective_duration(self) -> int:
        if self.duration_override:
            return self.duration_override
        if self.fitness_class:
            return self.fitness_class.duration_min
        return 0

    def effective_capacity(self) -> int:
        if self.capacity_override is not None:
            return self.capacity_override
        if self.fitness_class:
            return self.fitness_class.capacity
        return 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "class_id": self.class_id,
            "class_name": self.fitness_class.name if self.fitness_class else None,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "duration_override": self.duration_override,
            "capacity_override": self.capacity_override,
            "effective_duration": self.effective_duration(),
            "effective_capacity": self.effective_capacity(),
            "is_exclusive": self.is_exclusive,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
