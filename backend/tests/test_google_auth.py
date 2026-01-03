import pytest

from backend.app import create_app
from backend.extensions import db
from backend.login.models import User


def _csrf_headers(client):
    resp = client.get("/auth/csrf-token")
    assert resp.status_code == 200
    token = resp.get_json().get("csrf_token")
    assert token
    return {"X-CSRF-Token": token}


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
    app = create_app()
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI="sqlite:///:memory:")
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _mock_google(monkeypatch, claims):
    monkeypatch.setattr("backend.login.routes._verify_google_credential", lambda token: claims)


def test_google_login_creates_placeholder_username(app, client, monkeypatch):
    app.config["GOOGLE_CLIENT_IDS"] = ["test-client"]
    claims = {
        "email": "google-user@example.com",
        "sub": "sub-123",
        "email_verified": True,
        "aud": "test-client",
        "name": "Google User",
    }
    _mock_google(monkeypatch, claims)

    resp = client.post("/auth/google", json={"credential": "test-token"}, headers=_csrf_headers(client))
    assert resp.status_code == 200, resp.get_data(as_text=True)
    payload = resp.get_json()
    assert payload["user"]["email"] == claims["email"]
    assert payload["user"]["auth_provider"] == "google"
    assert payload["user"]["needs_username"] is True
    assert payload["user"]["username"]

    with app.app_context():
        user = User.query.filter_by(email=claims["email"]).first()
        assert user is not None
        assert user.google_sub == claims["sub"]
        assert not user.username_confirmed


def test_google_login_rejects_taken_username(app, client, monkeypatch):
    app.config["GOOGLE_CLIENT_IDS"] = ["test-client"]
    with app.app_context():
        user = User.create(email="existing@example.com", username="taken_name", password="Secret123", full_name="Existing")
        db.session.commit()
        assert user.username == "taken_name"

    claims = {
        "email": "new-google@example.com",
        "sub": "sub-456",
        "email_verified": True,
        "aud": "test-client",
        "name": "New Google",
    }
    _mock_google(monkeypatch, claims)

    resp = client.post(
        "/auth/google",
        json={"credential": "other-token", "preferred_username": "taken_name"},
        headers=_csrf_headers(client),
    )
    assert resp.status_code == 409


def test_update_username_flow(app, client, monkeypatch):
    app.config["GOOGLE_CLIENT_IDS"] = ["test-client"]
    claims = {
        "email": "pending@example.com",
        "sub": "sub-789",
        "email_verified": True,
        "aud": "test-client",
        "name": "Pending User",
    }
    _mock_google(monkeypatch, claims)
    login_resp = client.post("/auth/google", json={"credential": "token"}, headers=_csrf_headers(client))
    assert login_resp.status_code == 200

    update_resp = client.put(
        "/auth/username",
        json={"username": "mi_apodo"},
        headers=_csrf_headers(client),
    )
    assert update_resp.status_code == 200, update_resp.get_data(as_text=True)
    data = update_resp.get_json()
    assert data["user"]["username"] == "mi_apodo"
    assert data["user"]["needs_username"] is False

    with app.app_context():
        user = User.query.filter_by(email=claims["email"]).first()
        assert user.username == "mi_apodo"
        assert user.username_confirmed is True
