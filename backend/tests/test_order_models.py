"""Unit tests for Order and OrderItem models."""
import pytest
from decimal import Decimal

from backend.app import create_app
from backend.extensions import db as _db
from backend.orders.models import Order, OrderItem
from backend.gestor_inventario.models import Producto


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


# ── Order basic CRUD ────────────────────────────────────────────────


def test_create_order_minimal(session):
    order = Order(total_amount=Decimal("15000.00"), currency="CLP", status="paid")
    session.add(order)
    session.commit()

    assert order.id is not None
    assert order.status == "paid"
    assert order.currency == "CLP"


def test_order_to_dict_keys(session):
    order = Order(
        total_amount=Decimal("5000"),
        customer_name="Diego",
        customer_email="diego@test.com",
    )
    session.add(order)
    session.commit()

    d = order.to_dict()
    expected_keys = {
        "id", "user_id", "customer_name", "customer_email", "status",
        "total_amount", "currency", "payment_method", "payment_reference",
        "metadata", "created_at", "updated_at", "items",
    }
    assert set(d.keys()) == expected_keys
    assert d["customer_name"] == "Diego"
    assert d["total_amount"] == 5000.0
    assert d["items"] == []


def test_order_timestamps_auto_set(session):
    order = Order(total_amount=Decimal("1000"))
    session.add(order)
    session.commit()

    assert order.created_at is not None
    assert order.updated_at is not None


# ── OrderItem ───────────────────────────────────────────────────────


def test_order_item_belongs_to_order(session):
    order = Order(total_amount=Decimal("30000"))
    session.add(order)
    session.flush()

    item = OrderItem(
        order_id=order.id,
        product_name="Proteína Whey",
        quantity=2,
        unit_price=Decimal("15000"),
        subtotal=Decimal("30000"),
    )
    session.add(item)
    session.commit()

    assert len(order.items) == 1
    assert order.items[0].product_name == "Proteína Whey"
    assert item.order_id == order.id


def test_order_item_fk_to_producto(session):
    """product_id should reference producto.id (FK integrity fix)."""
    producto = Producto(nombre="Creatina", precio=Decimal("12000"), stock=10)
    session.add(producto)
    session.flush()

    order = Order(total_amount=Decimal("12000"))
    session.add(order)
    session.flush()

    item = OrderItem(
        order_id=order.id,
        product_id=producto.id,
        product_name="Creatina",
        quantity=1,
        unit_price=Decimal("12000"),
        subtotal=Decimal("12000"),
    )
    session.add(item)
    session.commit()

    assert item.product_id == producto.id


def test_order_item_to_dict(session):
    order = Order(total_amount=Decimal("5000"))
    session.add(order)
    session.flush()

    item = OrderItem(
        order_id=order.id,
        product_name="Banda elástica",
        quantity=3,
        unit_price=Decimal("1500"),
        subtotal=Decimal("4500"),
        snapshot={"color": "rojo"},
    )
    session.add(item)
    session.commit()

    d = item.to_dict()
    assert d["product_name"] == "Banda elástica"
    assert d["quantity"] == 3
    assert d["unit_price"] == 1500.0
    assert d["subtotal"] == 4500.0
    assert d["snapshot"]["color"] == "rojo"


def test_cascade_delete_items(session):
    order = Order(total_amount=Decimal("10000"))
    session.add(order)
    session.flush()

    for i in range(3):
        session.add(
            OrderItem(
                order_id=order.id,
                product_name=f"Item {i}",
                quantity=1,
                unit_price=Decimal("3333"),
                subtotal=Decimal("3333"),
            )
        )
    session.commit()

    assert session.query(OrderItem).count() == 3
    session.delete(order)
    session.commit()
    assert session.query(OrderItem).count() == 0


# ── from_cart_snapshot factory ──────────────────────────────────────


def test_from_cart_snapshot(session):
    snapshot = {
        "items": {
            "1": {
                "producto_id": None,
                "nombre": "Guantes",
                "cantidad": 2,
                "precio_unitario": 8000,
                "acumulado": 16000,
            }
        },
        "total": 16000.0,
    }
    order = Order.from_cart_snapshot(
        snapshot=snapshot,
        customer_name="Test User",
        payment_method="mercadopago",
    )
    session.commit()

    assert order.id is not None
    assert float(order.total_amount) == 16000.0
    assert len(order.items) == 1
    assert order.items[0].product_name == "Guantes"
    assert order.items[0].quantity == 2


def test_from_cart_snapshot_empty(session):
    order = Order.from_cart_snapshot(snapshot={}, customer_name="Empty")
    session.commit()

    assert order.id is not None
    assert float(order.total_amount) == 0.0
    assert len(order.items) == 0
