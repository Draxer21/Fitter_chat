"""Unit tests for ProgressLog model."""
import pytest
from decimal import Decimal

from backend.app import create_app
from backend.extensions import db as _db
from backend.chat.models import ProgressLog
from backend.login.models import User


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
    app = create_app()
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI="sqlite:///:memory:")
    with app.app_context():
        _db.create_all()
    yield app
    with app.app_context():
        _db.drop_all()


@pytest.fixture
def session(app):
    with app.app_context():
        yield _db.session


@pytest.fixture
def user(session):
    u = User(email="prog@test.com", username="prog_user", full_name="Prog User")
    u.set_password("Secret123")
    session.add(u)
    session.flush()
    return u


# ── Basic record ────────────────────────────────────────────────────


def test_record_basic(session):
    entry = ProgressLog.record(sender_id="sender1", metric="peso", value="75.5")
    session.commit()

    assert entry.id is not None
    assert entry.metric == "peso"
    assert entry.value == "75.5"
    assert entry.recorded_at is not None


def test_record_with_user(session, user):
    entry = ProgressLog.record(
        sender_id="sender1",
        metric="sentadilla",
        value="100",
        note="PR nuevo",
        user_id=user.id,
    )
    session.commit()

    assert entry.user_id == user.id
    assert entry.note == "PR nuevo"


# ── numeric_value auto-parse ────────────────────────────────────────


def test_numeric_value_parsed_from_number(session):
    entry = ProgressLog.record(sender_id="s1", metric="peso", value="82.3")
    session.commit()

    assert entry.numeric_value is not None
    assert float(entry.numeric_value) == pytest.approx(82.3)


def test_numeric_value_integer(session):
    entry = ProgressLog.record(sender_id="s1", metric="reps", value="12")
    session.commit()

    assert float(entry.numeric_value) == 12.0


def test_numeric_value_none_for_text(session):
    entry = ProgressLog.record(sender_id="s1", metric="estado", value="bien")
    session.commit()

    assert entry.numeric_value is None
    assert entry.value == "bien"


def test_numeric_value_none_when_value_is_none(session):
    entry = ProgressLog.record(sender_id="s1", metric="nota", value=None)
    session.commit()

    assert entry.numeric_value is None
    assert entry.value is None


# ── unit column ─────────────────────────────────────────────────────


def test_unit_stored(session):
    entry = ProgressLog.record(
        sender_id="s1", metric="peso", value="75", unit="kg"
    )
    session.commit()

    assert entry.unit == "kg"


def test_unit_default_none(session):
    entry = ProgressLog.record(sender_id="s1", metric="reps", value="10")
    session.commit()

    assert entry.unit is None


# ── to_dict ─────────────────────────────────────────────────────────


def test_to_dict_includes_new_fields(session):
    entry = ProgressLog.record(
        sender_id="s1", metric="peso", value="80.5", unit="kg"
    )
    session.commit()

    d = entry.to_dict()
    assert d["numeric_value"] == pytest.approx(80.5)
    assert d["unit"] == "kg"
    assert d["metric"] == "peso"
    assert d["value"] == "80.5"
    assert "recorded_at" in d


def test_to_dict_text_value(session):
    entry = ProgressLog.record(sender_id="s1", metric="mood", value="excelente")
    session.commit()

    d = entry.to_dict()
    assert d["numeric_value"] is None
    assert d["unit"] is None
    assert d["value"] == "excelente"


# ── Truncation safety ──────────────────────────────────────────────


def test_sender_id_truncated(session):
    long_sender = "x" * 200
    entry = ProgressLog.record(sender_id=long_sender, metric="test", value="1")
    session.commit()

    assert len(entry.sender_id) == 80


def test_metric_truncated(session):
    long_metric = "m" * 200
    entry = ProgressLog.record(sender_id="s1", metric=long_metric, value="1")
    session.commit()

    assert len(entry.metric) == 80


def test_value_truncated(session):
    long_value = "v" * 300
    entry = ProgressLog.record(sender_id="s1", metric="test", value=long_value)
    session.commit()

    assert len(entry.value) == 120
