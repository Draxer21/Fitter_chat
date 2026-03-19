from datetime import datetime

from ..extensions import db


class HandoffRequest(db.Model):
    __tablename__ = "handoff_request"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True, index=True)
    sender_id = db.Column(db.String(120), nullable=False)
    reason = db.Column(db.String(64), nullable=False, default="otro")
    status = db.Column(db.String(32), nullable=False, default="pending")
    assigned_admin_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", foreign_keys=[user_id], backref=db.backref("handoff_requests", lazy="dynamic"))
    assigned_admin = db.relationship("User", foreign_keys=[assigned_admin_id])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "sender_id": self.sender_id,
            "reason": self.reason,
            "status": self.status,
            "assigned_admin_id": self.assigned_admin_id,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
