# backend/carritoapp/routes.py
# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict

from flask import Blueprint, current_app, jsonify, render_template, request
from sqlalchemy import select

from ..extensions import db
from ..gestor_inventario.models import Producto
from .carrito import Carrito

bp = Blueprint("carrito", __name__)

# --------- Utilidades ---------
def _get_carrito() -> Dict[str, Any]:
    return Carrito().snapshot()


def _luhn_checksum(card_num: str) -> bool:
    """Validate card number using Luhn algorithm."""
    def digits_of(n):
        return [int(d) for d in str(n)]
    digits = digits_of(card_num)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d*2))
    return checksum % 10 == 0


def validar_y_deducir() -> tuple[bool, str | None]:
    """Valida stock y deduce atómicamente sin limpiar carrito.

    Retorna una tupla (éxito, mensaje_de_error)."""
    carrito_obj = Carrito()
    snapshot = carrito_obj.snapshot()
    items_data = snapshot.get("items", {})
    if not items_data:
        return False, "Carrito vacío."

    # Normaliza lista de (producto_id, cantidad)
    items: Dict[int, int] = {}
    for item in items_data.values():
        pid = _to_int(item.get("producto_id"), default=0)
        cant = max(1, _to_int(item.get("cantidad"), default=0))
        if pid > 0:
            items[pid] = items.get(pid, 0) + cant

    if not items:
        return False, "No hay productos válidos en el carrito."

    try:
        with db.session.begin():
            # Cargar y bloquear productos
            productos = (
                db.session.execute(
                    select(Producto).where(Producto.id.in_(list(items.keys()))).with_for_update()
                )
                .scalars()
                .all()
            )
            by_id = {p.id: p for p in productos}

            # Validar stocks
            for pid, cant in items.items():
                prod = by_id.get(pid)
                if not prod:
                    return False, f"Producto ID {pid} no encontrado."
                stock_disponible = prod.stock or 0
                if cant > stock_disponible:
                    return False, f"Stock insuficiente para {prod.nombre}. Solo quedan {stock_disponible} unidades."

            # Descontar
            for pid, cant in items.items():
                prod = by_id[pid]
                prod.stock = (prod.stock or 0) - cant

        return True, None
    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception("Error al validar y deducir stock: %s", exc)
        return False, "Error interno al validar carrito."


# Endpoint esperado por el frontend: devuelve el estado actual del carrito en sesión
@bp.get("/estado")
def estado_carrito():
    return jsonify(_get_carrito()), 200


def _to_int(v, default=0) -> int:
    try:
        return int(v)
    except Exception:
        return default


def _to_decimal(v, default=Decimal("0.00")) -> Decimal:
    if isinstance(v, Decimal):
        return v
    try:
        return Decimal(str(v))
    except (InvalidOperation, TypeError, ValueError):
        return default


# --------- Vistas ---------
@bp.get("/tienda")  # SSR opcional; si usas React, consume JSON desde /producto/
def tienda():
    productos = Producto.query.order_by(Producto.id.desc()).all()
    return render_template("tienda.html", productos=productos)


@bp.post("/agregar/<int:producto_id>")
def agregar_producto(producto_id: int):
    p = db.session.get(Producto, producto_id)
    if not p:
        return jsonify({"error": "Producto no encontrado"}), 404
    try:
        state = Carrito().agregar(p)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"ok": True, "carrito": state}), 200  # 201 si quieres crear-recurso


@bp.post("/eliminar/<int:producto_id>")
def eliminar_producto(producto_id: int):
    p = db.session.get(Producto, producto_id)
    if not p:
        return jsonify({"error": "Producto no encontrado"}), 404
    state = Carrito().eliminar(p)
    return jsonify({"ok": True, "carrito": state}), 200


@bp.post("/restar/<int:producto_id>")
def restar_producto(producto_id: int):
    p = db.session.get(Producto, producto_id)
    if not p:
        return jsonify({"error": "Producto no encontrado"}), 404
    state = Carrito().restar(p)
    return jsonify({"ok": True, "carrito": state}), 200


@bp.post("/limpiar")
def limpiar_carrito():
    state = Carrito().limpiar()
    return jsonify({"ok": True, "carrito": state}), 200


@bp.post("/validar")
def validar_carrito():
    """Valida y descuenta stock, luego limpia carrito."""
    exito, mensaje = validar_y_deducir()
    if exito:
        nuevo_estado = Carrito().limpiar()
        return jsonify({"exito": "Compra validada.", "carrito": nuevo_estado}), 200
    else:
        return jsonify({"error": mensaje or "Error validando carrito o stock insuficiente."}), 400


@bp.post("/pagar")
def procesar_pago():
    """Valida pago simulado y procesa compra."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Datos de pago requeridos."}), 400

    card_num = data.get("card_num", "").replace(" ", "").replace("-", "")
    exp = data.get("exp", "")  # MM/YY
    cvv = data.get("cvv", "")
    name = data.get("name", "").strip()

    # Validate card number
    if not card_num.isdigit() or not (13 <= len(card_num) <= 19) or not _luhn_checksum(card_num):
        return jsonify({"error": "Número de tarjeta inválido."}), 400

    # Validate expiration
    try:
        mm, yy = exp.split("/")
        mm = int(mm)
        yy = int("20" + yy)  # assume 20xx
        now = datetime.now()
        exp_date = datetime(yy, mm, 1)
        if exp_date < now:
            return jsonify({"error": "Tarjeta expirada."}), 400
    except:
        return jsonify({"error": "Fecha de expiración inválida (MM/YY)."}), 400

    # Validate CVV
    if not cvv.isdigit() or len(cvv) != 3:
        return jsonify({"error": "CVV inválido."}), 400

    # Validate name
    if not name:
        return jsonify({"error": "Nombre del titular requerido."}), 400

    # If all valid, process cart
    exito, mensaje = validar_y_deducir()
    if exito:
        return jsonify({"exito": "Pago procesado y compra validada."}), 200
    else:
        return jsonify({"error": mensaje or "Error procesando compra o stock insuficiente."}), 400


@bp.get("/boleta")
def generar_boleta():
    carrito = _get_carrito()
    items = carrito.get("items", {})
    if not items:
        return jsonify({"error": "Carrito vacío."}), 400

    fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    total = Decimal("0.00")
    for item in items.values():
        total += _to_decimal(item.get("acumulado"), Decimal("0.00"))

    Carrito().limpiar()

    return render_template(
        "boleta.html",
        fecha=fecha,
        carrito=items,
        total_carrito=float(total),
    )


@bp.get("/boleta_json")
def generar_boleta_json():
    """Devuelve la boleta en formato JSON (esperado por el frontend)."""
    carrito = _get_carrito()
    items = carrito.get("items", {})
    if not items:
        return jsonify({"error": "Carrito vacío."}), 400

    total = Decimal("0.00")
    for item in items.values():
        total += _to_decimal(item.get("acumulado"), Decimal("0.00"))

    return jsonify({
        "fecha": datetime.now().isoformat(),
        "carrito": {"items": items, "total": float(total)},
        "total_carrito": float(total),
    }), 200
