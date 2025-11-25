"""Merge profile encryption branch with orders branch.

Revision ID: 20251129_merge_profiles_orders
Revises: 4a2e6b28f5da, cab3c72e1b0d
Create Date: 2025-11-29 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251129_merge_profiles_orders"
down_revision = ("4a2e6b28f5da", "cab3c72e1b0d")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Solo une las ramas; no se requieren cambios de esquema.
    pass


def downgrade() -> None:
    # No hay cambios que revertir.
    pass
