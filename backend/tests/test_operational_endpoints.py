import pytest

from backend.app import create_app
from backend.chat.service import ServiceResponse
from backend.extensions import db


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
    monkeypatch.setenv("METRICS_WINDOW_SIZE", "10")
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


def test_health_returns_operational_payload(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["ok"] is True
    assert payload["service"]
    assert payload["ts"]


def test_ready_returns_db_unavailable(client, app, monkeypatch):
    monkeypatch.setattr(app.chat_service, "check_database_ready", lambda: False)
    monkeypatch.setattr(app.chat_service, "check_rasa_ready", lambda: True)

    resp = client.get("/ready")
    assert resp.status_code == 503
    payload = resp.get_json()
    assert payload == {"ok": False, "reason": "db_unavailable"}


def test_ready_returns_rasa_unavailable(client, app, monkeypatch):
    monkeypatch.setattr(app.chat_service, "check_database_ready", lambda: True)
    monkeypatch.setattr(app.chat_service, "check_rasa_ready", lambda: False)

    resp = client.get("/ready")
    assert resp.status_code == 503
    payload = resp.get_json()
    assert payload == {"ok": False, "reason": "rasa_unavailable"}


def test_ready_returns_ok_when_dependencies_are_available(client, app, monkeypatch):
    monkeypatch.setattr(app.chat_service, "check_database_ready", lambda: True)
    monkeypatch.setattr(app.chat_service, "check_rasa_ready", lambda: True)

    resp = client.get("/ready")
    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["ok"] is True
    assert payload["service"]


def test_metrics_reports_rates_and_no_text(client, app, monkeypatch):
    responses = [
        ServiceResponse([{"text": "fallback"}], 200, "fallback"),
        ServiceResponse({"ok": False, "error": "consent_required"}, 200, "blocked_no_consent"),
        ServiceResponse([{"text": "ok"}], 200, "success"),
    ]
    perf_values = iter([0.0, 0.1, 0.2, 0.25, 0.3, 0.5])

    def fake_send_message(_data, _headers, _session):
        return responses.pop(0)

    monkeypatch.setattr(app.chat_service, "send_message", fake_send_message)
    monkeypatch.setattr("backend.app.time.perf_counter", lambda: next(perf_values))

    assert client.post("/chat/send", json={"sender": "u1", "message": "hola"}).status_code == 200
    assert client.post("/chat/send", json={"sender": "u1", "message": "hola"}).status_code == 200
    assert client.post("/chat/send", json={"sender": "u1", "message": "hola"}).status_code == 200

    resp = client.get("/metrics")
    assert resp.status_code == 200
    payload = resp.get_json()

    assert payload["window_size"] == 3
    assert payload["count_2xx"] == 3
    assert payload["count_4xx"] == 0
    assert payload["count_5xx"] == 0
    assert payload["fallback_rate"] == pytest.approx(0.3333, rel=0, abs=1e-4)
    assert payload["handoff_rate"] == 0.0
    assert payload["blocked_rate"] == pytest.approx(0.3333, rel=0, abs=1e-4)
    assert payload["p95_latency_ms"] == 200.0
    assert "text" not in payload
    assert "user_text" not in payload
    assert "bot_text" not in payload
