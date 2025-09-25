# -*- coding: utf-8 -*-
from flask import session

class Carrito:
    def __init__(self, session_obj=None):
        self.session = session_obj or session
        self.carrito = self.session.setdefault("carrito", {})

    def guardar(self):
        self.session["carrito"] = self.carrito
        self.session.modified = True

    def agregar(self, producto):
        pid = str(producto.id)
        if pid not in self.carrito:
            self.carrito[pid] = {
                "producto_id": producto.id,
                "nombre": producto.nombre,
                "acumulado": float(producto.precio),
                "cantidad": 1,
                "precio_unitario": float(producto.precio),
            }
        else:
            self.carrito[pid]["cantidad"]  += 1
            self.carrito[pid]["acumulado"] += float(producto.precio)
        self.guardar()

    def eliminar(self, producto):
        pid = str(producto.id)
        if pid in self.carrito:
            del self.carrito[pid]
            self.guardar()

    def restar(self, producto):
        pid = str(producto.id)
        if pid in self.carrito:
            self.carrito[pid]["cantidad"]  -= 1
            self.carrito[pid]["acumulado"] -= float(producto.precio)
            if self.carrito[pid]["cantidad"] <= 0:
                self.eliminar(producto)
            else:
                self.guardar()

    def limpiar(self):
        self.session["carrito"] = {}
        self.session.modified = True
