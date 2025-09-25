# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, request
from extensions import db
from gestor_inventario.models import Producto

bp = Blueprint("producto", __name__)

@bp.get("/")
def listar():
    items = Producto.query.order_by(Producto.id.desc()).all()
    return jsonify([{"id": p.id, "nombre": p.nombre, "precio": float(p.precio), "stock": p.stock} for p in items])

@bp.post("/")
def crear():
    data = request.get_json(force=True, silent=True) or {}
    p = Producto(nombre=data.get("nombre",""), precio=data.get("precio",0), stock=data.get("stock",0))
    db.session.add(p)
    db.session.commit()
    return jsonify({"id": p.id}), 201
