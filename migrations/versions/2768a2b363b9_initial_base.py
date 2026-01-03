"""Placeholder base revision to satisfy historical migrations.

Revision ID: 2768a2b363b9
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""

from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401

# revision identifiers, used by Alembic.
revision = "2768a2b363b9"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Historical placeholder; no schema changes required."""
    pass


def downgrade() -> None:
    """Historical placeholder; no schema changes required."""
    pass
