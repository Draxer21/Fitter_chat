"""Add handoff_request table.

Revision ID: 20260319_add_handoff_request
Revises: 20260319_add_subscription
Create Date: 2026-03-19 00:00:02.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260319_add_handoff_request"
down_revision = "20260319_add_subscription"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "handoff_request",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("sender_id", sa.String(length=120), nullable=False),
        sa.Column("reason", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("assigned_admin_id", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["assigned_admin_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("handoff_request", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_handoff_request_user_id"), ["user_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("handoff_request", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_handoff_request_user_id"))

    op.drop_table("handoff_request")
