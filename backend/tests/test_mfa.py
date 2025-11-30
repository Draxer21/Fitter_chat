import time

import pyotp
import pytest

from backend.app import create_app
from backend.extensions import db
from backend.login.models import User


def _get_csrf_token(client):
    resp = client.get("/auth/csrf-token")
    assert resp.status_code == 200, resp.get_data(as_text=True)
    data = resp.get_json() or {}
    token = data.get("csrf_token")
    assert token, "csrf token missing"
    return token


def post_with_csrf(client, path, json=None):
    token = _get_csrf_token(client)
    headers = {"X-CSRF-Token": token}
    return client.post(path, json=json, headers=headers)


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
    monkeypatch.setenv("CHAT_EMAIL_ROUTINE", "0")
    monkeypatch.setenv("RASA_BASE_URL", "http://localhost:5005")
    app = create_app()
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        WTF_CSRF_ENABLED=False,
    )
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _register_user(client, email="user@example.com", username="user", password="secret123"):
    payload = {
        "full_name": "Test User",
        "email": email,
        "username": username,
        "password": password,
    }
    resp = post_with_csrf(client, "/auth/register", json=payload)
    assert resp.status_code == 201, resp.get_data(as_text=True)
    return payload


def _setup_mfa(client):
    setup_resp = post_with_csrf(client, "/auth/mfa/setup")
    assert setup_resp.status_code == 200, setup_resp.get_data(as_text=True)
    data = setup_resp.get_json()
    secret = data.get("secret")
    assert secret, "La respuesta de setup debe entregar el secreto TOTP"
    return secret


def _confirm_mfa(client, totp):
    confirm_resp = post_with_csrf(client, "/auth/mfa/confirm", json={"code": totp.now()})
    assert confirm_resp.status_code == 200, confirm_resp.get_data(as_text=True)
    payload = confirm_resp.get_json()
    backup_codes = payload.get("backup_codes") or payload.get("recovery_codes")
    assert backup_codes and len(backup_codes) > 0
    return backup_codes


def test_login_with_totp_success(app, client):
    creds = _register_user(client)
    secret = _setup_mfa(client)
    totp = pyotp.TOTP(secret)
    _confirm_mfa(client, totp)

    # logout and force new login flow
    post_with_csrf(client, "/auth/logout")

    resp = post_with_csrf(client, "/auth/login", json={"username": creds["username"], "password": creds["password"]})
    assert resp.status_code == 401
    assert resp.get_json().get("mfa_required") is True

    # ensure new code window if confirm and login happened muy rápido
    time.sleep(0.5)
    code = totp.now()
    resp = post_with_csrf(client, "/auth/login", json={"username": creds["username"], "password": creds["password"], "totp": code})
    assert resp.status_code == 200, resp.get_data(as_text=True)
    data = resp.get_json()
    assert data["user"]["email"] == creds["email"]


def test_login_with_backup_code_consumes_once(app, client):
    creds = _register_user(client, email="backup@example.com", username="backup_user")
    secret = _setup_mfa(client)
    totp = pyotp.TOTP(secret)
    backup_codes = _confirm_mfa(client, totp)
    first_backup = backup_codes[0]

    post_with_csrf(client, "/auth/logout")

    resp = post_with_csrf(
        client,
        "/auth/login",
        json={
            "username": creds["username"],
            "password": creds["password"],
            "backup_code": first_backup,
        },
    )
    assert resp.status_code == 200, resp.get_data(as_text=True)

    post_with_csrf(client, "/auth/logout")

    # reuse should fail
    resp = post_with_csrf(
        client,
        "/auth/login",
        json={
            "username": creds["username"],
            "password": creds["password"],
            "backup_code": first_backup,
        },
    )
    assert resp.status_code == 401

    # totp still works
    time.sleep(0.5)
    resp = post_with_csrf(
        client,
        "/auth/login",
        json={
            "username": creds["username"],
            "password": creds["password"],
            "totp": pyotp.TOTP(secret).now(),
        },
    )
    assert resp.status_code == 200, resp.get_data(as_text=True)


def test_disable_mfa_requires_valid_code(app, client):
    creds = _register_user(client, email="disable@example.com", username="disable_user")
    secret = _setup_mfa(client)
    totp = pyotp.TOTP(secret)
    _confirm_mfa(client, totp)

    # invalid code
    resp = post_with_csrf(client, "/auth/mfa/disable", json={"code": "000000"})
    assert resp.status_code == 401

    time.sleep(0.5)
    valid_code = totp.now()
    resp = post_with_csrf(client, "/auth/mfa/disable", json={"code": valid_code})
    assert resp.status_code == 200, resp.get_data(as_text=True)

    status = client.get("/auth/mfa/status")
    assert status.status_code == 200
    assert status.get_json().get("enabled") is False

    post_with_csrf(client, "/auth/logout")
    resp = post_with_csrf(client, "/auth/login", json={"username": creds["username"], "password": creds["password"]})
    assert resp.status_code == 200, resp.get_data(as_text=True)

