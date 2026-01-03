"""add totp fields to user

Revision ID: 8f6a9d1c2b3e
Revises: 3c9b7a3f8c3d
Create Date: 2025-10-30 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8f6a9d1c2b3e"
down_revision = "3c9b7a3f8c3d"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(sa.Column("totp_secret", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("totp_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")))
        batch_op.add_column(sa.Column("totp_enabled_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("totp_backup_codes", sa.JSON(), nullable=True))
        batch_op.alter_column("totp_enabled", server_default=None)


def downgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("totp_backup_codes")
        batch_op.drop_column("totp_enabled_at")
        batch_op.drop_column("totp_enabled")
        batch_op.drop_column("totp_secret")
