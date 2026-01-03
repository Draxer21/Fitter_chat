"""Add Google auth columns and username metadata.

Revision ID: 20251210_add_google_auth_columns
Revises: 20251201_add_dislikes_to_chat_user_context
Create Date: 2025-12-10 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251210_add_google_auth_columns"
down_revision = "20251201_add_dislikes_to_chat_user_context"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    if not insp.has_table("user"):
        return

    columns = {col["name"] for col in insp.get_columns("user")}

    if "auth_provider" not in columns:
        op.add_column(
            "user",
            sa.Column("auth_provider", sa.String(length=32), nullable=False, server_default="local"),
        )
        op.execute('UPDATE "user" SET auth_provider = \'local\' WHERE auth_provider IS NULL')
        columns.add("auth_provider")

    added_google_sub = False
    if "google_sub" not in columns:
        op.add_column("user", sa.Column("google_sub", sa.String(length=64), nullable=True))
        columns.add("google_sub")
        added_google_sub = True

    if "username_confirmed" not in columns:
        op.add_column(
            "user",
            sa.Column("username_confirmed", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        )
        op.execute('UPDATE "user" SET username_confirmed = true WHERE username_confirmed IS NULL')
        columns.add("username_confirmed")

    # Allow password_hash to be nullable for SSO accounts
    op.alter_column("user", "password_hash", existing_type=sa.String(length=255), nullable=True)

    # Ensure index/constraint on google_sub if column exists
    indexes = {idx["name"] for idx in insp.get_indexes("user")}
    if "ix_user_google_sub" not in indexes and ("google_sub" in columns or added_google_sub):
        try:
            op.create_index("ix_user_google_sub", "user", ["google_sub"], unique=True)
        except Exception:
            # Best-effort: ignore if index already exists with other name
            pass


def downgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    if not insp.has_table("user"):
        return

    indexes = {idx["name"] for idx in insp.get_indexes("user")}
    if "ix_user_google_sub" in indexes:
        op.drop_index("ix_user_google_sub", table_name="user")

    columns = {col["name"] for col in insp.get_columns("user")}
    if "google_sub" in columns:
        op.drop_column("user", "google_sub")
    if "auth_provider" in columns:
        op.drop_column("user", "auth_provider")
    if "username_confirmed" in columns:
        op.drop_column("user", "username_confirmed")

    op.alter_column("user", "password_hash", existing_type=sa.String(length=255), nullable=False)
