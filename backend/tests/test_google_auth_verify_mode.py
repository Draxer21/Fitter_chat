import pytest

from backend.app import create_app
from backend.extensions import db
from backend.tests.fixtures.google_tokens import CLIENT_ID, INVALID_AUD_TOKEN, VALID_TOKEN


def _csrf_headers(client):
    resp = client.get("/auth/csrf-token")
    assert resp.status_code == 200
    token = resp.get_json().get("csrf_token")
    assert token
    return {"X-CSRF-Token": token}


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
    monkeypatch.setenv("GOOGLE_AUTH_VERIFY_MODE", "mock")
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


def test_no_client_ids_returns_503(app, client):
    app.config["GOOGLE_CLIENT_IDS"] = []
    resp = client.post("/auth/google", json={"credential": VALID_TOKEN}, headers=_csrf_headers(client))
    assert resp.status_code == 503


def test_valid_aud_returns_success(app, client):
    app.config["GOOGLE_CLIENT_IDS"] = [CLIENT_ID]
    resp = client.post("/auth/google", json={"credential": VALID_TOKEN}, headers=_csrf_headers(client))
    assert resp.status_code == 200, resp.get_data(as_text=True)


def test_invalid_aud_returns_401(app, client):
    app.config["GOOGLE_CLIENT_IDS"] = [CLIENT_ID]
    resp = client.post("/auth/google", json={"credential": INVALID_AUD_TOKEN}, headers=_csrf_headers(client))
    assert resp.status_code == 401
