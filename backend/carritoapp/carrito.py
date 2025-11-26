# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict

from flask import session


class Carrito:
    def __init__(self, session_obj=None):
        self.session = session_obj or session
        raw = self.session.get("carrito")
        if not isinstance(raw, dict) or "items" not in raw:
            items = raw if isinstance(raw, dict) else {}
            if items and all(isinstance(v, dict) for v in items.values()):
                total = sum(float(v.get("acumulado", 0)) for v in items.values())
            else:
                items = {}
                total = 0.0
            raw = {"items": items, "total": float(total)}
        raw.setdefault("items", {})
        raw.setdefault("total", 0.0)
        self.carrito: Dict[str, Any] = raw
        self.session["carrito"] = self.carrito

    @property
    def items(self) -> Dict[str, Dict[str, Any]]:
        return self.carrito.setdefault("items", {})

    def guardar(self) -> None:
        self.session["carrito"] = self.carrito
        self.session.modified = True

    def _recalcular_total(self) -> None:
        total = sum(Decimal(str(item.get("acumulado", 0))) for item in self.items.values())
        self.carrito["total"] = float(total)

    def _actualizar_item(self, pid: str, nombre: str, precio_unitario: float, cantidad: int, imagen: str = None) -> None:
        acumulado = float(Decimal(str(precio_unitario)) * cantidad)
        self.items[pid] = {
            "producto_id": int(pid),
            "nombre": nombre,
            "cantidad": cantidad,
            "precio_unitario": precio_unitario,
            "acumulado": acumulado,
            "imagen": imagen,
        }

    def agregar(self, producto) -> Dict[str, Any]:
        pid = str(producto.id)
        stock_disponible = producto.stock if producto.stock is not None else None
        actual = self.items.get(pid)
        cantidad_actual = actual.get("cantidad", 0) if actual else 0
        if stock_disponible is not None and cantidad_actual >= stock_disponible:
            raise ValueError(f"No hay stock suficiente para {producto.nombre}.")

        cantidad_nueva = cantidad_actual + 1
        precio_unitario = float(producto.precio)
        imagen = producto.imagen_url() if hasattr(producto, 'imagen_url') else None
        self._actualizar_item(pid, producto.nombre, precio_unitario, cantidad_nueva, imagen)
        self._recalcular_total()
        self.guardar()
        return self.snapshot()

    def eliminar(self, producto) -> Dict[str, Any]:
        pid = str(producto.id)
        if pid in self.items:
            self.items.pop(pid)
            self._recalcular_total()
            self.guardar()
        return self.snapshot()

    def restar(self, producto) -> Dict[str, Any]:
        pid = str(producto.id)
        if pid in self.items:
            item = self.items[pid]
            nueva_cantidad = item.get("cantidad", 0) - 1
            if nueva_cantidad <= 0:
                self.items.pop(pid)
            else:
                precio_unitario = float(producto.precio)
                imagen = producto.imagen_url() if hasattr(producto, 'imagen_url') else item.get("imagen")
                self._actualizar_item(pid, item.get("nombre", producto.nombre), precio_unitario, nueva_cantidad, imagen)
            self._recalcular_total()
            self.guardar()
        return self.snapshot()

    def limpiar(self) -> Dict[str, Any]:
        self.carrito = {"items": {}, "total": 0.0}
        self.guardar()
        return self.snapshot()

    def snapshot(self) -> Dict[str, Any]:
        return {
            "items": {pid: item.copy() for pid, item in self.items.items()},
            "total": float(self.carrito.get("total", 0.0) or 0.0),
        }
