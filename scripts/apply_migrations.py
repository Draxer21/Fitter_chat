#!/usr/bin/env python
import sys
import traceback

try:
    from backend.app import create_app
    from alembic.config import Config
    from alembic import command
except Exception:
    traceback.print_exc()
    sys.exit(2)

app = create_app()

with app.app_context():
    try:
        import os
        cfg = Config("migrations/alembic.ini")
        # Ensure alembic knows the absolute script_location to avoid relative lookup issues
        migrations_path = os.path.abspath(os.path.join(os.getcwd(), "migrations"))
        cfg.set_main_option("script_location", migrations_path)
        # ensure script_location is relative to the ini file
        command.upgrade(cfg, "head")
        print("alembic upgrade head: OK")
    except Exception:
        traceback.print_exc()
        sys.exit(1)
