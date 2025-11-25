"""Add encrypted payload to user_profile and migrate data.

Revision ID: 20251128_encrypt_user_profile_payload
Revises: 20251007_add_username_to_user
Create Date: 2025-11-28 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm

# revision identifiers, used by Alembic.
revision = "20251128_encrypt_user_profile_payload"
down_revision = "20251007_add_username_to_user"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user_profile", sa.Column("encrypted_payload", sa.LargeBinary(), nullable=True))
    op.add_column("user_profile", sa.Column("payload_checksum", sa.String(length=64), nullable=True))

    bind = op.get_bind()
    session = orm.Session(bind=bind)

    try:
        from backend.profile.models import UserProfile
        from backend.security.profile_crypto import (
            encrypt_profile_payload,
            profile_payload_checksum,
        )

        profiles = session.query(UserProfile).all()
        for profile in profiles:
            payload = {
                "weight_kg": profile.weight_kg,
                "height_cm": profile.height_cm,
                "age_years": profile.age_years,
                "sex": profile.sex,
                "activity_level": profile.activity_level,
                "primary_goal": profile.primary_goal,
                "allergies": profile.allergies,
                "medical_conditions": profile.medical_conditions,
                "notes": profile.notes,
                "body_fat_percent": None,
                "fitness_goal": None,
                "dietary_preferences": None,
                "additional_notes": None,
            }
            blob = encrypt_profile_payload(payload)
            profile.encrypted_payload = blob
            profile.payload_checksum = profile_payload_checksum(blob)

            # limpiamos columnas en texto plano para evitar duplicados
            profile.weight_kg = None
            profile.height_cm = None
            profile.age_years = None
            profile.sex = None
            profile.activity_level = None
            profile.primary_goal = None
            profile.allergies = None
            profile.medical_conditions = None
            profile.notes = None

        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def downgrade() -> None:
    # No se puede recuperar texto plano una vez cifrado; solo eliminamos columnas nuevas.
    op.drop_column("user_profile", "payload_checksum")
    op.drop_column("user_profile", "encrypted_payload")
