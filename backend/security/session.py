"""Helpers reutilizables para autenticación basada en cabeceras y sesión."""

from typing import Mapping, MutableMapping, Optional, Any


def context_api_key_valid(
    headers: Mapping[str, str],
    expected_key: str,
) -> bool:
    """Valida encabezados contra una API key esperada."""
    expected = (expected_key or "").strip()
    if not expected:
        return False
    provided = (
        headers.get("X-Context-Key")
        or headers.get("X-Api-Key")
        or headers.get("Authorization")
        or ""
    ).strip()
    if provided.lower().startswith("bearer "):
        provided = provided.split(" ", 1)[1].strip()
    return provided == expected


def session_uid(flask_session: MutableMapping[str, Any]) -> Optional[int]:
    """Obtiene el uid almacenado en sesión, convirtiéndolo a int si aplica."""
    try:
        uid = flask_session.get("uid")
    except Exception:
        return None
    try:
        return int(uid) if uid is not None else None
    except (TypeError, ValueError):
        return None
