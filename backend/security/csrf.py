import hmac
import secrets
from typing import Mapping, Optional

from flask import Response, current_app, request, session

CSRF_SESSION_KEY = "_csrf_token"
CSRF_COOKIE_NAME = "XSRF-TOKEN"
CSRF_HEADER_NAMES = ("X-CSRF-Token", "X-XSRF-TOKEN")


def get_or_create_csrf_token() -> str:
    token = session.get(CSRF_SESSION_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        session[CSRF_SESSION_KEY] = token
    return token


def set_csrf_cookie(response: Response) -> Response:
    token = get_or_create_csrf_token()
    secure = bool(current_app.config.get("SESSION_COOKIE_SECURE"))
    same_site = current_app.config.get("SESSION_COOKIE_SAMESITE") or "Lax"
    response.set_cookie(
        CSRF_COOKIE_NAME,
        token,
        httponly=False,
        secure=secure,
        samesite=same_site,
        path="/",
    )
    return response


def _extract_provided_token(headers: Optional[Mapping[str, str]] = None) -> Optional[str]:
    headers = headers or request.headers
    for header in CSRF_HEADER_NAMES:
        value = headers.get(header)
        if value:
            trimmed = value.strip()
            if trimmed:
                return trimmed
    cookie_val = request.cookies.get(CSRF_COOKIE_NAME)
    if cookie_val:
        trimmed = cookie_val.strip()
        if trimmed:
            return trimmed
    return None


def validate_csrf(headers: Optional[Mapping[str, str]] = None) -> bool:
    expected = session.get(CSRF_SESSION_KEY)
    if not expected:
        return False
    provided = _extract_provided_token(headers=headers)
    if not provided:
        return False
    try:
        return hmac.compare_digest(provided, expected)
    except Exception:
        return False


def clear_csrf_token() -> None:
    session.pop(CSRF_SESSION_KEY, None)
