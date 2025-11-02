"""secure profile storage"""

from datetime import datetime
import json
import hashlib
import os

from alembic import op
import sqlalchemy as sa
from cryptography.fernet import Fernet, InvalidToken

# revision identifiers, used by Alembic.
revision = "4a2e6b28f5da"
down_revision = "c6f1d3b8e3a4"
branch_labels = None
depends_on = None


PROFILE_FIELDS = (
    "weight_kg",
    "height_cm",
    "body_fat_percent",
    "fitness_goal",
    "dietary_preferences",
    "health_conditions",
    "additional_notes",
)


def _load_cipher() -> Fernet:
    key = os.getenv("PROFILE_ENCRYPTION_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "PROFILE_ENCRYPTION_KEY debe establecerse antes de ejecutar la migracion para proteger los datos"
        )
    try:
        return Fernet(key.encode("utf-8"))
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("PROFILE_ENCRYPTION_KEY no tiene un formato valido de Fernet") from exc


def _encrypt_payload(cipher: Fernet, data: dict) -> bytes:
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return cipher.encrypt(payload)


def _decrypt_payload(cipher: Fernet, payload: bytes) -> dict:
    try:
        decrypted = cipher.decrypt(payload)
    except InvalidToken as exc:  # pragma: no cover
        raise RuntimeError("No se pudo descifrar el perfil almacenado durante el downgrade") from exc
    return json.loads(decrypted.decode("utf-8"))


def upgrade() -> None:
    bind = op.get_bind()
    cipher = _load_cipher()

    op.create_table(
        "user_profile",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False, unique=True),
        sa.Column("encrypted_payload", sa.LargeBinary(), nullable=False),
        sa.Column("payload_checksum", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column("updated_at", sa.DateTime(), nullable=False, default=datetime.utcnow),
    )

    result = bind.execute(
        sa.text(
            "SELECT id, weight_kg, height_cm, body_fat_percent, fitness_goal, dietary_preferences, "
            "health_conditions, additional_notes FROM \"user\""
        )
    )
    now = datetime.utcnow()

    for row in result.mappings():
        profile = {
            "weight_kg": row["weight_kg"],
            "height_cm": row["height_cm"],
            "body_fat_percent": row["body_fat_percent"],
            "fitness_goal": row["fitness_goal"],
            "dietary_preferences": row["dietary_preferences"],
            "health_conditions": row["health_conditions"] or [],
            "additional_notes": row["additional_notes"],
            "last_updated_at": now.isoformat(),
        }
        normalized = {k: v for k, v in profile.items() if v not in (None, [], "")}
        if not normalized:
            continue
        encrypted = _encrypt_payload(cipher, profile)
        checksum = hashlib.sha256(encrypted).hexdigest()
        bind.execute(
            sa.text(
                "INSERT INTO user_profile (user_id, encrypted_payload, payload_checksum, created_at, updated_at) "
                "VALUES (:user_id, :payload, :checksum, :created_at, :updated_at)"
            ),
            {
                "user_id": row["id"],
                "payload": encrypted,
                "checksum": checksum,
                "created_at": now,
                "updated_at": now,
            },
        )

    with op.batch_alter_table("user", schema=None) as batch_op:
        for column in reversed(PROFILE_FIELDS):
            batch_op.drop_column(column)


def downgrade() -> None:
    bind = op.get_bind()
    cipher = _load_cipher()

    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(sa.Column("additional_notes", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("health_conditions", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("dietary_preferences", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("fitness_goal", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("body_fat_percent", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("height_cm", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("weight_kg", sa.Float(), nullable=True))

    result = bind.execute(sa.text("SELECT user_id, encrypted_payload FROM user_profile"))
    for row in result.mappings():
        payload = _decrypt_payload(cipher, row["encrypted_payload"])
        update_values = {
            "weight_kg": payload.get("weight_kg"),
            "height_cm": payload.get("height_cm"),
            "body_fat_percent": payload.get("body_fat_percent"),
            "fitness_goal": payload.get("fitness_goal"),
            "dietary_preferences": payload.get("dietary_preferences"),
            "health_conditions": payload.get("health_conditions"),
            "additional_notes": payload.get("additional_notes"),
        }
        bind.execute(
            sa.text(
                "UPDATE \"user\" SET weight_kg=:weight_kg, height_cm=:height_cm, body_fat_percent=:body_fat_percent, "
                "fitness_goal=:fitness_goal, dietary_preferences=:dietary_preferences, "
                "health_conditions=:health_conditions, additional_notes=:additional_notes WHERE id=:user_id"
            ),
            {**update_values, "user_id": row["user_id"]},
        )

    op.drop_table("user_profile")
