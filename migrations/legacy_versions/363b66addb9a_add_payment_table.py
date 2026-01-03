"""add payment table

Revision ID: 363b66addb9a
Revises: 20251129_merge_profiles_orders
Create Date: 2025-11-25 15:57:36.152840

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '363b66addb9a'
down_revision = '20251129_merge_profiles_orders'
branch_labels = None
depends_on = None


def upgrade():
    # Crear tabla payment
    op.create_table('payment',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('order_id', sa.Integer(), nullable=False),
    sa.Column('preference_id', sa.String(length=255), nullable=False),
    sa.Column('payment_id', sa.String(length=255), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('transaction_amount', sa.Float(), nullable=False),
    sa.Column('currency_id', sa.String(length=10), nullable=True),
    sa.Column('payment_method_id', sa.String(length=50), nullable=True),
    sa.Column('payment_type_id', sa.String(length=50), nullable=True),
    sa.Column('merchant_order_id', sa.String(length=255), nullable=True),
    sa.Column('external_reference', sa.String(length=255), nullable=True),
    sa.Column('payer_email', sa.String(length=255), nullable=True),
    sa.Column('payer_id', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('approved_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['order_id'], ['order.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('preference_id'),
    sa.UniqueConstraint('payment_id')
    )


def downgrade():
    # Eliminar tabla payment
    op.drop_table('payment')
