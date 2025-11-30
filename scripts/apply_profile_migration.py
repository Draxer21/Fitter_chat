#!/usr/bin/env python
"""Marcar las migraciones sin ejecutarlas (ya existen en BD)"""

from backend.app import create_app
from backend.extensions import db

app = create_app()

with app.app_context():
    try:
        # Limpiar
        db.session.execute(db.text("DELETE FROM alembic_version"))
        db.session.commit()
        print("✓ Tabla limpiada")
        
        # Marcar todas las migraciones que ya están aplicadas en la BD
        migrations = [
            '2f48eec72e9c',  # initial schema
            '58f8c303b7c2',  # add user table
            '7a9f8fb07064',  # add username to user
            '8f6a9d1c2b3e',  # add totp fields
            'c6f1d3b8e3a4',  # add profile fields to user
            'a5b4d2c7fe80',  # add user profile table
            'b6e8f0b1d9a2',  # add rich product metadata
            '3edcf041f1aa',  # imagen producto
            '3c9b7a3f8c3d',  # add chat user context
            'cab3c72e1b0d',  # create orders tables
            'e2716ca87846',  # merge heads
            '4a2e6b28f5da',  # secure profile storage
            '20251129_merge_profiles_orders',  # merge final
        ]
        
        for migration in migrations:
            try:
                db.session.execute(db.text(f"INSERT INTO alembic_version (version_num) VALUES ('{migration}')"))
            except:
                pass  # Ya existe
        
        db.session.commit()
        print(f"✓ {len(migrations)} migraciones marcadas como aplicadas")
        
        # Verificar el estado
        result = db.session.execute(db.text("SELECT COUNT(*) FROM alembic_version")).scalar()
        print(f"✓ Total migraciones en BD: {result}")
        
    except Exception as e:
        print(f"⚠️ Error: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()

