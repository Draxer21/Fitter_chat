"""Unit tests for Payment model."""
import pytest
from decimal import Decimal
from datetime import datetime

from backend.app import create_app
from backend.extensions import db as _db
from backend.orders.models import Order
from backend.payments.models import Payment


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
def order(session):
    o = Order(total_amount=Decimal("49990"), customer_email="pay@test.com")
    session.add(o)
    session.flush()
    return o


# ── Payment CRUD ────────────────────────────────────────────────────


def test_create_payment(session, order):
    payment = Payment(
        order_id=order.id,
        preference_id="pref_abc123",
        status="pending",
        transaction_amount=49990.0,
        currency_id="CLP",
    )
    session.add(payment)
    session.commit()

    assert payment.id is not None
    assert payment.status == "pending"
    assert payment.transaction_amount == 49990.0


def test_payment_to_dict(session, order):
    payment = Payment(
        order_id=order.id,
        preference_id="pref_dict_test",
        status="approved",
        transaction_amount=29990.0,
        payment_method_id="debit_card",
        payment_type_id="debit_card",
        payer_email="payer@test.com",
    )
    session.add(payment)
    session.commit()

    d = payment.to_dict()
    assert d["order_id"] == order.id
    assert d["status"] == "approved"
    assert d["transaction_amount"] == 29990.0
    assert d["payment_method_id"] == "debit_card"
    assert d["created_at"] is not None


def test_payment_order_relationship(session, order):
    payment = Payment(
        order_id=order.id,
        preference_id="pref_rel_test",
        status="approved",
        transaction_amount=49990.0,
    )
    session.add(payment)
    session.commit()

    assert order.payment is not None
    assert order.payment.id == payment.id
    assert payment.order.id == order.id


def test_payment_approved_at(session, order):
    now = datetime.utcnow()
    payment = Payment(
        order_id=order.id,
        preference_id="pref_approved",
        status="approved",
        transaction_amount=10000.0,
        approved_at=now,
    )
    session.add(payment)
    session.commit()

    d = payment.to_dict()
    assert d["approved_at"] is not None


def test_payment_cascade_with_order(session, order):
    payment = Payment(
        order_id=order.id,
        preference_id="pref_cascade",
        status="pending",
        transaction_amount=5000.0,
    )
    session.add(payment)
    session.commit()

    assert session.query(Payment).count() == 1
    session.delete(order)
    session.commit()
    assert session.query(Payment).count() == 0


def test_payment_repr(session, order):
    payment = Payment(
        order_id=order.id,
        preference_id="pref_repr",
        status="pending",
        transaction_amount=1000.0,
    )
    session.add(payment)
    session.commit()

    r = repr(payment)
    assert "Payment" in r
    assert str(order.id) in r
    assert "pending" in r
