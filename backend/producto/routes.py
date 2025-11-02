# backend/producto/routes.py
from flask import Blueprint, jsonify, request, current_app
import json
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
    is_multipart = request.content_type and request.content_type.startswith('multipart/form-data')
    data = {}
    if is_multipart:
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

    def _parse_json_field(value):
        if value in (None, "", []):
            return None
        if isinstance(value, (dict, list)):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None

    brand = None
    rating = None
    rating_count = None
    gallery = None
    specifications = None
    highlights = None

    source = request.form if is_multipart else data
    if source:
        brand = source.get('brand')
        rating_raw = source.get('rating')
        rating_count_raw = source.get('rating_count')
        gallery = _parse_json_field(source.get('gallery'))
        specifications = _parse_json_field(source.get('specifications'))
        highlights = _parse_json_field(source.get('highlights'))
        try:
            if rating_raw not in (None, ""):
                rating = float(rating_raw)
        except (TypeError, ValueError):
            rating = None
        try:
            if rating_count_raw not in (None, ""):
                rating_count = int(rating_count_raw)
        except (TypeError, ValueError):
            rating_count = None

    p = Producto(
        nombre=nombre,
        precio=precio,
        descripcion=descripcion,
        categoria=categoria,
        stock=stock,
        brand=brand,
        rating=rating,
        rating_count=rating_count,
        gallery=gallery,
        specifications=specifications,
        highlights=highlights,
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
        def _parse_json_field(value):
            if value in (None, "", []):
                return None
            if isinstance(value, (dict, list)):
                return value
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return None
            return None
        if "brand" in form:
            p.brand = form.get("brand")
        if "rating" in form:
            try:
                p.rating = float(form.get("rating"))
            except (TypeError, ValueError):
                p.rating = None
        if "rating_count" in form:
            try:
                p.rating_count = int(form.get("rating_count"))
            except (TypeError, ValueError):
                p.rating_count = None
        if "gallery" in form:
            p.gallery = _parse_json_field(form.get("gallery"))
        if "specifications" in form:
            p.specifications = _parse_json_field(form.get("specifications"))
        if "highlights" in form:
            p.highlights = _parse_json_field(form.get("highlights"))
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
        def _parse_json_field(value):
            if value in (None, "", []):
                return None
            if isinstance(value, (dict, list)):
                return value
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return None
            return None
        if "brand" in data:
            p.brand = data.get("brand")
        if "rating" in data:
            try:
                p.rating = float(data.get("rating"))
            except (TypeError, ValueError):
                p.rating = None
        if "rating_count" in data:
            try:
                p.rating_count = int(data.get("rating_count"))
            except (TypeError, ValueError):
                p.rating_count = None
        if "gallery" in data:
            p.gallery = _parse_json_field(data.get("gallery"))
        if "specifications" in data:
            p.specifications = _parse_json_field(data.get("specifications"))
        if "highlights" in data:
            p.highlights = _parse_json_field(data.get("highlights"))
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
