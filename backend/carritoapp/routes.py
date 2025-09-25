# -*- coding: utf-8 -*-
from datetime import datetime
from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy import select
from extensions import db
from gestor_inventario.models import Producto
from .carrito import Carrito

bp = Blueprint("carrito", __name__)

@bp.get("/tienda")  # (opcional si usas SSR; si usas React, consume JSON)
def tienda():
    productos = Producto.query.order_by(Producto.id.desc()).all()
    return render_template("tienda.html", productos=productos)

@bp.post("/agregar/<int:producto_id>")
def agregar_producto(producto_id):
    p = db.session.get(Producto, producto_id)
    if not p:
        return jsonify({"error": "Producto no encontrado"}), 404
    Carrito().agregar(p)
    return jsonify({"ok": True})

@bp.post("/eliminar/<int:producto_id>")
def eliminar_producto(producto_id):
    p = db.session.get(Producto, producto_id)
    if not p:
        return jsonify({"error": "Producto no encontrado"}), 404
    Carrito().eliminar(p)
    return jsonify({"ok": True})

@bp.post("/restar/<int:producto_id>")
def restar_producto(producto_id):
    p = db.session.get(Producto, producto_id)
    if not p:
        return jsonify({"error": "Producto no encontrado"}), 404
    Carrito().restar(p)
    return jsonify({"ok": True})

@bp.post("/limpiar")
def limpiar_carrito():
    Carrito().limpiar()
    return jsonify({"ok": True})

@bp.post("/validar")
def validar_carrito():
    if "carrito" not in session or not session["carrito"]:
        return jsonify({"error": "El carrito está vacío."}), 400

    carrito = session["carrito"]
    errores = []
    try:
        with db.session.begin():
            for item in carrito.values():
                pid  = int(item["producto_id"])
                cant = int(item["cantidad"])
                prod = db.session.execute(
                    select(Producto).where(Producto.id == pid).with_for_update()
                ).scalar_one()
                if cant > prod.stock:
                    errores.append(f"Stock insuficiente para {prod.nombre}. Quedan {prod.stock}.")
                else:
                    prod.stock -= cant
            if errores:
                db.session.rollback()
                return jsonify({"errores": errores}), 400
        return jsonify({"exito": "Compra validada."}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Error validando carrito."}), 500

@bp.get("/boleta")
def generar_boleta():
    if "carrito" not in session or not session["carrito"]:
        return jsonify({"error": "Carrito vacío."}), 400
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    carrito = session.pop("carrito", {})
    total = sum(float(i.get("acumulado", 0)) for i in carrito.values())
    session.modified = True
    return render_template("boleta.html", fecha=fecha, carrito=carrito, total_carrito=total)
