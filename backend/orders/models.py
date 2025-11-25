from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy.dialects.postgresql import JSONB

from ..extensions import db


class Order(db.Model):
    __tablename__ = "order"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True, index=True)
    customer_name = db.Column(db.String(255), nullable=True)
    customer_email = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(32), nullable=False, default="paid", index=True)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.String(8), nullable=False, default="CLP")
    payment_method = db.Column(db.String(64), nullable=True)
    payment_reference = db.Column(db.String(255), nullable=True)
    order_metadata = db.Column("metadata", JSONB().with_variant(db.JSON, "sqlite"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = db.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan", lazy="joined")
    payment = db.relationship("Payment", back_populates="order", uselist=False, cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "customer_name": self.customer_name,
            "customer_email": self.customer_email,
            "status": self.status,
            "total_amount": float(self.total_amount),
            "currency": self.currency,
            "payment_method": self.payment_method,
            "payment_reference": self.payment_reference,
            "metadata": self.order_metadata or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "items": [item.to_dict() for item in self.items],
        }

    @classmethod
    def from_cart_snapshot(
        cls,
        *,
        snapshot: Dict[str, Any],
        status: str = "paid",
        user_id: Optional[int] = None,
        customer_name: Optional[str] = None,
        customer_email: Optional[str] = None,
        payment_method: Optional[str] = None,
        payment_reference: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "Order":
        snapshot = snapshot or {}
        items_data: Iterable[Dict[str, Any]] = snapshot.get("items", {}).values()
        total_amount = Decimal(str(snapshot.get("total", 0.0)))
        metadata_payload = dict(metadata or {})
        metadata_payload.setdefault("snapshot", snapshot)
        order = cls(
            user_id=user_id,
            customer_name=customer_name,
            customer_email=customer_email,
            status=status,
            total_amount=total_amount,
            payment_method=payment_method,
            payment_reference=payment_reference,
            order_metadata=metadata_payload,
        )
        db.session.add(order)
        db.session.flush()

        for item in items_data:
            producto_id = item.get("producto_id")
            nombre = item.get("nombre") or f"Producto {producto_id}"
            cantidad = int(item.get("cantidad") or 1)
            precio = Decimal(str(item.get("precio_unitario") or 0.0))
            subtotal = Decimal(str(item.get("acumulado") or (precio * cantidad)))
            db.session.add(
                OrderItem(
                    order_id=order.id,
                    product_id=producto_id,
                    product_name=nombre,
                    quantity=cantidad,
                    unit_price=precio,
                    subtotal=subtotal,
                    snapshot=item,
                )
            )
        return order


class OrderItem(db.Model):
    __tablename__ = "order_item"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = db.Column(db.Integer, nullable=True)
    product_name = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False)
    snapshot = db.Column(JSONB().with_variant(db.JSON, "sqlite"), nullable=True)

    order = db.relationship("Order", back_populates="items")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "quantity": self.quantity,
            "unit_price": float(self.unit_price),
            "subtotal": float(self.subtotal),
            "snapshot": self.snapshot or {},
        }
