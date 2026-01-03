"""Add dislikes column to chat_user_context.

Revision ID: 20251201_add_dislikes_to_chat_user_context
Revises: 20251129_squash_schema
Create Date: 2025-12-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251201_add_dislikes_to_chat_user_context"
down_revision = "20251129_squash_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)

    # Skip if table absent
    if not insp.has_table("chat_user_context"):
        return

    existing_columns = {col["name"] for col in insp.get_columns("chat_user_context")}

    if "dislikes" not in existing_columns:
        op.add_column("chat_user_context", sa.Column("dislikes", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("chat_user_context", "dislikes")
