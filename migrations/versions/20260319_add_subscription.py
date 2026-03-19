"""Add subscription table.

Revision ID: 20260319_add_subscription
Revises: 20260319_add_class_booking
Create Date: 2026-03-19 00:00:01.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260319_add_subscription"
down_revision = "20260319_add_class_booking"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "subscription",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("plan_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("start_date", sa.DateTime(), nullable=False),
        sa.Column("end_date", sa.DateTime(), nullable=True),
        sa.Column("auto_renew", sa.Boolean(), nullable=False),
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("subscription", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_subscription_user_id"), ["user_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("subscription", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_subscription_user_id"))

    op.drop_table("subscription")
