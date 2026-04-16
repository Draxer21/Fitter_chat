"""
Tests de autenticacion y seguridad (RF1).
Verifica registro, login, validacion de credenciales, CSRF y MFA/TOTP.
"""
import pytest
import pyotp

from backend.app import create_app
from backend.extensions import db
from backend.login.models import User


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


def _csrf(client):
    resp = client.get("/auth/csrf-token")
    assert resp.status_code == 200
    return resp.get_json()["csrf_token"]


def _post_csrf(client, path, payload):
    token = _csrf(client)
    return client.post(path, json=payload, headers={"X-CSRF-Token": token})


def _register(client, email="user@fitter.cl", username="testuser", password="SecurePass123"):
    return _post_csrf(client, "/auth/register", {
        "full_name": "Test User",
        "email": email,
        "username": username,
        "password": password,
    })


# =========================================================
# Modelo User (logica de passwords, TOTP, backup codes)
# =========================================================
class TestUserModel:
    """Verificar el modelo User y manejo de passwords."""

    def test_create_user(self, app):
        with app.app_context():
            user = User.create(
                email="create@fitter.cl",
                username="createuser",
                password="SecurePass123!",
                full_name="Create User",
            )
            db.session.commit()
            assert user.id is not None
            assert user.email == "create@fitter.cl"

    def test_password_hashed(self, app):
        with app.app_context():
            user = User.create(
                email="hash@fitter.cl",
                username="hashuser",
                password="MyPassword1",
                full_name="Hash Test",
            )
            db.session.commit()
            assert user.password_hash != "MyPassword1"
            assert user.check_password("MyPassword1") is True
            assert user.check_password("wrong") is False

    def test_empty_password_rejected(self, app):
        with app.app_context():
            with pytest.raises(ValueError):
                User.create(
                    email="empty@fitter.cl",
                    username="emptypass",
                    password="",
                    full_name="Empty Pass",
                )

    def test_duplicate_email_rejected(self, app):
        from sqlalchemy.exc import IntegrityError
        with app.app_context():
            User.create(email="dup@fitter.cl", username="dup1", password="Pass1234", full_name="Dup1")
            db.session.commit()
            User.create(email="dup@fitter.cl", username="dup2", password="Pass1234", full_name="Dup2")
            with pytest.raises(IntegrityError):
                db.session.commit()
            db.session.rollback()

    def test_to_dict_excludes_password(self, app):
        with app.app_context():
            user = User.create(
                email="dict@fitter.cl",
                username="dictuser",
                password="Pass1234",
                full_name="Dict Test",
            )
            db.session.commit()
            d = user.to_dict(include_profile=False)
            assert d["email"] == "dict@fitter.cl"
            assert "password" not in d
            assert "password_hash" not in d


# =========================================================
# MFA / TOTP
# =========================================================
class TestTOTP:
    """Verificar funcionalidad MFA/TOTP."""

    def test_totp_setup_and_verify(self, app):
        with app.app_context():
            user = User.create(
                email="totp@fitter.cl", username="totpuser",
                password="Pass1234", full_name="TOTP Test",
            )
            db.session.commit()
            secret = user.reset_totp_secret()
            assert secret is not None
            code = pyotp.TOTP(secret).now()
            assert user.verify_totp_token(code) is True

    def test_invalid_totp_rejected(self, app):
        with app.app_context():
            user = User.create(
                email="badtotp@fitter.cl", username="badtotpuser",
                password="Pass1234", full_name="Bad TOTP",
            )
            db.session.commit()
            user.reset_totp_secret()
            assert user.verify_totp_token("000000") is False

    def test_backup_codes_single_use(self, app):
        with app.app_context():
            user = User.create(
                email="backup@fitter.cl", username="backupuser",
                password="Pass1234", full_name="Backup Test",
            )
            db.session.commit()
            codes = user.generate_backup_codes(count=3)
            assert len(codes) == 3
            assert user.consume_backup_code(codes[0]) is True
            # no se puede consumir dos veces
            assert user.consume_backup_code(codes[0]) is False


# =========================================================
# Endpoint de login
# =========================================================
class TestLoginEndpoint:
    """Verificar endpoint POST /auth/login."""

    def test_login_success(self, client):
        assert _register(client).status_code == 201
        resp = _post_csrf(client, "/auth/login", {
            "username": "testuser",
            "password": "SecurePass123",
        })
        assert resp.status_code == 200
        assert resp.get_json().get("ok") is True

    def test_login_wrong_password(self, client):
        _register(client)
        resp = _post_csrf(client, "/auth/login", {
            "username": "testuser",
            "password": "WrongPassword",
        })
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client):
        resp = _post_csrf(client, "/auth/login", {
            "username": "noexiste",
            "password": "whatever",
        })
        assert resp.status_code == 401

    def test_login_empty_credentials(self, client):
        resp = _post_csrf(client, "/auth/login", {"username": "", "password": ""})
        assert resp.status_code == 401

    def test_login_by_email(self, client):
        _register(client, email="email@fitter.cl", username="emailuser")
        resp = _post_csrf(client, "/auth/login", {
            "username": "email@fitter.cl",
            "password": "SecurePass123",
        })
        assert resp.status_code == 200


# =========================================================
# Endpoint de registro
# =========================================================
class TestRegisterEndpoint:
    """Verificar endpoint POST /auth/register."""

    def test_register_success(self, client):
        resp = _register(client, email="nuevo@fitter.cl", username="nuevousr")
        assert resp.status_code == 201
        assert resp.get_json().get("ok") is True

    def test_register_missing_fields(self, client):
        resp = _post_csrf(client, "/auth/register", {"email": "inc@fitter.cl"})
        assert resp.status_code == 400

    def test_register_duplicate_email(self, client):
        _register(client, email="dup@fitter.cl", username="dupuser1")
        resp = _register(client, email="dup@fitter.cl", username="dupuser2")
        assert resp.status_code == 409


# =========================================================
# CSRF
# =========================================================
class TestCSRF:
    """Verificar proteccion CSRF."""

    def test_csrf_token_endpoint(self, client):
        resp = client.get("/auth/csrf-token")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "csrf_token" in data
        assert len(data["csrf_token"]) > 0
