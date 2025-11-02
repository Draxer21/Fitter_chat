"""Herramientas de cifrado para la informacion sensible del perfil."""

from __future__ import annotations

import json
import os
import hashlib
from typing import Any, Dict

from cryptography.fernet import Fernet, InvalidToken
from flask import current_app


class ProfileCipherError(RuntimeError):
    """Error al cifrar o descifrar datos del perfil del usuario."""


def _load_cipher() -> Fernet:
    try:
        raw_key = (current_app.config.get("PROFILE_ENCRYPTION_KEY") or "").strip()
    except RuntimeError:
        raw_key = ""
    if not raw_key:
        raw_key = os.getenv("PROFILE_ENCRYPTION_KEY", "").strip()
    if not raw_key:
        raise ProfileCipherError(
            "PROFILE_ENCRYPTION_KEY no esta configurada. Genera una clave con 'python -c "
            "\"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"'"
        )
    key_bytes = raw_key.encode("utf-8")
    try:
        # Validamos que la clave tenga formato Fernet
        Fernet(key_bytes)
    except Exception as exc:  # pragma: no cover - validacion defensiva
        raise ProfileCipherError(
            "PROFILE_ENCRYPTION_KEY debe ser una cadena base64 urlsafe generada con Fernet"
        ) from exc
    return Fernet(key_bytes)


def encrypt_profile_payload(data: Dict[str, Any]) -> bytes:
    """Cifra el diccionario de datos sensibles del perfil."""

    cipher = _load_cipher()
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return cipher.encrypt(payload)


def decrypt_profile_payload(payload: bytes) -> Dict[str, Any]:
    """Descifra el payload almacenado para un perfil."""

    if not payload:
        return {}
    cipher = _load_cipher()
    try:
        decrypted = cipher.decrypt(payload)
    except InvalidToken as exc:
        raise ProfileCipherError("No se pudo descifrar el perfil almacenado") from exc
    return json.loads(decrypted.decode("utf-8"))


def profile_payload_checksum(payload: bytes) -> str:
    """Calcula un checksum para detectar corrupcion en el payload cifrado."""

    if not payload:
        return ""
    return hashlib.sha256(payload).hexdigest()
