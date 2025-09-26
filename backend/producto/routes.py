# backend/producto/routes.py
from flask import Blueprint, jsonify, request
from ..extensions import db
from ..gestor_inventario.models import Producto

bp = Blueprint("producto", __name__)

# -----------------------
# LISTAR TODOS
# -----------------------
@bp.get("/")
def listar_productos():
    productos = Producto.query.all()
    return jsonify([
        {
            "id": p.id,
            "nombre": p.nombre,
            "precio": float(p.precio),
            "descripcion": p.descripcion,
            "categoria": p.categoria,
            "stock": p.stock
        }
        for p in productos
    ])

# -----------------------
# OBTENER POR ID
# -----------------------
@bp.get("/<int:producto_id>")
def obtener_producto(producto_id):
    p = Producto.query.get_or_404(producto_id)
    return jsonify({
        "id": p.id,
        "nombre": p.nombre,
        "precio": float(p.precio),
        "descripcion": p.descripcion,
        "categoria": p.categoria,
        "stock": p.stock
    })

# -----------------------
# CREAR
# -----------------------
@bp.post("/")
def crear_producto():
    data = request.get_json(force=True)
    p = Producto(
        nombre=data.get("nombre"),
        precio=data.get("precio", 0),
        descripcion=data.get("descripcion"),
        categoria=data.get("categoria"),
        stock=data.get("stock", 0),
    )
    db.session.add(p)
    db.session.commit()
    return jsonify({"message": "Producto creado", "id": p.id}), 201

# -----------------------
# ACTUALIZAR
# -----------------------
@bp.put("/<int:producto_id>")
def actualizar_producto(producto_id):
    p = Producto.query.get_or_404(producto_id)
    data = request.get_json(force=True)
    for campo in ["nombre", "precio", "descripcion", "categoria", "stock"]:
        if campo in data:
            setattr(p, campo, data[campo])
    db.session.commit()
    return jsonify({"message": "Producto actualizado"})

# -----------------------
# ELIMINAR
# -----------------------
@bp.delete("/<int:producto_id>")
def eliminar_producto(producto_id):
    p = Producto.query.get_or_404(producto_id)
    db.session.delete(p)
    db.session.commit()
    return jsonify({"message": "Producto eliminado"})
