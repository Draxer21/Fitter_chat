"""add rich product metadata

Revision ID: b6e8f0b1d9a2
Revises: e2716ca87846
Create Date: 2025-10-31 19:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b6e8f0b1d9a2"
down_revision = "e2716ca87846"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("producto", schema=None) as batch_op:
        batch_op.add_column(sa.Column("gallery", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("specifications", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("highlights", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("brand", sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column("rating", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("rating_count", sa.Integer(), nullable=True))


def downgrade():
    with op.batch_alter_table("producto", schema=None) as batch_op:
        batch_op.drop_column("rating_count")
        batch_op.drop_column("rating")
        batch_op.drop_column("brand")
        batch_op.drop_column("highlights")
        batch_op.drop_column("specifications")
        batch_op.drop_column("gallery")
