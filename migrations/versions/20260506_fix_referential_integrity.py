"""Fix referential integrity: FK on OrderItem.product_id, numeric column
on ProgressLog, and order_id on Subscription.

Revision ID: 20260506_fix_ri
Revises: 6446a7afbd9a
Create Date: 2026-05-06 00:00:01.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260506_fix_ri"
down_revision = "6446a7afbd9a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) OrderItem.product_id -> FK to producto.id
    with op.batch_alter_table("order_item", schema=None) as batch_op:
        batch_op.create_foreign_key(
            "fk_order_item_product_id",
            "producto",
            ["product_id"],
            ["id"],
            ondelete="SET NULL",
        )

    # 2) ProgressLog: add numeric_value and unit columns
    with op.batch_alter_table("progress_log", schema=None) as batch_op:
        batch_op.add_column(sa.Column("numeric_value", sa.Numeric(10, 2), nullable=True))
        batch_op.add_column(sa.Column("unit", sa.String(16), nullable=True))

    # 3) Subscription: add order_id FK
    with op.batch_alter_table("subscription", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("order_id", sa.Integer(), nullable=True)
        )
        batch_op.create_index(
            batch_op.f("ix_subscription_order_id"), ["order_id"], unique=False
        )
        batch_op.create_foreign_key(
            "fk_subscription_order_id",
            "order",
            ["order_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("subscription", schema=None) as batch_op:
        batch_op.drop_constraint("fk_subscription_order_id", type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_subscription_order_id"))
        batch_op.drop_column("order_id")

    with op.batch_alter_table("progress_log", schema=None) as batch_op:
        batch_op.drop_column("unit")
        batch_op.drop_column("numeric_value")

    with op.batch_alter_table("order_item", schema=None) as batch_op:
        batch_op.drop_constraint("fk_order_item_product_id", type_="foreignkey")
