"""create orders tables

Revision ID: cab3c72e1b0d
Revises: b6e8f0b1d9a2
Create Date: 2025-11-01 16:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "cab3c72e1b0d"
down_revision = "b6e8f0b1d9a2"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "order",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("customer_name", sa.String(length=255), nullable=True),
        sa.Column("customer_email", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="paid"),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="CLP"),
        sa.Column("payment_method", sa.String(length=64), nullable=True),
        sa.Column("payment_reference", sa.String(length=255), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_order_created_at"), "order", ["created_at"], unique=False)
    op.create_index(op.f("ix_order_status"), "order", ["status"], unique=False)
    op.create_index(op.f("ix_order_user_id"), "order", ["user_id"], unique=False)

    op.create_table(
        "order_item",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("product_name", sa.String(length=255), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["order_id"], ["order.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_order_item_order_id"), "order_item", ["order_id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_order_item_order_id"), table_name="order_item")
    op.drop_table("order_item")
    op.drop_index(op.f("ix_order_user_id"), table_name="order")
    op.drop_index(op.f("ix_order_status"), table_name="order")
    op.drop_index(op.f("ix_order_created_at"), table_name="order")
    op.drop_table("order")
