"""Unit tests for DietPlan and RoutinePlan models."""
import uuid
import pytest
from unittest.mock import patch

from backend.app import create_app
from backend.extensions import db as _db
from backend.plans.models import DietPlan, RoutinePlan
from backend.login.models import User


def _str_uuid():
    """Return a UUID as string so SQLite can store it."""
    return str(uuid.uuid4())


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
    u = User(email="plan@test.com", username="plan_user", full_name="Plan User")
    u.set_password("Secret123")
    session.add(u)
    session.flush()
    return u


# ── DietPlan ────────────────────────────────────────────────────────


def test_create_diet_plan(session, user):
    plan = DietPlan(
        id=_str_uuid(),
        user_id=user.id,
        title="Dieta Cutting",
        goal="Bajar grasa",
        content={
            "days": [
                {"day": "lunes", "meals": [{"name": "Desayuno", "calories": 400}]},
            ]
        },
    )
    session.add(plan)
    session.commit()

    assert plan.id is not None
    assert plan.title == "Dieta Cutting"
    assert plan.version == 1


def test_diet_plan_uuid_unique(session, user):
    p1 = DietPlan(id=_str_uuid(), user_id=user.id, title="Plan A", content={"days": []})
    p2 = DietPlan(id=_str_uuid(), user_id=user.id, title="Plan B", content={"days": []})
    session.add_all([p1, p2])
    session.commit()

    assert str(p1.id) != str(p2.id)


def test_diet_plan_json_content(session, user):
    content = {
        "days": [
            {
                "day": "lunes",
                "meals": [
                    {"name": "Desayuno", "calories": 500, "protein_g": 30},
                    {"name": "Almuerzo", "calories": 800, "protein_g": 50},
                ],
            }
        ],
        "total_calories": 2200,
    }
    plan = DietPlan(id=_str_uuid(), user_id=user.id, title="Bulk", goal="Masa muscular", content=content)
    session.add(plan)
    session.commit()

    fetched = session.get(DietPlan, plan.id)
    assert fetched.content["total_calories"] == 2200
    assert len(fetched.content["days"][0]["meals"]) == 2


def test_diet_plan_versioning(session, user):
    plan = DietPlan(id=_str_uuid(), user_id=user.id, title="V1", content={"days": []}, version=1)
    session.add(plan)
    session.commit()

    plan.version = 2
    plan.content = {"days": [{"day": "lunes", "meals": []}]}
    session.commit()

    assert plan.version == 2


def test_diet_plan_timestamps(session, user):
    plan = DietPlan(id=_str_uuid(), user_id=user.id, title="Timestamps", content={})
    session.add(plan)
    session.commit()

    assert plan.created_at is not None
    assert plan.updated_at is not None


# ── RoutinePlan ─────────────────────────────────────────────────────


def test_create_routine_plan(session, user):
    plan = RoutinePlan(
        id=_str_uuid(),
        user_id=user.id,
        title="Push Pull Legs",
        objective="Hipertrofia",
        content={
            "weeks": [
                {
                    "week": 1,
                    "days": [
                        {
                            "day": "lunes",
                            "focus": "push",
                            "exercises": [
                                {"name": "Press banca", "sets": 4, "reps": "8-10"},
                            ],
                        }
                    ],
                }
            ]
        },
    )
    session.add(plan)
    session.commit()

    assert plan.id is not None
    assert plan.title == "Push Pull Legs"
    assert plan.objective == "Hipertrofia"
    assert plan.version == 1


def test_routine_plan_uuid_not_guessable(session, user):
    plans = []
    for i in range(5):
        p = RoutinePlan(id=_str_uuid(), user_id=user.id, title=f"R{i}", content={})
        session.add(p)
        plans.append(p)
    session.commit()

    ids = [str(p.id) for p in plans]
    # UUIDs should all be unique and not sequential integers
    assert len(set(ids)) == 5
    for pid in ids:
        assert len(pid) >= 32  # UUID string length


def test_routine_plan_json_content_complex(session, user):
    content = {
        "weeks": [
            {
                "week": 1,
                "days": [
                    {
                        "day": "lunes",
                        "focus": "push",
                        "exercises": [
                            {"name": "Press banca", "sets": 4, "reps": "8-10", "rest_s": 90},
                            {"name": "Press inclinado", "sets": 3, "reps": "10-12", "rest_s": 75},
                        ],
                    },
                    {
                        "day": "martes",
                        "focus": "pull",
                        "exercises": [
                            {"name": "Dominadas", "sets": 4, "reps": "6-8", "rest_s": 120},
                        ],
                    },
                ],
            }
        ]
    }
    plan = RoutinePlan(id=_str_uuid(), user_id=user.id, title="Full PPL", content=content)
    session.add(plan)
    session.commit()

    fetched = session.get(RoutinePlan, plan.id)
    week1 = fetched.content["weeks"][0]
    assert len(week1["days"]) == 2
    assert week1["days"][0]["exercises"][0]["name"] == "Press banca"


def test_routine_plan_timestamps(session, user):
    plan = RoutinePlan(id=_str_uuid(), user_id=user.id, title="TS", content={})
    session.add(plan)
    session.commit()

    assert plan.created_at is not None
    assert plan.updated_at is not None


def test_multiple_plans_per_user(session, user):
    for i in range(3):
        session.add(DietPlan(id=_str_uuid(), user_id=user.id, title=f"Diet {i}", content={}))
        session.add(RoutinePlan(id=_str_uuid(), user_id=user.id, title=f"Routine {i}", content={}))
    session.commit()

    diets = DietPlan.query.filter_by(user_id=user.id).all()
    routines = RoutinePlan.query.filter_by(user_id=user.id).all()
    assert len(diets) == 3
    assert len(routines) == 3
