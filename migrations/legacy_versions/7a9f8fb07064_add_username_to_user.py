"""add username column to user

Revision ID: 7a9f8fb07064
Revises: 58f8c303b7c2
Create Date: 2025-10-09 16:05:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7a9f8fb07064"
down_revision = "58f8c303b7c2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(sa.Column("username", sa.String(length=80), nullable=True))

    # Populate username with the local-part of the email when possible
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE "user"
            SET username = SPLIT_PART(email, '@', 1)
            WHERE username IS NULL AND email IS NOT NULL
            """
        )
    )

    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.alter_column("username", existing_type=sa.String(length=80), nullable=False)
        batch_op.create_index(batch_op.f("ix_user_username"), ["username"], unique=True)


def downgrade() -> None:
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_user_username"))
        batch_op.drop_column("username")
