"""Add user hero plans table.

Revision ID: 20251226_add_user_hero_plan
Revises: 20251210_add_google_auth_columns
Create Date: 2025-12-26 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20251226_add_user_hero_plan"
down_revision = "20251210_add_google_auth_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    if insp.has_table("user_hero_plan"):
        return

    json_type = postgresql.JSONB().with_variant(sa.JSON, "sqlite")

    op.create_table(
        "user_hero_plan",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("plan_key", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=140), nullable=False),
        sa.Column("payload", json_type, nullable=False),
        sa.Column("source", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_user_hero_plan_user_id", "user_hero_plan", ["user_id"])
    op.create_index("ix_user_hero_plan_plan_key", "user_hero_plan", ["plan_key"])


def downgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    if not insp.has_table("user_hero_plan"):
        return
    op.drop_index("ix_user_hero_plan_plan_key", table_name="user_hero_plan")
    op.drop_index("ix_user_hero_plan_user_id", table_name="user_hero_plan")
    op.drop_table("user_hero_plan")
