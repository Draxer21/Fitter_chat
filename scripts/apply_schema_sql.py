#!/usr/bin/env python
import traceback
import sys

try:
    from backend.app import create_app
except Exception:
    traceback.print_exc()
    sys.exit(2)

SQL = """
-- Ensure producto table
CREATE TABLE IF NOT EXISTS producto (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    categoria VARCHAR(80),
    precio NUMERIC(10,2) NOT NULL DEFAULT 0.00,
    descripcion TEXT,
    stock INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_producto_categoria ON producto (categoria);
CREATE INDEX IF NOT EXISTS ix_producto_created_at ON producto (created_at);
CREATE INDEX IF NOT EXISTS ix_producto_nombre ON producto (nombre);

-- Ensure user table
CREATE TABLE IF NOT EXISTS "user" (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now()
);

-- Ensure chat_user_context table and chat_id
CREATE TABLE IF NOT EXISTS chat_user_context (
    id SERIAL PRIMARY KEY,
    sender_id VARCHAR(80) NOT NULL,
    user_id INTEGER,
    allergies TEXT,
    medical_conditions TEXT,
    last_routine JSON,
    last_diet JSON,
    history JSON NOT NULL DEFAULT '[]'::json,
    notes TEXT,
    last_interaction_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now()
);
-- Ensure chat_user_context table exists (may lack chat_id on older DBs)

-- Ensure chat_id column exists before creating indexes
ALTER TABLE chat_user_context ADD COLUMN IF NOT EXISTS chat_id VARCHAR(80);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_chat_context_sender'
    ) THEN
        ALTER TABLE chat_user_context ADD CONSTRAINT uq_chat_context_sender UNIQUE (sender_id);
    END IF;
EXCEPTION WHEN duplicate_table THEN
    NULL;
END
$$;
CREATE INDEX IF NOT EXISTS ix_chat_user_context_sender_id ON chat_user_context (sender_id);
CREATE INDEX IF NOT EXISTS ix_chat_user_context_chat_id ON chat_user_context (chat_id);
CREATE INDEX IF NOT EXISTS ix_chat_user_context_user_id ON chat_user_context (user_id);

"""

app = create_app()
with app.app_context():
    engine = app.extensions['migrate'].db.get_engine()
    print('Applying schema SQL to DB:', engine.url)
    try:
        with engine.connect() as conn:
            with conn.begin():
                # exec_driver_sql runs the full SQL block
                conn.exec_driver_sql(SQL)
        print('Schema SQL applied successfully.')
    except Exception:
        traceback.print_exc()
        sys.exit(1)
