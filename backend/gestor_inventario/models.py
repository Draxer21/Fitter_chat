# backend/gestor_inventario/models.py
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from ..extensions import db

# tabla puente M2M
producto_categoria = db.Table(
    "producto_categoria",
    db.Column("producto_id", db.Integer, db.ForeignKey("producto.id"), primary_key=True),
    db.Column("categoria_id", db.Integer, db.ForeignKey("categoria.id"), primary_key=True),
)

class Categoria(db.Model):
    __tablename__ = "categoria"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), unique=True, nullable=False, index=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Categoria id={self.id} nombre={self.nombre!r}>"

class Producto(db.Model):
    __tablename__ = "producto"

    id = db.Column(db.Integer, primary_key=True)

    nombre = db.Column(db.String(255), nullable=False, index=True)
    # si quieres mantener una sola categoría “principal” además del M2M:
    categoria = db.Column(db.String(80), index=True)

    precio = db.Column(db.Numeric(10, 2), nullable=False, server_default="0.00")
    descripcion = db.Column(db.Text)
    stock = db.Column(db.Integer, nullable=False, server_default="0")

    # NUEVO: nombre del archivo de imagen (en /static/uploads)
    imagen_filename = db.Column(db.String(255))  # null si no hay imagen

    # relación M2M
    categorias = db.relationship("Categoria", secondary=producto_categoria, backref="productos", lazy="joined")

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.CheckConstraint("stock >= 0", name="ck_producto_stock_nonneg"),
        db.CheckConstraint("precio >= 0", name="ck_producto_precio_nonneg"),
    )

    def __repr__(self) -> str:
        return f"<Producto id={self.id} nombre={self.nombre!r} precio={self.precio} stock={self.stock}>"

    def imagen_url(self) -> str | None:
        if not self.imagen_filename:
            return None
        # sirve desde /static/uploads/<filename>
        return f"/static/uploads/{self.imagen_filename}"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "precio": str(self.precio) if isinstance(self.precio, Decimal) else self.precio,
            "descripcion": self.descripcion,
            "categoria": self.categoria,  # legado / principal (opcional)
            "stock": self.stock,
            "imagen_url": self.imagen_url(),
            "categorias": [c.nombre for c in self.categorias],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
