"""Add chat_id column to chat_user_context.

Revision ID: 20251129_add_chat_id_to_chat_user_context
Revises: 20251128_encrypt_user_profile_payload
Create Date: 2025-11-29 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251129_add_chat_id_to_chat_user_context"
down_revision = "20251128_encrypt_user_profile_payload"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)

    # Skip if table is missing (nothing to do on fresh empty DBs)
    if not insp.has_table("chat_user_context"):
        return

    existing_columns = {col["name"] for col in insp.get_columns("chat_user_context")}
    existing_indexes = {idx["name"] for idx in insp.get_indexes("chat_user_context")}

    # Add nullable chat_id column and an index for faster lookups, but only if absent
    if "chat_id" not in existing_columns:
        op.add_column(
            "chat_user_context",
            sa.Column("chat_id", sa.String(length=80), nullable=True),
        )

    if "ix_chat_user_context_chat_id" not in existing_indexes:
        op.create_index(
            "ix_chat_user_context_chat_id",
            "chat_user_context",
            ["chat_id"],
        )


def downgrade() -> None:
    op.drop_index("ix_chat_user_context_chat_id", table_name="chat_user_context")
    op.drop_column("chat_user_context", "chat_id")
