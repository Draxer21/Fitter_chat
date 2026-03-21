"""Add class_booking table.

Revision ID: 20260319_add_class_booking
Revises: 20260208_add_chat_consent_and_interaction_result
Create Date: 2026-03-19 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260319_add_class_booking"
down_revision = "20260208_add_chat_consent_and_interaction_result"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "class_booking",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("booked_at", sa.DateTime(), nullable=False),
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["class_session.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "user_id", name="uq_booking_session_user"),
    )
    with op.batch_alter_table("class_booking", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_class_booking_session_id"), ["session_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_class_booking_user_id"), ["user_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("class_booking", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_class_booking_user_id"))
        batch_op.drop_index(batch_op.f("ix_class_booking_session_id"))

    op.drop_table("class_booking")
