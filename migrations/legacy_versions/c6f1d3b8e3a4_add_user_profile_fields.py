"""add profile fields to user

Revision ID: c6f1d3b8e3a4
Revises: 8f6a9d1c2b3e
Create Date: 2025-10-31 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c6f1d3b8e3a4"
down_revision = "8f6a9d1c2b3e"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(sa.Column("weight_kg", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("height_cm", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("body_fat_percent", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("fitness_goal", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("dietary_preferences", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("health_conditions", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("additional_notes", sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("additional_notes")
        batch_op.drop_column("health_conditions")
        batch_op.drop_column("dietary_preferences")
        batch_op.drop_column("fitness_goal")
        batch_op.drop_column("body_fat_percent")
        batch_op.drop_column("height_cm")
        batch_op.drop_column("weight_kg")

