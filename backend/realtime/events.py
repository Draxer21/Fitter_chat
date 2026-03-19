# backend/realtime/events.py
"""
Flask-SocketIO event handlers and realtime notification helpers.

This module is a no-op when flask-socketio is not installed (socketio is None).
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from ..extensions import socketio

logger = logging.getLogger(__name__)


def notify_user(uid: Any, event: str, data: Dict[str, Any]) -> None:
    """Emit *event* with *data* to the private room of a single user.

    Safe to call even when socketio is None (graceful no-op).
    """
    if socketio is None:
        return
    try:
        socketio.emit(event, data, room=f"user_{uid}")
    except Exception:
        logger.exception("notify_user: failed to emit '%s' to user %s", event, uid)


def notify_admins(event: str, data: Dict[str, Any]) -> None:
    """Emit *event* with *data* to all connected admin sockets.

    Safe to call even when socketio is None (graceful no-op).
    """
    if socketio is None:
        return
    try:
        socketio.emit(event, data, room="admins")
    except Exception:
        logger.exception("notify_admins: failed to emit '%s' to admins room", event)


def init_realtime(app: Any) -> None:  # noqa: ANN001
    """Register SocketIO event handlers on *app*.

    Does nothing when socketio is None so the application works without
    flask-socketio installed.
    """
    if socketio is None:
        app.logger.info("realtime: flask-socketio not available, skipping event registration.")
        return

    @socketio.on("connect")
    def on_connect() -> None:  # type: ignore[misc]
        from flask import request as _req  # local import to avoid circular issues at module load
        from flask import session as _session

        uid = _session.get("uid")
        if not uid:
            logger.warning("realtime: unauthenticated connect from %s — disconnecting", _req.sid)
            return False  # returning False disconnects the client

        try:
            from flask_socketio import join_room
            join_room(f"user_{uid}")
            logger.info("realtime: user %s connected and joined room user_%s", uid, uid)
        except Exception:
            logger.exception("realtime: on_connect failed for uid=%s", uid)

    @socketio.on("disconnect")
    def on_disconnect() -> None:  # type: ignore[misc]
        from flask import session as _session

        uid = _session.get("uid", "<unknown>")
        logger.info("realtime: user %s disconnected", uid)

    @socketio.on("join_admin")
    def on_join_admin() -> None:  # type: ignore[misc]
        from flask import session as _session

        uid = _session.get("uid")
        if not uid:
            logger.warning("realtime: join_admin called without uid — ignoring")
            return

        try:
            from ..extensions import db
            from ..login.models import User

            user = db.session.get(User, uid)
            if user and user.is_admin:
                from flask_socketio import join_room
                join_room("admins")
                logger.info("realtime: admin user %s joined admins room", uid)
            else:
                logger.warning(
                    "realtime: join_admin denied for uid=%s (not admin or not found)", uid
                )
        except Exception:
            logger.exception("realtime: on_join_admin failed for uid=%s", uid)

    app.logger.info("realtime: SocketIO event handlers registered.")
