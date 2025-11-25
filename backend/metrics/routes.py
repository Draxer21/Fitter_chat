from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from . import metrics

bp = Blueprint("metrics", __name__, url_prefix="/metrics")


def _authorized() -> bool:
    expected = (current_app.config.get("METRICS_API_KEY") or "").strip()
    if not expected:
        return False
    provided = (
        request.headers.get("X-Api-Key")
        or request.headers.get("Authorization")
        or request.headers.get("X-Metrics-Key")
        or ""
    ).strip()
    if provided.lower().startswith("bearer "):
        provided = provided.split(" ", 1)[1].strip()
    return provided == expected


@bp.get("/summary")
def summary():
    if not _authorized():
        return jsonify({"error": "No autorizado"}), 401
    return jsonify(metrics.snapshot()), 200
