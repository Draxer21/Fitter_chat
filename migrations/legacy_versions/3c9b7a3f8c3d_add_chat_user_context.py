"""add chat user context table

Revision ID: 3c9b7a3f8c3d
Revises: 2f48eec72e9c
Create Date: 2025-10-08 21:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "3c9b7a3f8c3d"
down_revision = "7a9f8fb07064"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "chat_user_context",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sender_id", sa.String(length=80), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("allergies", sa.Text(), nullable=True),
        sa.Column("medical_conditions", sa.Text(), nullable=True),
        sa.Column("last_routine", sa.JSON(), nullable=True),
        sa.Column("last_diet", sa.JSON(), nullable=True),
        sa.Column("history", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("last_interaction_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name="fk_chat_context_user"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sender_id", name="uq_chat_context_sender"),
    )
    with op.batch_alter_table("chat_user_context", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_chat_user_context_sender_id"), ["sender_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_chat_user_context_user_id"), ["user_id"], unique=False)


def downgrade():
    with op.batch_alter_table("chat_user_context", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_chat_user_context_user_id"))
        batch_op.drop_index(batch_op.f("ix_chat_user_context_sender_id"))

    op.drop_table("chat_user_context")
