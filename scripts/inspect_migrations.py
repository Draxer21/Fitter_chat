#!/usr/bin/env python
import os
import sys
import traceback

try:
    from backend.app import create_app
    from sqlalchemy import text
except Exception:
    traceback.print_exc()
    sys.exit(2)

def list_revision_files(path):
    revs = {}
    if not os.path.isdir(path):
        return revs
    for fn in os.listdir(path):
        if not fn.endswith('.py'):
            continue
        p = os.path.join(path, fn)
        try:
            with open(p, 'r', encoding='utf-8') as fh:
                data = fh.read()
            # crude parse
            for line in data.splitlines():
                if line.strip().startswith('revision ='):
                    rev = line.split('=',1)[1].strip().strip('"\'')
                    revs[rev] = fn
                    break
        except Exception:
            pass
    return revs

app = create_app()
with app.app_context():
    engine = app.extensions['migrate'].db.get_engine()
    print('DB url:', str(engine.url))
    try:
        with engine.connect() as conn:
            res = conn.execute(text("SELECT version_num FROM alembic_version"))
            rows = res.fetchall()
            if rows:
                for r in rows:
                    print('alembic_version:', r[0])
            else:
                print('alembic_version: <empty>')
    except Exception as e:
        print('Could not read alembic_version table:', e)

    base = os.getcwd()
    backend_versions = os.path.join(base, 'backend', 'migrations', 'versions')
    root_versions = os.path.join(base, 'migrations', 'versions')
    print('\nBackend migrations:')
    for rev, fn in sorted(list_revision_files(backend_versions).items()):
        print(' ', rev, fn)
    print('\nRoot migrations:')
    for rev, fn in sorted(list_revision_files(root_versions).items()):
        print(' ', rev, fn)
