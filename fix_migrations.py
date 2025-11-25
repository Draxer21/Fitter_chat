#!/usr/bin/env python
"""Script para encontrar el punto de migración correcto"""

from backend.app import create_app
from backend.extensions import db

app = create_app()

with app.app_context():
    try:
        # Limpiar versiones previas
        db.session.execute(db.text("DELETE FROM alembic_version"))
        db.session.commit()
        print("✓ Tabla alembic_version limpiada")
        
        # Si user_profile existe, debemos marcar como si ambas ramas estuvieran completas
        query = "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'user_profile')"
        user_profile_exists = db.session.execute(db.text(query)).scalar()
        
        if user_profile_exists:
            print("✓ user_profile existe, marcando ambas ramas completas...")
            # Marcar ambas ramas como completadas
            db.session.execute(db.text("INSERT INTO alembic_version (version_num) VALUES ('c6f1d3b8e3a4')"))  # add profile fields
            db.session.execute(db.text("INSERT INTO alembic_version (version_num) VALUES ('a5b4d2c7fe80')"))  # add user profile table  
            db.session.execute(db.text("INSERT INTO alembic_version (version_num) VALUES ('cab3c72e1b0d')"))  # orders
            db.session.execute(db.text("INSERT INTO alembic_version (version_num) VALUES ('4a2e6b28f5da')"))  # secure profile storage
            db.session.execute(db.text("INSERT INTO alembic_version (version_num) VALUES ('20251129_merge_profiles_orders')"))  # merge
            db.session.commit()
            print("✓ BD marcada correctamente en versión merge!")
        else:
            print("❌ user_profile no existe")
        
    except Exception as e:
        print(f"⚠️ Error: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
