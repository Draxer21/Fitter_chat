"""Utilidades de retencion y purga de datos sensibles."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Optional

from flask import Flask

from ..chat.models import ChatUserContext
from ..login.models import User
from ..profile.models import UserProfile


def purge_stale_data(app: Flask, db, *, retention_days: Optional[int] = None, dry_run: bool = False) -> Dict[str, int]:
    """Elimina o anonimiza datos luego del periodo de retencion."""

    days = int(retention_days or app.config.get("DATA_RETENTION_DAYS", 730))
    cutoff = datetime.utcnow() - timedelta(days=days)
    logger = getattr(app, "logger", None)

    # Purga contextos de chat inactivos
    stale_ctx_q = ChatUserContext.query.filter(ChatUserContext.last_interaction_at < cutoff)
    stale_ctx_count = stale_ctx_q.count()
    if not dry_run and stale_ctx_count:
        stale_ctx_q.delete(synchronize_session=False)

    # Anonimiza perfiles sin actividad reciente (no admins)
    profiles_q = (
        UserProfile.query.join(User, UserProfile.user_id == User.id)
        .filter(User.is_admin.is_(False))
        .filter(UserProfile.updated_at < cutoff)
    )
    stale_profiles = profiles_q.all()
    anonymized_profiles = 0
    if stale_profiles and not dry_run:
        for profile in stale_profiles:
            profile.encrypted_payload = None
            profile.payload_checksum = None
            profile.updated_at = datetime.utcnow()
            anonymized_profiles += 1
    else:
        anonymized_profiles = len(stale_profiles)

    if not dry_run:
        db.session.commit()

    if logger:
        logger.info(
            "Retencion ejecutada (days=%s, dry_run=%s): chat_context purgados=%s, perfiles_anonimizados=%s",
            days,
            dry_run,
            stale_ctx_count,
            anonymized_profiles,
        )

    return {
        "retention_days": days,
        "chat_contexts_deleted": stale_ctx_count,
        "profiles_anonymized": anonymized_profiles,
        "dry_run": dry_run,
    }
