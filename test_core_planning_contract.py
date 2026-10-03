from __future__ import annotations

import pytest

from app.auth import routes as auth_routes
from test_training_execution import _context, _headers, client


@pytest.fixture(autouse=True)
def _disable_registration_rate_limit():
    previous = auth_routes.limiter.enabled
    auth_routes.limiter.enabled = False
    yield
    auth_routes.limiter.enabled = previous


def _baseline(ctx, **overrides):
    payload = {
        "training_level": "średniozaawansowany",
        "sessions_per_week": 4,
        "availability_hours_per_week": 6,
        "recovery_score": 8,
        "basketball_level": "średniozaawansowany",
    }
    payload.update(overrides)
    response = client.post("/app/assessment", json=payload, headers=_headers(ctx["token"]))
    assert response.status_code == 200, response.text
    return response.json()["assessment"]


def _core(plan):
    value = dict(plan)
    value.pop("generated_at", None)
    return value


def test_planner_requires_assessment_and_reports_readiness():
    ctx = _context()
    readiness = client.get("/app/plan/readiness", headers=_headers(ctx["token"]))
    assert readiness.status_code == 200
    body = readiness.json()
    assert body["profile_ready"] is True
    assert body["assessment_ready"] is False
    assert body["ready"] is False
    assert body["next"] == "complete_assessment"

    generated = client.post(
        "/app/plan/generate",
        json={"force": True},
        headers=_headers(ctx["token"]),
    )
    assert generated.status_code == 400


def test_planner_is_reproducible_from_same_profile_and_assessment():
    ctx = _context()
    assessment = _baseline(ctx, sessions_per_week=3)

    first = client.post(
        "/app/plan/generate",
        json={"force": True},
        headers=_headers(ctx["token"]),
    )
    second = client.post(
        "/app/plan/generate",
        json={"force": True},
        headers=_headers(ctx["token"]),
    )
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert _core(first.json()["plan"]) == _core(second.json()["plan"])
    assert first.json()["plan"]["_evolve_core"]["planning_source"] == "deterministic-v2"
    assert first.json()["plan"]["_evolve_core"]["assessment_id"] == assessment["id"]
    assert first.json()["plan"]["_evolve_core"]["assessment_version"] == 1
    assert len([
        day for day in first.json()["plan"]["days"]
        if day["day_type"] != "rest"
    ]) == 3


def test_profile_equipment_changes_plan_behavior():
    ctx = _context()
    response = client.put(
        "/app/profile",
        json={
            "training_focus": ["klatka"],
            "improvement_areas": [],
            "available_equipment": ["hantle"],
            "avoid_exercises": [],
        },
        headers=_headers(ctx["token"]),
    )
    assert response.status_code == 200, response.text
    _baseline(ctx, sessions_per_week=3)

    generated = client.post(
        "/app/plan/generate",
        json={"force": True},
        headers=_headers(ctx["token"]),
    )
    assert generated.status_code == 200, generated.text
    exercises = [
        exercise["name"].lower()
        for day in generated.json()["plan"]["days"]
        for exercise in day["workout"]["exercises"]
        if day["day_type"] != "rest"
    ]
    assert exercises
    assert all("sztang" not in name and "maszyn" not in name and "leg press" not in name for name in exercises)


def test_new_assessment_invalidates_existing_plan_by_provenance():
    ctx = _context()
    first_assessment = _baseline(ctx, sessions_per_week=4)
    generated = client.post(
        "/app/plan/generate",
        json={"force": True},
        headers=_headers(ctx["token"]),
    )
    assert generated.status_code == 200

    second_assessment = _baseline(ctx, sessions_per_week=2, shooting_pct=55)
    readiness = client.get("/app/plan/readiness", headers=_headers(ctx["token"]))
    assert readiness.status_code == 200
    body = readiness.json()
    assert body["plan_stale"] is True
    assert body["assessment_stale"] is True
    assert body["assessment_version"] == 2

    regenerated = client.post(
        "/app/plan/generate",
        json={"force": False},
        headers=_headers(ctx["token"]),
    )
    assert regenerated.status_code == 200, regenerated.text
    plan = regenerated.json()["plan"]
    assert plan["_evolve_core"]["assessment_id"] == second_assessment["id"]
    assert plan["_evolve_core"]["assessment_version"] == 2
    assert plan["_evolve_core"]["assessment_id"] != first_assessment["id"]


def test_assessment_is_not_shared_between_users():
    first = _context()
    second = _context()
    _baseline(first, shooting_pct=52)

    own = client.get("/app/assessment/latest", headers=_headers(first["token"]))
    foreign = client.get("/app/assessment/latest", headers=_headers(second["token"]))
    assert own.status_code == 200
    assert own.json()["has_assessment"] is True
    assert foreign.status_code == 200
    assert foreign.json()["has_assessment"] is False
