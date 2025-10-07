"""Add username column to user table.

Revision ID: 20251007_add_username_to_user
Revises: 
Create Date: 2025-10-07 20:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251007_add_username_to_user"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user", sa.Column("username", sa.String(length=80), nullable=True))
    op.create_index(op.f("ix_user_username"), "user", ["username"], unique=True)
    op.execute('UPDATE "user" SET username = email WHERE username IS NULL')
    op.alter_column("user", "username", nullable=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_user_username"), table_name="user")
    op.drop_column("user", "username")
