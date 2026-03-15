"""Add consent and interaction result to chat_user_context.

Revision ID: 20260208_add_chat_consent_and_interaction_result
Revises: 20260127_add_plan_tables
Create Date: 2026-02-08 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260208_add_chat_consent_and_interaction_result"
down_revision = "20260127_add_plan_tables"
branch_labels = None
depends_on = None


def _has_column(inspector, table: str, column: str) -> bool:
    return column in {col["name"] for col in inspector.get_columns(table)}


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)

    if not insp.has_table("chat_user_context"):
        return

    if not _has_column(insp, "chat_user_context", "consent_given"):
        op.add_column(
            "chat_user_context",
            sa.Column("consent_given", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        )
    if not _has_column(insp, "chat_user_context", "consent_version"):
        op.add_column(
            "chat_user_context",
            sa.Column("consent_version", sa.String(length=32), nullable=True),
        )
    if not _has_column(insp, "chat_user_context", "consent_timestamp"):
        op.add_column(
            "chat_user_context",
            sa.Column("consent_timestamp", sa.DateTime(), nullable=True),
        )
    if not _has_column(insp, "chat_user_context", "consent_revoked_at"):
        op.add_column(
            "chat_user_context",
            sa.Column("consent_revoked_at", sa.DateTime(), nullable=True),
        )
    if not _has_column(insp, "chat_user_context", "last_interaction_result"):
        op.add_column(
            "chat_user_context",
            sa.Column("last_interaction_result", sa.String(length=32), nullable=True),
        )
    else:
        with op.batch_alter_table("chat_user_context") as batch_op:
            batch_op.alter_column(
                "last_interaction_result",
                existing_type=sa.String(length=16),
                type_=sa.String(length=32),
            )


def downgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)

    if not insp.has_table("chat_user_context"):
        return

    if _has_column(insp, "chat_user_context", "last_interaction_result"):
        op.drop_column("chat_user_context", "last_interaction_result")
    if _has_column(insp, "chat_user_context", "consent_revoked_at"):
        op.drop_column("chat_user_context", "consent_revoked_at")
    if _has_column(insp, "chat_user_context", "consent_timestamp"):
        op.drop_column("chat_user_context", "consent_timestamp")
    if _has_column(insp, "chat_user_context", "consent_version"):
        op.drop_column("chat_user_context", "consent_version")
    if _has_column(insp, "chat_user_context", "consent_given"):
        op.drop_column("chat_user_context", "consent_given")
