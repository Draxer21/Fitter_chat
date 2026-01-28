"""Add diet_plans and routine_plans tables.

Revision ID: 20260127_add_plan_tables
Revises: 20251226_add_user_hero_plan
Create Date: 2026-01-27 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260127_add_plan_tables"
down_revision = "20251226_merge_heads_hero_plan"
branch_labels = None
depends_on = None


def _json_type():
    return postgresql.JSONB().with_variant(sa.JSON, "sqlite")


def _uuid_type():
    return postgresql.UUID(as_uuid=True).with_variant(sa.String(36), "sqlite")


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)

    if not insp.has_table("diet_plans"):
        op.create_table(
            "diet_plans",
            sa.Column("id", _uuid_type(), primary_key=True, nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
            sa.Column("title", sa.String(length=120), nullable=False),
            sa.Column("goal", sa.String(length=120), nullable=True, server_default=""),
            sa.Column("content", _json_type(), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_diet_plans_user_id", "diet_plans", ["user_id"])
        op.create_index("ix_diet_plans_user_created", "diet_plans", ["user_id", "created_at"])

    if not insp.has_table("routine_plans"):
        op.create_table(
            "routine_plans",
            sa.Column("id", _uuid_type(), primary_key=True, nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
            sa.Column("title", sa.String(length=120), nullable=False),
            sa.Column("objective", sa.String(length=120), nullable=True, server_default=""),
            sa.Column("content", _json_type(), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_routine_plans_user_id", "routine_plans", ["user_id"])
        op.create_index("ix_routine_plans_user_created", "routine_plans", ["user_id", "created_at"])


def downgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)

    if insp.has_table("routine_plans"):
        op.drop_index("ix_routine_plans_user_created", table_name="routine_plans")
        op.drop_index("ix_routine_plans_user_id", table_name="routine_plans")
        op.drop_table("routine_plans")

    if insp.has_table("diet_plans"):
        op.drop_index("ix_diet_plans_user_created", table_name="diet_plans")
        op.drop_index("ix_diet_plans_user_id", table_name="diet_plans")
        op.drop_table("diet_plans")
