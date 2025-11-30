"""Merge heads: connect squash migration with existing head.

Revision ID: 20251129_merge_squash_heads
Revises: 20251129_add_chat_id_to_chat_user_context, 20251129_squash_schema
Create Date: 2025-11-29 00:10:00.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251129_merge_squash_heads"
down_revision = ("20251129_add_chat_id_to_chat_user_context", "20251129_squash_schema")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # No-op merge: this file simply links the heads so Alembic has a single head.
    pass


def downgrade() -> None:
    pass
