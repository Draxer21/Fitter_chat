import os

import pyotp
import pytest

from backend.app import create_app
from backend.extensions import db
from backend.chat.models import ChatUserContext
from backend.login.models import User


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
    monkeypatch.setenv("CHAT_CONTEXT_API_KEY", "ctx-key")
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


def csrf_headers(client):
    resp = client.get("/auth/csrf-token")
    assert resp.status_code == 200
    token = resp.get_json().get("csrf_token")
    assert token
    return {"X-CSRF-Token": token}


def register_and_login(client):
    payload = {
        "full_name": "Perfil Test",
        "email": "profile@test.com",
        "username": "profile_user",
        "password": "Secret123",
    }
    resp = client.post("/auth/register", json=payload, headers=csrf_headers(client))
    assert resp.status_code == 201
    return payload


def test_profile_get_and_update(client, app):
    register_and_login(client)

    # GET inicial crea perfil vacío
    resp = client.get("/profile/me")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["profile"]["user_id"]

    # Actualiza datos
    update_payload = {
        "weight_kg": 82.5,
        "height_cm": 179,
        "primary_goal": "ganar_masa",
        "allergies": "lactosa",
        "medical_conditions": "asma",
        "experience_level": "intermedio",
        "somatotipo": "ectomorfo",
    }
    resp = client.put("/profile/me", json=update_payload)
    assert resp.status_code == 200
    profile = resp.get_json()["profile"]
    assert profile["weight_kg"] == 82.5
    assert profile["primary_goal"] == "ganar_masa"
    assert profile["experience_level"] == "intermedio"
    assert profile["somatotipo"] == "ectomorfo"
    assert profile["weight_bmi"] is not None

    # Comprueba sincronización con contexto de chat
    with app.app_context():
        ctx = ChatUserContext.get_or_create("sender-1", user_id=profile["user_id"])
        db.session.commit()
    resp = client.put("/profile/me", json={"allergies": "frutos secos"})
    assert resp.status_code == 200
    with app.app_context():
        ctx = ChatUserContext.query.filter_by(user_id=profile["user_id"]).first()
        assert ctx.allergies == "frutos secos"


def test_profile_lookup_with_api_key(client, app):
    register_and_login(client)
    client.put("/profile/me", json={"weight_kg": 70, "activity_level": "moderar"})

    client.post("/auth/logout", headers=csrf_headers(client))
    headers = {"X-Context-Key": "ctx-key"}
    resp = client.get("/profile/me", headers=headers, query_string={"user_id": 1})
    assert resp.status_code == 200
    profile = resp.get_json().get("profile")
    assert profile is not None
    assert profile["weight_kg"] == 70


def test_profile_update_with_api_key(client, app):
    register_and_login(client)
    with app.app_context():
        user = User.query.filter_by(username="profile_user").first()
        assert user is not None
        user_id = user.id

    client.post("/auth/logout", headers=csrf_headers(client))
    headers = {"X-Context-Key": "ctx-key"}
    payload = {"user_id": user_id, "weight_kg": 88.2, "medical_conditions": "asma leve"}
    resp = client.put("/profile/me", headers=headers, json=payload)
    assert resp.status_code == 200
    profile = resp.get_json().get("profile")
    assert profile["weight_kg"] == 88.2
    assert profile["medical_conditions"] == "asma leve"


def test_profile_requires_auth_without_key(client):
    register_and_login(client)
    client.post("/auth/logout", headers=csrf_headers(client))
    resp = client.get("/profile/me")
    assert resp.status_code == 401

