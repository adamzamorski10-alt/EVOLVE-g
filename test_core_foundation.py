from __future__ import annotations

import json

from sqlmodel import Session, select

import pytest

from app.auth import routes as auth_routes
from app.database import engine
from app.models import AssessmentDB, UserDB
from test_training_execution import _context, _headers, client


@pytest.fixture(autouse=True)
def _disable_registration_rate_limit():
    previous = auth_routes.limiter.enabled
    auth_routes.limiter.enabled = False
    yield
    auth_routes.limiter.enabled = previous


def test_profile_updates_core_planning_constraints():
    ctx = _context()
    response = client.put(
        "/app/profile",
        json={
            "name": "Core User",
            "sports": ["koszykówka"],
            "training_focus": ["siła", "eksplozywność"],
            "improvement_areas": ["rzut"],
            "available_equipment": ["sztanga", "hantle"],
            "sport_focus": "koszykówka",
            "sport_specialization": "rzuty",
            "sport_training_days": ["Środa", "Sobota"],
        },
        headers=_headers(ctx["token"]),
    )
    assert response.status_code == 200, response.text
    profile = response.json()["profile"]
    assert profile["training_focus"] == ["siła", "eksplozywność"]
    assert profile["available_equipment"] == ["sztanga", "hantle"]
    assert profile["sport_focus"] == "koszykówka"


def test_assessment_is_versioned_and_user_scoped():
    first = _context()
    second = _context()
    payload = {
        "training_level": "średniozaawansowany",
        "training_experience_years": 2,
        "sessions_per_week": 4,
        "availability_hours_per_week": 6,
        "recovery_score": 7,
        "basketball_level": "średniozaawansowany",
        "shooting_pct": 52,
        "free_throw_pct": 78,
        "sprint_30m_seconds": 4.6,
        "vertical_jump_cm": 48,
        "metrics": {"bench_5rm_kg": 80},
    }
    first_save = client.post("/app/assessment", json=payload, headers=_headers(first["token"]))
    second_save = client.post("/app/assessment", json={**payload, "shooting_pct": 55}, headers=_headers(first["token"]))
    assert first_save.status_code == 200
    assert second_save.status_code == 200
    assert first_save.json()["assessment"]["version"] == 1
    assert second_save.json()["assessment"]["version"] == 2

    own = client.get("/app/assessment/latest", headers=_headers(first["token"]))
    foreign = client.get("/app/assessment/latest", headers=_headers(second["token"]))
    assert own.status_code == 200
    assert own.json()["assessment"]["version"] == 2
    assert own.json()["assessment"]["shooting_pct"] == 55
    assert foreign.status_code == 200
    assert foreign.json()["has_assessment"] is False

    with Session(engine) as db:
        rows = list(db.exec(select(AssessmentDB)).all())
        assert len(rows) >= 2
        assert all(row.user_id for row in rows)


def test_assessment_requires_real_baseline():
    ctx = _context()
    response = client.post(
        "/app/assessment",
        json={"notes": "tylko notatka"},
        headers=_headers(ctx["token"]),
    )
    assert response.status_code == 422


def test_plan_readiness_and_generation_keep_provenance():
    ctx = _context()
    before = client.get("/app/plan/readiness", headers=_headers(ctx["token"]))
    assert before.status_code == 200
    assert before.json()["profile_ready"] is True
    assert before.json()["assessment_ready"] is False

    assessment = client.post(
        "/app/assessment",
        json={"training_level": "średniozaawansowany", "sessions_per_week": 4, "recovery_score": 8},
        headers=_headers(ctx["token"]),
    )
    assert assessment.status_code == 200

    after = client.get("/app/plan/readiness", headers=_headers(ctx["token"]))
    assert after.json()["assessment_ready"] is True
    assert after.json()["assessment_version"] == 1

    generated = client.post(
        "/app/plan/generate",
        json={"force": True},
        headers=_headers(ctx["token"]),
    )
    assert generated.status_code == 200, generated.text
    plan = generated.json()["plan"]
    assert plan["_evolve_core"]["planning_source"] == "deterministic-v2"
    assert plan["_evolve_core"]["assessment_version"] == 1


def test_core_setup_uis_are_available():
    assert client.get("/app/assessment/ui").status_code == 200
    assert "Assessment początkowy" in client.get("/app/assessment/ui").text
    assert client.get("/app/plan/ui").status_code == 200
    assert "Planowanie treningu" in client.get("/app/plan/ui").text
