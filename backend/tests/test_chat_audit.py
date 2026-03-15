import requests

import pytest

from backend.app import create_app
from backend.chat.service import ChatService
from backend.extensions import db


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
    monkeypatch.setenv("NLU_FALLBACK_THRESHOLD", "0.25")
    app = create_app()
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI="sqlite:///:memory:")
    return app


def _service(app):
    return ChatService(app, db, requests.Session())


def test_classify_fallback_by_intent(app):
    service = _service(app)
    result, is_fallback, is_handoff, reason, threshold = service._classify_interaction_result(
        "nlu_fallback", 0.9, [], []
    )
    assert result == "fallback"
    assert is_fallback is True
    assert is_handoff is False
    assert reason is None
    assert threshold == 0.25


def test_classify_fallback_by_confidence(app):
    service = _service(app)
    result, is_fallback, is_handoff, reason, threshold = service._classify_interaction_result(
        "saludar", 0.1, [], []
    )
    assert result == "fallback"
    assert is_fallback is True
    assert is_handoff is False
    assert reason is None
    assert threshold == 0.25


def test_classify_handoff_by_intent(app):
    service = _service(app)
    result, is_fallback, is_handoff, reason, threshold = service._classify_interaction_result(
        "handoff_human", 0.9, [], []
    )
    assert result == "handoff"
    assert is_handoff is True
    assert reason == "intent:handoff_human"
    assert threshold == 0.25


def test_classify_handoff_by_payload(app):
    service = _service(app)
    payload = [{"custom": {"handoff": True, "handoff_reason": "dolor_agudo"}}]
    result, is_fallback, is_handoff, reason, threshold = service._classify_interaction_result(
        "informar", 0.9, [], payload
    )
    assert result == "handoff"
    assert is_handoff is True
    assert reason == "payload:otro"
    assert threshold == 0.25


def test_classify_handoff_by_payload_valid_reason(app):
    service = _service(app)
    payload = [{"custom": {"handoff": True, "handoff_reason": "asesor"}}]
    result, is_fallback, is_handoff, reason, threshold = service._classify_interaction_result(
        "informar", 0.9, [], payload
    )
    assert result == "handoff"
    assert is_handoff is True
    assert reason == "payload:asesor"
    assert threshold == 0.25


def test_payload_handoff_overrides_fallback(app):
    service = _service(app)
    payload = [{"custom": {"handoff": True, "handoff_reason": "asesor"}}]
    result, is_fallback, is_handoff, reason, threshold = service._classify_interaction_result(
        "saludar", 0.1, [], payload
    )
    assert result == "handoff"
    assert is_handoff is True
    assert reason == "payload:asesor"
    assert threshold == 0.25


def test_classify_success(app):
    service = _service(app)
    result, is_fallback, is_handoff, reason, threshold = service._classify_interaction_result(
        "saludar", 0.9, [], []
    )
    assert result == "success"
    assert is_fallback is False
    assert is_handoff is False
    assert reason is None
    assert threshold == 0.25
