#!/usr/bin/env python
"""Ejecutar manualmente las columnas que faltan"""

from backend.app import create_app
from backend.extensions import db

app = create_app()

with app.app_context():
    try:
        # Añadir las columnas manualmente
        columns_to_add = [
            "ALTER TABLE \"user\" ADD COLUMN weight_kg FLOAT;",
            "ALTER TABLE \"user\" ADD COLUMN height_cm FLOAT;",
            "ALTER TABLE \"user\" ADD COLUMN body_fat_percent FLOAT;",
            "ALTER TABLE \"user\" ADD COLUMN fitness_goal VARCHAR(255);",
            "ALTER TABLE \"user\" ADD COLUMN dietary_preferences VARCHAR(255);",
            "ALTER TABLE \"user\" ADD COLUMN health_conditions JSON;",
            "ALTER TABLE \"user\" ADD COLUMN additional_notes TEXT;",
        ]
        
        for sql in columns_to_add:
            try:
                db.session.execute(db.text(sql))
                print(f"✓ Ejecutado: {sql.split()[3]}")
            except Exception as e:
                if "already exists" in str(e) or "ya existe" in str(e):
                    print(f"ℹ️ {sql.split()[3]} ya existe")
                else:
                    raise
        
        db.session.commit()
        print("\n✓ ¡Columnas de perfil añadidas correctamente!")
        
    except Exception as e:
        print(f"⚠️ Error: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
