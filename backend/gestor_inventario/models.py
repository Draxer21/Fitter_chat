# -*- coding: utf-8 -*-
from decimal import Decimal
from extensions import db

class Producto(db.Model):
    __tablename__ = "producto"
    id     = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    precio = db.Column(db.Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    stock  = db.Column(db.Integer, nullable=False, default=0)
