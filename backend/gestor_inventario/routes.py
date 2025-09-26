# backend/gestor_inventario/routes.py
from flask import Blueprint, jsonify
from ..extensions import db
from .models import Producto

bp = Blueprint("inventario", __name__)

@bp.get("/")
def resumen():
    # Devuelve lista de productos y su stock
    rows = db.session.execute(
        db.select(Producto.nombre, Producto.stock)
    ).all()
    return jsonify([{"producto": n, "cantidad": c} for (n, c) in rows])
