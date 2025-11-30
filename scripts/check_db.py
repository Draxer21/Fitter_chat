#!/usr/bin/env python
"""Verificar estado de la base de datos"""

from backend.app import create_app
from backend.extensions import db

app = create_app()

with app.app_context():
    # Verificar si existe weight_kg
    query = "SELECT EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name = 'user' AND column_name = 'weight_kg')"
    result = db.session.execute(db.text(query)).scalar()
    print(f"✓ weight_kg exists: {result}")
    
    # Listar todas las columnas de user
    query = "SELECT column_name FROM information_schema.columns WHERE table_name = 'user' ORDER BY ordinal_position"
    result = db.session.execute(db.text(query)).fetchall()
    print("\n✓ Columnas en tabla 'user':")
    for row in result:
        print(f"  - {row[0]}")
