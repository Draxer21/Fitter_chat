# -*- coding: utf-8 -*-
from flask import session

def total_carrito():
    total = 0
    for v in session.get("carrito", {}).values():
        total += float(v.get("acumulado", 0))
    return {"total_carrito": total}
