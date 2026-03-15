import pytest

from backend.app import create_app
from backend.extensions import db
from backend.chat.models import ChatUserContext


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
    monkeypatch.setenv("CHAT_CONTEXT_API_KEY", "ctx-key")
    monkeypatch.setenv("CONSENT_VERSION", "2025-11-22")
    app = create_app()
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False, SQLALCHEMY_DATABASE_URI="sqlite:///:memory:")
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_chat_send_blocked_without_consent(client, app):
    resp = client.post("/chat/send", json={"sender": "u1", "message": "hola"})
    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["ok"] is False
    assert payload["error"] == "consent_required"
    assert payload["consent_version"] == "2025-11-22"

    with app.app_context():
        ctx = ChatUserContext.query.filter_by(sender_id="u1").one()
        assert ctx.consent_given is False
        assert ctx.last_interaction_result == "blocked_no_consent"
        history = ctx.history or []
        assert history
        last_entry = history[-1]
        assert last_entry.get("result") == "blocked_no_consent"
        assert last_entry.get("text") is None


def test_consent_grant_and_revoke(client, app):
    headers = {"X-Context-Key": "ctx-key"}

    resp = client.post("/chat/context/u2", headers=headers, json={"consent_given": True})
    assert resp.status_code == 200
    ctx_payload = resp.get_json()["context"]
    assert ctx_payload["consent_given"] is True
    assert ctx_payload["consent_version"] == "2025-11-22"
    assert ctx_payload["consent_timestamp"] is not None

    revoke = client.post("/chat/consent/revoke/u2", headers=headers, json={})
    assert revoke.status_code == 200
    data = revoke.get_json()
    assert data["ok"] is True
    assert data["consent_given"] is False
    assert data["consent_revoked_at"] is not None

    check = client.get("/chat/context/u2", headers=headers)
    assert check.status_code == 200
    ctx = check.get_json()["context"]
    assert ctx["consent_given"] is False
    assert ctx["consent_revoked_at"] is not None
