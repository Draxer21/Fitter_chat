# backend/gestor_inventario/routes.py
from flask import Blueprint, jsonify
from backend.app import db, Stock, Producto  # o importa desde tu módulo de modelos

bp = Blueprint("inventario", __name__)

@bp.get("/")
def resumen():
    rows = db.session.execute(
        db.select(Producto.nombre, Stock.cantidad).join(Stock, Stock.producto_id==Producto.id)
    ).all()
    return jsonify([{"producto": n, "cantidad": c} for n, c in rows])
