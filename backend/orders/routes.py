from __future__ import annotations

from datetime import datetime, timedelta
from io import BytesIO
from typing import Any, Dict

from flask import Blueprint, Response, current_app, jsonify, request, session, send_file
from sqlalchemy import func, select

from ..extensions import db
from ..orders.models import Order, OrderItem

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
except Exception:
    canvas = None  # pragma: no cover

bp = Blueprint("orders", __name__)


def _is_admin() -> bool:
    return bool(session.get("is_admin"))


def _require_admin():
    if not _is_admin():
        return jsonify({"error": "No autorizado"}), 403
    return None


def _order_allowed(order: Order) -> bool:
    if _is_admin():
        return True
    last_id = session.get("last_order_id")
    user_id = session.get("uid")
    if last_id == order.id:
        return True
    if user_id and order.user_id and order.user_id == int(user_id):
        return True
    return False


@bp.get("/orders/<int:order_id>")
def get_order(order_id: int):
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({"error": "Pedido no encontrado"}), 404
    if not _order_allowed(order):
        return jsonify({"error": "No autorizado"}), 403
    return jsonify({"order": order.to_dict()}), 200


@bp.get("/orders/<int:order_id>/receipt.pdf")
def order_receipt_pdf(order_id: int):
    if canvas is None:
        return jsonify({"error": "La generacion de PDF no esta disponible en este entorno."}), 503

    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({"error": "Pedido no encontrado"}), 404
    if not _order_allowed(order):
        return jsonify({"error": "No autorizado"}), 403

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 40 * mm

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(25 * mm, y, "Comprobante de compra")
    y -= 12 * mm

    pdf.setFont("Helvetica", 10)
    pdf.drawString(25 * mm, y, f"Numero de pedido: {order.id}")
    y -= 6 * mm
    pdf.drawString(25 * mm, y, f"Fecha: {order.created_at.strftime('%d/%m/%Y %H:%M') if order.created_at else '-'}")
    y -= 6 * mm
    pdf.drawString(25 * mm, y, f"Cliente: {order.customer_name or 'Invitado'}")
    y -= 10 * mm

    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(25 * mm, y, "Producto")
    pdf.drawString(110 * mm, y, "Cantidad")
    pdf.drawString(135 * mm, y, "PU")
    pdf.drawString(160 * mm, y, "Subtotal")
    y -= 5 * mm
    pdf.line(25 * mm, y, 180 * mm, y)
    y -= 5 * mm

    pdf.setFont("Helvetica", 10)
    for item in order.items:
        if y < 25 * mm:
            pdf.showPage()
            y = height - 30 * mm
            pdf.setFont("Helvetica", 10)
        pdf.drawString(25 * mm, y, item.product_name[:35])
        pdf.drawRightString(130 * mm, y, str(item.quantity))
        pdf.drawRightString(155 * mm, y, f"${float(item.unit_price):,.0f}")
        pdf.drawRightString(180 * mm, y, f"${float(item.subtotal):,.0f}")
        y -= 6 * mm

    y -= 6 * mm
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawRightString(180 * mm, y, f"Total: ${float(order.total_amount):,.0f}")

    pdf.showPage()
    pdf.save()

    buffer.seek(0)
    filename = f"boleta_{order.id}.pdf"
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype="application/pdf")


@bp.get("/admin/orders/summary")
def admin_orders_summary():
    auth = _require_admin()
    if auth:
        return auth

    now = datetime.utcnow()
    last_30 = now - timedelta(days=30)

    total_sales = db.session.scalar(select(func.coalesce(func.sum(Order.total_amount), 0)))
    total_orders = db.session.scalar(select(func.count(Order.id)))
    paid_orders = db.session.scalar(select(func.count(Order.id)).where(Order.status == "paid"))

    sales_last_30 = db.session.scalar(
        select(func.coalesce(func.sum(Order.total_amount), 0)).where(Order.created_at >= last_30)
    )
    orders_last_30 = db.session.scalar(
        select(func.count(Order.id)).where(Order.created_at >= last_30)
    )

    daily_sales = (
        db.session.execute(
            select(
                func.date(Order.created_at).label("day"),
                func.coalesce(func.sum(Order.total_amount), 0).label("total"),
            )
            .where(Order.created_at >= last_30)
            .group_by(func.date(Order.created_at))
            .order_by(func.date(Order.created_at))
        )
        .mappings()
        .all()
    )

    top_products = (
        db.session.execute(
            select(
                OrderItem.product_name,
                func.coalesce(func.sum(OrderItem.quantity), 0).label("quantity"),
                func.coalesce(func.sum(OrderItem.subtotal), 0).label("revenue"),
            )
            .join(Order)
            .where(Order.status == "paid")
            .group_by(OrderItem.product_name)
            .order_by(func.sum(OrderItem.subtotal).desc())
            .limit(5)
        )
        .mappings()
        .all()
    )

    return jsonify(
        {
            "total_sales": float(total_sales or 0),
            "total_orders": int(total_orders or 0),
            "paid_orders": int(paid_orders or 0),
            "sales_last_30": float(sales_last_30 or 0),
            "orders_last_30": int(orders_last_30 or 0),
            "daily_sales": [
                {"date": row["day"].isoformat(), "total": float(row["total"])} for row in daily_sales
            ],
            "top_products": [
                {
                    "name": row["product_name"],
                    "quantity": int(row["quantity"]),
                    "revenue": float(row["revenue"]),
                }
                for row in top_products
            ],
        }
    ), 200


@bp.get("/admin/orders")
def admin_orders_list():
    auth = _require_admin()
    if auth:
        return auth

    status = request.args.get("status")
    start = request.args.get("start")
    end = request.args.get("end")
    limit = min(int(request.args.get("limit", 50)), 200)

    query = Order.query.order_by(Order.created_at.desc())
    if status:
        query = query.filter(Order.status == status)
    if start:
        try:
            start_dt = datetime.fromisoformat(start)
            query = query.filter(Order.created_at >= start_dt)
        except ValueError:
            pass
    if end:
        try:
            end_dt = datetime.fromisoformat(end)
            query = query.filter(Order.created_at <= end_dt)
        except ValueError:
            pass

    orders = query.limit(limit).all()
    return jsonify({"orders": [order.to_dict() for order in orders]}), 200
