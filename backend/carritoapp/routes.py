# backend/carritoapp/routes.py
# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict

from flask import Blueprint, jsonify, render_template
from sqlalchemy import select

from ..extensions import db
from ..gestor_inventario.models import Producto
from .carrito import Carrito

bp = Blueprint("carrito", __name__)

# --------- Utilidades ---------
def _get_carrito() -> Dict[str, Any]:
    return Carrito().snapshot()


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
    """Valida y descuenta stock de todos los ítems del carrito atómicamente."""
    carrito_obj = Carrito()
    snapshot = carrito_obj.snapshot()
    items_data = snapshot.get("items", {})
    if not items_data:
        return jsonify({"error": "El carrito está vacío."}), 400

    # 1) Normaliza lista de (producto_id, cantidad)
    items: Dict[int, int] = {}
    for item in items_data.values():
        pid = _to_int(item.get("producto_id"), default=0)
        cant = max(1, _to_int(item.get("cantidad"), default=0))
        if pid > 0:
            items[pid] = items.get(pid, 0) + cant  # agrupa por producto

    if not items:
        return jsonify({"error": "Carrito inválido."}), 400

    try:
        with db.session.begin():
            # 2) Cargar y bloquear todos los productos del carrito
            productos = (
                db.session.execute(
                    select(Producto).where(Producto.id.in_(list(items.keys()))).with_for_update()
                )
                .scalars()
                .all()
            )
            by_id = {p.id: p for p in productos}

            # 3) Validar stocks
            errores = []
            for pid, cant in items.items():
                prod = by_id.get(pid)
                if not prod:
                    errores.append(f"Producto {pid} no existe.")
                    continue
                if cant > (prod.stock or 0):
                    errores.append(f"Stock insuficiente para {prod.nombre}. Quedan {prod.stock}.")

            if errores:
                return jsonify({"errores": errores}), 400

            # 4) Descontar y commit (dentro del begin)
            for pid, cant in items.items():
                prod = by_id[pid]
                prod.stock = (prod.stock or 0) - cant

        nuevo_estado = carrito_obj.limpiar()
        return jsonify({"exito": "Compra validada.", "carrito": nuevo_estado}), 200

    except Exception:
        db.session.rollback()
        return jsonify({"error": "Error validando carrito."}), 500


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
