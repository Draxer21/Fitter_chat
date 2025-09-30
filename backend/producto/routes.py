# backend/producto/routes.py
from flask import Blueprint, jsonify, request, current_app
import os
import uuid
from werkzeug.utils import secure_filename
from ..extensions import db
from ..gestor_inventario.models import Producto

bp = Blueprint("producto", __name__)

# -----------------------
# LISTAR TODOS
# -----------------------
@bp.get("/")
def listar_productos():
    productos = Producto.query.all()
    return jsonify([p.to_dict() for p in productos])

# -----------------------
# OBTENER POR ID
# -----------------------
@bp.get("/<int:producto_id>")
def obtener_producto(producto_id):
    p = Producto.query.get_or_404(producto_id)
    return jsonify(p.to_dict())

# -----------------------
# CREAR
# -----------------------
@bp.post("/")
def crear_producto():
    # Soportar tanto JSON como multipart/form-data con archivo 'imagen'
    if request.content_type and request.content_type.startswith('multipart/form-data'):
        nombre = request.form.get('nombre')
        precio = request.form.get('precio', 0)
        descripcion = request.form.get('descripcion')
        categoria = request.form.get('categoria')
        stock = request.form.get('stock', 0)
    else:
        data = request.get_json(force=True)
        nombre = data.get('nombre')
        precio = data.get('precio', 0)
        descripcion = data.get('descripcion')
        categoria = data.get('categoria')
        stock = data.get('stock', 0)

    p = Producto(
        nombre=nombre,
        precio=precio,
        descripcion=descripcion,
        categoria=categoria,
        stock=stock,
    )

    # Manejar subida de imagen si existe
    imagen = request.files.get('imagen')
    if imagen:
        uploads = os.path.join(current_app.static_folder or 'static', 'uploads')
        os.makedirs(uploads, exist_ok=True)
        filename = secure_filename(imagen.filename)
        # añadir uuid para evitar colisiones
        name, ext = os.path.splitext(filename)
        filename = f"{name}-{uuid.uuid4().hex}{ext}"
        path = os.path.join(uploads, filename)
        imagen.save(path)
        p.imagen_filename = filename

    db.session.add(p)
    db.session.commit()
    return jsonify({"message": "Producto creado", "id": p.id}), 201

# -----------------------
# ACTUALIZAR
# -----------------------
@bp.put("/<int:producto_id>")
def actualizar_producto(producto_id):
    p = Producto.query.get_or_404(producto_id)
    # Soportar actualización por JSON o multipart/form-data (incluye nueva imagen)
    if request.content_type and request.content_type.startswith('multipart/form-data'):
        form = request.form
        for campo in ["nombre", "precio", "descripcion", "categoria", "stock"]:
            if campo in form:
                setattr(p, campo, form.get(campo))
        imagen = request.files.get('imagen')
        if imagen:
            uploads = os.path.join(current_app.static_folder or 'static', 'uploads')
            os.makedirs(uploads, exist_ok=True)
            filename = secure_filename(imagen.filename)
            name, ext = os.path.splitext(filename)
            filename = f"{name}-{uuid.uuid4().hex}{ext}"
            path = os.path.join(uploads, filename)
            imagen.save(path)
            p.imagen_filename = filename
    else:
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
