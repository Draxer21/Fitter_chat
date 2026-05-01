from datetime import datetime

from ..extensions import db


# ---------------------------------------------------------------------------
# MembershipPlan — catálogo de planes de membresía (fuente de verdad en BD)
# ---------------------------------------------------------------------------

class MembershipPlan(db.Model):
    __tablename__ = "membership_plan"

    id = db.Column(db.Integer, primary_key=True)
    plan_type = db.Column(db.String(32), unique=True, nullable=False)   # basic | premium | black
    name = db.Column(db.String(64), nullable=False)
    price_clp = db.Column(db.Integer, nullable=False)                   # precio en pesos chilenos
    price_display = db.Column(db.String(32), nullable=False)            # "$29.990/mes"
    features = db.Column(db.Text, nullable=False, default="")           # descripción libre
    sort_order = db.Column(db.Integer, nullable=False, default=0)       # 0=basic, 1=premium, 2=black
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "plan_type": self.plan_type,
            "name": self.name,
            "price_clp": self.price_clp,
            "price_display": self.price_display,
            "features": self.features,
            "sort_order": self.sort_order,
            "is_active": self.is_active,
        }


# Planes por defecto — usados por seed_membership_plans()
_DEFAULT_PLANS = [
    {
        "plan_type": "basic",
        "name": "Básico",
        "price_clp": 29990,
        "price_display": "$29.990/mes",
        "features": "Acceso ilimitado, clases grupales, sauna y duchas",
        "sort_order": 0,
    },
    {
        "plan_type": "premium",
        "name": "Premium",
        "price_clp": 49990,
        "price_display": "$49.990/mes",
        "features": "Todo lo del Básico + coaching personalizado, zona VIP, bebidas ilimitadas",
        "sort_order": 1,
    },
    {
        "plan_type": "black",
        "name": "Black",
        "price_clp": 79990,
        "price_display": "$79.990/mes",
        "features": "Todo lo del Premium + acceso 24/7, masajista, nutricionista, invitados ilimitados",
        "sort_order": 2,
    },
]


def seed_membership_plans() -> None:
    """Inserta los planes por defecto si no existen. Idempotente."""
    for data in _DEFAULT_PLANS:
        existing = MembershipPlan.query.filter_by(plan_type=data["plan_type"]).first()
        if not existing:
            db.session.add(MembershipPlan(**data))
    db.session.commit()


class Subscription(db.Model):
    __tablename__ = "subscription"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    plan_type = db.Column(db.String(32), nullable=False)  # basic, premium, black
    status = db.Column(db.String(32), nullable=False, default="active")
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=True)
    auto_renew = db.Column(db.Boolean, nullable=False, default=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("subscriptions", lazy="dynamic"))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "plan_type": self.plan_type,
            "status": self.status,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "auto_renew": self.auto_renew,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
