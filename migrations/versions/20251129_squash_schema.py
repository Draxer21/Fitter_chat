"""Squash migration: ensure core schema exists (idempotent)

This migration is intentionally idempotent and uses SQL `IF NOT EXISTS` where
supported by the DB (Postgres). It is intended for fresh installs: it creates
the main tables and ensures the `chat_user_context.chat_id` column exists.

Revision ID: 20251129_squash_schema
Revises: 20251129_add_chat_id_to_chat_user_context
Create Date: 2025-11-29 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251129_squash_schema"
down_revision = "20251129_add_chat_id_to_chat_user_context"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name

    # We'll use raw SQL with IF NOT EXISTS for Postgres; for other dialects
    # we fall back to a safe approach using SQLAlchemy where possible.

    # --- producto table (from initial schema) ---
    if dialect == 'postgresql':
        op.execute(
            """
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
            """
        )
    else:
        # conservative: create table if not present via SQLAlchemy
        meta = sa.MetaData()
        producto = sa.Table(
            'producto', meta,
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('nombre', sa.String(255), nullable=False),
            sa.Column('categoria', sa.String(80)),
            sa.Column('precio', sa.Numeric(10, 2), server_default='0.00', nullable=False),
            sa.Column('descripcion', sa.Text),
            sa.Column('stock', sa.Integer, server_default='0', nullable=False),
            sa.Column('created_at', sa.DateTime),
            sa.Column('updated_at', sa.DateTime),
        )
        producto.create(bind=conn, checkfirst=True)

    # --- user table basic (if missing) ---
    if dialect == 'postgresql':
        op.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_user_context (
                id SERIAL PRIMARY KEY,
                sender_id VARCHAR(80) NOT NULL,
                user_id INTEGER,
                allergies TEXT,
                dislikes TEXT,
                medical_conditions TEXT,
                last_routine JSON,
                last_diet JSON,
                history JSON NOT NULL DEFAULT '[]'::json,
                notes TEXT,
                last_interaction_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
                updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now()
            );
            """
        )
    # --- Ensure chat_id column exists if table already present ---
    if dialect == 'postgresql':
        # alter table add column if not exists
        op.execute("ALTER TABLE chat_user_context ADD COLUMN IF NOT EXISTS chat_id VARCHAR(80);")
        op.execute("DO $$\nBEGIN\n    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_chat_context_sender') THEN\n        ALTER TABLE chat_user_context ADD CONSTRAINT uq_chat_context_sender UNIQUE (sender_id);\n    END IF;\nEND\n$$;")
        op.execute("CREATE INDEX IF NOT EXISTS ix_chat_user_context_sender_id ON chat_user_context (sender_id);")
        op.execute("CREATE INDEX IF NOT EXISTS ix_chat_user_context_chat_id ON chat_user_context (chat_id);")
        op.execute("CREATE INDEX IF NOT EXISTS ix_chat_user_context_user_id ON chat_user_context (user_id);")
        op.execute("ALTER TABLE chat_user_context ADD COLUMN IF NOT EXISTS dislikes TEXT;")
    else:
        meta = sa.MetaData()
        chat = sa.Table(
            'chat_user_context', meta,
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('sender_id', sa.String(80), nullable=False),
            sa.Column('chat_id', sa.String(80), nullable=True),
            sa.Column('user_id', sa.Integer),
            sa.Column('allergies', sa.Text),
            sa.Column('dislikes', sa.Text),
            sa.Column('medical_conditions', sa.Text),
            sa.Column('last_routine', sa.JSON),
            sa.Column('last_diet', sa.JSON),
            sa.Column('history', sa.JSON, nullable=False, server_default=sa.text("'[]'")),
            sa.Column('notes', sa.Text),
            sa.Column('last_interaction_at', sa.DateTime),
            sa.Column('created_at', sa.DateTime),
            sa.Column('updated_at', sa.DateTime),
        )
        chat.create(bind=conn, checkfirst=True)
        # create indexes
        try:
            op.create_index('ix_chat_user_context_sender_id', 'chat_user_context', ['sender_id'])
        except Exception:
            pass
        try:
            op.create_index('ix_chat_user_context_chat_id', 'chat_user_context', ['chat_id'])
        except Exception:
            pass

    # --- Ensure chat_id column exists if table already present ---
    if dialect == 'postgresql':
        # alter table add column if not exists
        op.execute("ALTER TABLE chat_user_context ADD COLUMN IF NOT EXISTS chat_id VARCHAR(80);")
        op.execute("ALTER TABLE chat_user_context ADD COLUMN IF NOT EXISTS dislikes TEXT;")
        op.execute("CREATE INDEX IF NOT EXISTS ix_chat_user_context_chat_id ON chat_user_context (chat_id);")
    else:
        # best-effort: try to add column
        try:
            op.add_column('chat_user_context', sa.Column('chat_id', sa.String(80), nullable=True))
        except Exception:
            pass
        try:
            op.add_column('chat_user_context', sa.Column('dislikes', sa.Text(), nullable=True))
        except Exception:
            pass


def downgrade() -> None:
    # This squash migration is intended to be forward-only; downgrading is a noop.
    pass
