"""secure profile storage"""

from datetime import datetime
import json
import hashlib
import os

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
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


def _create_profile_table():
    op.create_table(
        "user_profile",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False, unique=True),
        sa.Column("encrypted_payload", sa.LargeBinary(), nullable=False),
        sa.Column("payload_checksum", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column("updated_at", sa.DateTime(), nullable=False, default=datetime.utcnow),
    )


def _build_legacy_select(columns: set) -> str:
    # Usa NULL con cast cuando la columna no existe en el esquema legacy.
    def _expr(name: str, sql_type: str) -> str:
        if name in columns:
            return f'"{name}"'
        return f"NULL::{sql_type} AS \"{name}\""

    parts = [
        _expr("weight_kg", "double precision"),
        _expr("height_cm", "double precision"),
        _expr("body_fat_percent", "double precision"),
        _expr("fitness_goal", "varchar"),
        _expr("dietary_preferences", "varchar"),
        _expr("health_conditions", "jsonb"),
        _expr("additional_notes", "text"),
        _expr("created_at", "timestamp"),
        _expr("updated_at", "timestamp"),
    ]
    return "SELECT user_id, " + ", ".join(parts) + " FROM user_profile"


def upgrade() -> None:
    bind = op.get_bind()
    cipher = _load_cipher()
    insp = inspect(bind)
    has_table = "user_profile" in insp.get_table_names()
    columns = set()
    if has_table:
        columns = {col["name"] for col in insp.get_columns("user_profile")}

    # Extrae filas legadas si existe tabla sin cifrado.
    legacy_rows = []
    if has_table and "encrypted_payload" not in columns:
        legacy_rows = list(
            bind.execute(
                sa.text(_build_legacy_select(columns))
            ).mappings()
        )
        op.drop_table("user_profile")
        has_table = False

    if not has_table:
        _create_profile_table()

    # Determina fuente de datos para payloads.
    now = datetime.utcnow()
    if legacy_rows:
        source_rows = legacy_rows
    elif not columns or "encrypted_payload" not in columns:
        source_rows = bind.execute(
            sa.text(
                "SELECT id as user_id, weight_kg, height_cm, body_fat_percent, fitness_goal, dietary_preferences, "
                "health_conditions, additional_notes, NULL::timestamp as created_at, NULL::timestamp as updated_at "
                "FROM \"user\""
            )
        ).mappings()
    else:
        source_rows = []

    for row in source_rows:
        profile = {
            "weight_kg": row.get("weight_kg"),
            "height_cm": row.get("height_cm"),
            "body_fat_percent": row.get("body_fat_percent"),
            "fitness_goal": row.get("fitness_goal"),
            "dietary_preferences": row.get("dietary_preferences"),
            "health_conditions": row.get("health_conditions") or [],
            "additional_notes": row.get("additional_notes"),
            "last_updated_at": (row.get("updated_at") or now).isoformat(),
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
                "user_id": row["user_id"],
                "payload": encrypted,
                "checksum": checksum,
                "created_at": row.get("created_at") or now,
                "updated_at": row.get("updated_at") or now,
            },
        )

    # Limpia columnas de perfil en la tabla user si existen.
    user_columns = {col["name"] for col in insp.get_columns("user")}
    with op.batch_alter_table("user", schema=None) as batch_op:
        for column in reversed(PROFILE_FIELDS):
            if column in user_columns:
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
