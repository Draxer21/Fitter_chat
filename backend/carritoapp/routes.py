# backend/carritoapp/routes.py
from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional, Tuple

from flask import Blueprint, current_app, jsonify, render_template, request, session
from sqlalchemy import select

from ..extensions import db
from ..gestor_inventario.models import Producto
from ..orders.models import Order
from .carrito import Carrito

bp = Blueprint("carrito", __name__)


# --------- Utilidades ---------
def _get_carrito() -> Dict[str, Any]:
    return Carrito().snapshot()


def _luhn_checksum(card_num: str) -> bool:
    """Basic Luhn checksum validator."""

    def digits_of(value: str):
        return [int(d) for d in value]

    digits = digits_of(card_num)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = sum(odd_digits)
    for digit in even_digits:
        checksum += sum(digits_of(str(digit * 2)))
    return checksum % 10 == 0


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _to_decimal(value: Any, default: Decimal = Decimal("0.00")) -> Decimal:
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return default


def _order_is_visible(order: Order) -> bool:
    if session.get("is_admin"):
        return True
    if session.get("last_order_id") == order.id:
        return True
    uid = session.get("uid")
    if uid and order.user_id and int(uid) == order.user_id:
        return True
    return False


def _order_to_cart(order: Order) -> Dict[str, Any]:
    items: Dict[str, Dict[str, Any]] = {}
    total = Decimal("0.00")
    for item in order.items:
        subtotal = Decimal(str(item.subtotal))
        unit_price = Decimal(str(item.unit_price))
        total += subtotal
        producto_id = item.product_id or item.id
        key = str(producto_id)
        items[key] = {
            "producto_id": producto_id,
            "nombre": item.product_name,
            "cantidad": item.quantity,
            "precio_unitario": float(unit_price),
            "acumulado": float(subtotal),
        }
    return {"items": items, "total": float(total or order.total_amount or 0)}


def validar_y_deducir(snapshot: Optional[Dict[str, Any]] = None) -> Tuple[bool, Optional[str]]:
    """Valida stock y reserva unidades de manera atomica."""
    carrito = Carrito()
    snapshot = snapshot or carrito.snapshot()
    items_raw: Dict[str, Dict[str, Any]] = snapshot.get("items") or {}
    if not items_raw:
        return False, "Carrito vacio."

    aggregated: Dict[int, int] = {}
    for item in items_raw.values():
        pid = _to_int(item.get("producto_id"))
        qty = max(1, _to_int(item.get("cantidad")))
        if pid <= 0:
            continue
        aggregated[pid] = aggregated.get(pid, 0) + qty

    if not aggregated:
        return False, "No hay productos validos en el carrito."

    try:
        with db.session.begin_nested():
            productos = (
                db.session.execute(
                    select(Producto).where(Producto.id.in_(list(aggregated.keys()))).with_for_update()
                )
                .scalars()
                .all()
            )
            catalogo = {producto.id: producto for producto in productos}

            for pid, qty in aggregated.items():
                producto = catalogo.get(pid)
                if not producto:
                    raise ValueError(f"Producto ID {pid} no encontrado.")
                stock_disponible = producto.stock or 0
                if qty > stock_disponible:
                    raise ValueError(
                        f"Stock insuficiente para {producto.nombre}. Solo quedan {stock_disponible} unidades."
                    )

            for pid, qty in aggregated.items():
                producto = catalogo[pid]
                producto.stock = (producto.stock or 0) - qty
        db.session.commit()
        return True, None
    except ValueError as exc:
        db.session.rollback()
        return False, str(exc)
    except Exception as exc:  # pragma: no cover - guarda log
        db.session.rollback()
        current_app.logger.exception("Error al validar carrito: %s", exc)
        return False, "Error interno al validar carrito."


# --------- Endpoints JSON ---------
@bp.get("/estado")
def estado_carrito():
    return jsonify(_get_carrito()), 200


@bp.post("/agregar/<int:producto_id>")
def agregar_producto(producto_id: int):
    producto = db.session.get(Producto, producto_id)
    if not producto:
        return jsonify({"error": "Producto no encontrado."}), 404
    try:
        estado = Carrito().agregar(producto)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"ok": True, "carrito": estado}), 200


@bp.post("/eliminar/<int:producto_id>")
def eliminar_producto(producto_id: int):
    producto = db.session.get(Producto, producto_id)
    if not producto:
        return jsonify({"error": "Producto no encontrado."}), 404
    estado = Carrito().eliminar(producto)
    return jsonify({"ok": True, "carrito": estado}), 200


@bp.post("/restar/<int:producto_id>")
def restar_producto(producto_id: int):
    producto = db.session.get(Producto, producto_id)
    if not producto:
        return jsonify({"error": "Producto no encontrado."}), 404
    estado = Carrito().restar(producto)
    return jsonify({"ok": True, "carrito": estado}), 200


@bp.post("/limpiar")
def limpiar_carrito():
    estado = Carrito().limpiar()
    return jsonify({"ok": True, "carrito": estado}), 200


@bp.post("/validar")
def validar_carrito():
    exito, mensaje = validar_y_deducir()
    if not exito:
        return jsonify({"error": mensaje or "Error validando carrito."}), 400
    nuevo_estado = Carrito().limpiar()
    return jsonify({"exito": "Compra validada.", "carrito": nuevo_estado}), 200


@bp.post("/pagar")
def procesar_pago():
    data = request.get_json(silent=True) or {}

    carrito = Carrito()
    snapshot = carrito.snapshot()
    if not snapshot.get("items"):
        return jsonify({"error": "Carrito vacio."}), 400

    card_num = (data.get("card_num") or "").replace(" ", "").replace("-", "")
    exp = data.get("exp") or ""
    cvv = data.get("cvv") or ""
    name = (data.get("name") or session.get("full_name") or "").strip()
    email = (data.get("email") or session.get("email") or session.get("user_email") or "").strip()

    if not card_num.isdigit() or not (13 <= len(card_num) <= 19) or not _luhn_checksum(card_num):
        return jsonify({"error": "Numero de tarjeta invalido."}), 400

    try:
        mes, anno = exp.split("/")
        mes = int(mes)
        anno = int("20" + anno) if len(anno) == 2 else int(anno)
        ahora = datetime.now()
        expiracion = datetime(anno, mes, 1)
        if expiracion < datetime(ahora.year, ahora.month, 1):
            return jsonify({"error": "Tarjeta expirada."}), 400
    except Exception:
        return jsonify({"error": "Fecha de expiracion invalida (MM/YY)."}), 400

    if not cvv.isdigit() or len(cvv) not in (3, 4):
        return jsonify({"error": "CVV invalido."}), 400

    if not name:
        return jsonify({"error": "Nombre del titular requerido."}), 400

    exito, mensaje = validar_y_deducir(snapshot)
    if not exito:
        return jsonify({"error": mensaje or "Error procesando compra o stock insuficiente."}), 400

    try:
        user_id = session.get("uid")
        order = Order.from_cart_snapshot(
            snapshot=snapshot,
            status="paid",
            user_id=int(user_id) if user_id else None,
            customer_name=name,
            customer_email=email or None,
            payment_method="card",
            payment_reference=card_num[-4:],
            metadata={"snapshot": snapshot},
        )
        db.session.commit()
    except Exception as exc:  # pragma: no cover - rollback y log
        db.session.rollback()
        current_app.logger.exception("No se pudo registrar el pedido: %s", exc)
        return jsonify({"error": "Pago procesado, pero no se pudo registrar la orden. Contacta soporte."}), 500

    carrito.limpiar()
    session["last_order_id"] = order.id
    return jsonify({"exito": "Pago procesado y compra validada.", "order_id": order.id}), 200


# --------- Vistas ---------
@bp.get("/tienda")
def tienda():
    productos = Producto.query.order_by(Producto.id.desc()).all()
    return render_template("tienda.html", productos=productos)


@bp.get("/boleta")
def generar_boleta():
    order_id = request.args.get("order", type=int)
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    if order_id:
        order = db.session.get(Order, order_id)
        if not order:
            return jsonify({"error": "Pedido no encontrado."}), 404
        if not _order_is_visible(order):
            return jsonify({"error": "No autorizado."}), 403
        carrito_data = _order_to_cart(order)
        if order.created_at:
            fecha = order.created_at.strftime("%d/%m/%Y %H:%M:%S")
    else:
        carrito_data = _get_carrito()
        if not carrito_data.get("items"):
            return jsonify({"error": "Carrito vacio."}), 400
        Carrito().limpiar()

    items = carrito_data.get("items", {})
    total = sum(_to_decimal(item.get("acumulado")) for item in items.values())

    return render_template(
        "boleta.html",
        fecha=fecha,
        carrito=items,
        total_carrito=float(total),
    )


@bp.get("/boleta_json")
def generar_boleta_json():
    order_id = request.args.get("order", type=int)

    if order_id:
        order = db.session.get(Order, order_id)
        if not order:
            return jsonify({"error": "Pedido no encontrado."}), 404
        if not _order_is_visible(order):
            return jsonify({"error": "No autorizado."}), 403
        carrito_data = _order_to_cart(order)
        fecha = order.created_at.isoformat() if order.created_at else datetime.now().isoformat()
        return jsonify(
            {
                "fecha": fecha,
                "carrito": carrito_data,
                "total_carrito": carrito_data.get("total", 0.0),
                "order_id": order.id,
            }
        ), 200

    carrito_data = _get_carrito()
    if not carrito_data.get("items"):
        return jsonify({"error": "Carrito vacio."}), 400

    total = sum(_to_decimal(item.get("acumulado")) for item in carrito_data["items"].values())
    carrito_data["total"] = float(total)

    return jsonify(
        {
            "fecha": datetime.now().isoformat(),
            "carrito": carrito_data,
            "total_carrito": float(total),
        }
    ), 200

