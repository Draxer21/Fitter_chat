"""Merge heads for hero plan and fitness classes.

Revision ID: 20251226_merge_heads_hero_plan
Revises: 20251226_add_user_hero_plan, b6a0482aab51
Create Date: 2025-12-26 00:00:00.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251226_merge_heads_hero_plan"
down_revision = ("20251226_add_user_hero_plan", "b6a0482aab51")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
