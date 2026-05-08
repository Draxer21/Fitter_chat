"""Unit tests for Subscription and MembershipPlan models."""
import pytest
from datetime import datetime, timedelta

from backend.app import create_app
from backend.extensions import db as _db
from backend.subscriptions.models import Subscription, MembershipPlan, seed_membership_plans
from backend.orders.models import Order
from backend.login.models import User
from decimal import Decimal


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
    app = create_app()
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI="sqlite:///:memory:")
    with app.app_context():
        _db.create_all()
    yield app
    with app.app_context():
        _db.drop_all()


@pytest.fixture
def session(app):
    with app.app_context():
        yield _db.session


@pytest.fixture
def user(session):
    u = User(
        email="sub@test.com",
        username="sub_user",
        full_name="Sub User",
    )
    u.set_password("Secret123")
    session.add(u)
    session.flush()
    return u


# ── MembershipPlan ──────────────────────────────────────────────────


def test_seed_membership_plans(session):
    seed_membership_plans()
    plans = MembershipPlan.query.all()
    assert len(plans) == 3
    plan_types = {p.plan_type for p in plans}
    assert plan_types == {"basic", "premium", "black"}


def test_seed_membership_plans_idempotent(session):
    seed_membership_plans()
    seed_membership_plans()
    assert MembershipPlan.query.count() == 3


def test_membership_plan_to_dict(session):
    seed_membership_plans()
    basic = MembershipPlan.query.filter_by(plan_type="basic").one()
    d = basic.to_dict()
    assert d["plan_type"] == "basic"
    assert d["price_clp"] == 29990
    assert d["is_active"] is True
    assert d["sort_order"] == 0


def test_membership_plan_sort_order(session):
    seed_membership_plans()
    plans = MembershipPlan.query.order_by(MembershipPlan.sort_order).all()
    assert [p.plan_type for p in plans] == ["basic", "premium", "black"]


# ── Subscription ────────────────────────────────────────────────────


def test_create_subscription(session, user):
    sub = Subscription(
        user_id=user.id,
        plan_type="premium",
        status="active",
    )
    session.add(sub)
    session.commit()

    assert sub.id is not None
    assert sub.plan_type == "premium"
    assert sub.auto_renew is True
    assert sub.start_date is not None
    assert sub.end_date is None


def test_subscription_to_dict(session, user):
    sub = Subscription(
        user_id=user.id,
        plan_type="black",
        status="active",
        end_date=datetime.utcnow() + timedelta(days=30),
    )
    session.add(sub)
    session.commit()

    d = sub.to_dict()
    expected_keys = {
        "id", "user_id", "order_id", "plan_type", "status",
        "start_date", "end_date", "auto_renew", "cancelled_at",
        "created_at", "updated_at",
    }
    assert set(d.keys()) == expected_keys
    assert d["plan_type"] == "black"
    assert d["order_id"] is None


def test_subscription_order_link(session, user):
    """Subscription.order_id FK links to Order (integrity fix)."""
    order = Order(total_amount=Decimal("49990"), user_id=user.id)
    session.add(order)
    session.flush()

    sub = Subscription(
        user_id=user.id,
        plan_type="premium",
        status="active",
        order_id=order.id,
    )
    session.add(sub)
    session.commit()

    assert sub.order_id == order.id
    assert sub.order.id == order.id
    assert order.subscription.id == sub.id
    assert sub.to_dict()["order_id"] == order.id


def test_subscription_user_relationship(session, user):
    sub = Subscription(user_id=user.id, plan_type="basic", status="active")
    session.add(sub)
    session.commit()

    assert sub.user.id == user.id
    assert user.subscriptions.count() == 1


def test_subscription_cancel(session, user):
    sub = Subscription(user_id=user.id, plan_type="premium", status="active")
    session.add(sub)
    session.commit()

    sub.status = "cancelled"
    sub.cancelled_at = datetime.utcnow()
    session.commit()

    d = sub.to_dict()
    assert d["status"] == "cancelled"
    assert d["cancelled_at"] is not None
