from __future__ import annotations

import uuid

import pytest

from app.auth import routes as auth_routes
from test_training_execution import _headers, client


@pytest.fixture(autouse=True)
def _disable_registration_rate_limit():
    previous = auth_routes.limiter.enabled
    auth_routes.limiter.enabled = False
    yield
    auth_routes.limiter.enabled = previous


def _baseline(ctx, **overrides):
    payload = {
        "training_level": "średniozaawansowany",
        "sessions_per_week": 3,
        "availability_hours_per_week": 6,
        "recovery_score": 8,
        "basketball_level": "średniozaawansowany",
    }
    payload.update(overrides)
    response = client.post("/app/assessment", json=payload, headers=_headers(ctx["token"]))
    assert response.status_code == 200, response.text
    return response.json()["assessment"]


def _register_profile_user():
    email = f"sport-profile-{uuid.uuid4().hex[:10]}@example.com"
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "SecurePassword123",
            "nickname": f"sport_profile_{uuid.uuid4().hex[:10]}",
            "name": "Sport Profile Test",
            "age": 25,
            "height": 188,
            "weight": 82,
            "target_weight": 85,
            "goal": "Budowa siły i wyskoku",
            "frequency": "3-4 razy w tygodniu",
            "diet": "zbilansowana",
        },
    )
    assert response.status_code == 200, response.text
    return {"token": response.json()["access_token"]}


def test_sport_profile_round_trips_through_get_and_put():
    ctx = _register_profile_user()
    headers = _headers(ctx["token"])
    payload = {
        "basketball_position": "SG",
        "training_experience": "advanced",
        "equipment": "hybrid",
        "health_limitations": "Lekkie przeciążenie lewego kolana",
    }

    updated = client.put("/app/profile", json=payload, headers=headers)
    assert updated.status_code == 200, updated.text
    assert {key: updated.json()["profile"][key] for key in payload} == payload

    fetched = client.get("/app/profile", headers=headers)
    assert fetched.status_code == 200, fetched.text
    assert {key: fetched.json()[key] for key in payload} == payload


def test_sport_profile_is_in_plan_provenance_and_marks_plan_stale():
    ctx = _register_profile_user()
    headers = _headers(ctx["token"])
    profile = {
        "basketball_position": "SG",
        "training_experience": "intermediate",
        "equipment": "dumbbells",
        "health_limitations": "Lekkie przeciążenie lewego kolana",
    }
    updated = client.put("/app/profile", json=profile, headers=headers)
    assert updated.status_code == 200, updated.text

    readiness_before = client.get("/app/plan/readiness", headers=headers)
    assert readiness_before.status_code == 200
    assert readiness_before.json()["assessment_ready"] is False
    assert readiness_before.json()["ready"] is False

    assessment = _baseline(ctx)
    generated = client.post("/app/plan/generate", json={"force": True}, headers=headers)
    assert generated.status_code == 200, generated.text
    plan = generated.json()["plan"]
    provenance = plan["_evolve_core"]
    assert {key: provenance["profile_inputs"][key] for key in profile} == profile
    assert provenance["assessment_id"] == assessment["id"]
    assert provenance["assessment_version"] == 1

    changed = client.put("/app/profile", json={"equipment": "gym_full"}, headers=headers)
    assert changed.status_code == 200, changed.text
    readiness_after = client.get("/app/plan/readiness", headers=headers)
    assert readiness_after.status_code == 200
    assert readiness_after.json()["profile_stale"] is True
    assert readiness_after.json()["plan_stale"] is True


def test_position_selects_basketball_drills_and_equipment_limits_workout():
    ctx = _register_profile_user()
    headers = _headers(ctx["token"])
    updated = client.put(
        "/app/profile",
        json={
            "basketball_position": "SG",
            "equipment": "dumbbells",
            "sport_training_days": ["Środa"],
            "training_focus": ["klatka"],
            "improvement_areas": [],
        },
        headers=headers,
    )
    assert updated.status_code == 200, updated.text
    _baseline(ctx)

    generated = client.post("/app/plan/generate", json={"force": True}, headers=headers)
    assert generated.status_code == 200, generated.text
    plan = generated.json()["plan"]
    sport_days = [day for day in plan["days"] if day["is_sport_session"]]
    assert sport_days
    assert all(day["workout"]["exercises"] for day in sport_days)

    exercises = [
        exercise["name"].lower()
        for day in plan["days"]
        if day["day_type"] != "rest"
        for exercise in day["workout"]["exercises"]
    ]
    assert exercises
    assert all(
        "sztang" not in name and "maszyn" not in name and "leg press" not in name
        for name in exercises
    )


def test_health_limitations_exclude_matching_exercises():
    ctx = _register_profile_user()
    headers = _headers(ctx["token"])
    updated = client.put(
        "/app/profile",
        json={"health_limitations": "Ból kolana i przeciążenie barku"},
        headers=headers,
    )
    assert updated.status_code == 200, updated.text
    _baseline(ctx)

    generated = client.post("/app/plan/generate", json={"force": True}, headers=headers)
    assert generated.status_code == 200, generated.text
    exercises = [
        exercise["name"].lower()
        for day in generated.json()["plan"]["days"]
        if day["day_type"] != "rest"
        for exercise in day["workout"]["exercises"]
    ]
    assert exercises
    assert all("przysiad ze sztangą" not in name for name in exercises)
    assert all("wyciskanie żołnierskie" not in name for name in exercises)
