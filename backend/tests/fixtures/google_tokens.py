from datetime import datetime, timedelta, timezone

import jwt

CLIENT_ID = "test-client-id.apps.googleusercontent.com"
INVALID_CLIENT_ID = "other-client.apps.googleusercontent.com"

_NOW = datetime(2024, 1, 1, tzinfo=timezone.utc)
_EXP = _NOW + timedelta(days=3650)

VALID_PAYLOAD = {
    "aud": CLIENT_ID,
    "iss": "https://accounts.google.com",
    "sub": "test-subject",
    "email": "google-user@example.com",
    "email_verified": True,
    "name": "Google User",
    "exp": int(_EXP.timestamp()),
}

INVALID_AUD_PAYLOAD = {
    **VALID_PAYLOAD,
    "aud": INVALID_CLIENT_ID,
}

VALID_TOKEN = jwt.encode(VALID_PAYLOAD, key=None, algorithm="none")
INVALID_AUD_TOKEN = jwt.encode(INVALID_AUD_PAYLOAD, key=None, algorithm="none")
