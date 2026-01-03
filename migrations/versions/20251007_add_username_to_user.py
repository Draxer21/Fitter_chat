"""Add username column to user table.

Revision ID: 20251007_add_username_to_user
Revises: 
Create Date: 2025-10-07 20:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251007_add_username_to_user"
down_revision = "20250901_expand_alembic_version_len"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {col["name"] for col in inspector.get_columns("user")}
    existing_indexes = {idx["name"] for idx in inspector.get_indexes("user")}

    if "username" not in existing_columns:
        op.add_column("user", sa.Column("username", sa.String(length=80), nullable=True))

    if "ix_user_username" not in existing_indexes:
        op.create_index(op.f("ix_user_username"), "user", ["username"], unique=True)

    op.execute('UPDATE "user" SET username = email WHERE username IS NULL')
    op.alter_column("user", "username", nullable=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_indexes = {idx["name"] for idx in inspector.get_indexes("user")}
    existing_columns = {col["name"] for col in inspector.get_columns("user")}

    if "ix_user_username" in existing_indexes:
        op.drop_index(op.f("ix_user_username"), table_name="user")
    if "username" in existing_columns:
        op.drop_column("user", "username")
