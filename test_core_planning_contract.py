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


def test_planner_normalizes_short_sport_weekdays():
    ctx = _context()
    response = client.put(
        "/app/profile",
        json={"sport_focus": "koszykówka", "sport_training_days": ["śr", "Sob."]},
        headers=_headers(ctx["token"]),
    )
    assert response.status_code == 200, response.text
    _baseline(ctx, sessions_per_week=3)
    generated = client.post("/app/plan/generate", json={"force": True}, headers=_headers(ctx["token"]))
    assert generated.status_code == 200, generated.text
    days = generated.json()["plan"]["days"]
    assert [day["day"] for day in days if day["is_sport_session"]] == ["Środa", "Sobota"]


def test_availability_weekdays_are_normalized():
    from app.plan.deterministic import _normalize_weekday
    assert _normalize_weekday("wt") == "Wtorek"
    assert _normalize_weekday("Czw.") == "Czwartek"
    assert _normalize_weekday("unknown") is None


def test_availability_api_persists_canonical_days():
    ctx = _context()
    response = client.put(
        "/app/plan/availability",
        json={"days": ["wt", "Czw.", "sob"]},
        headers=_headers(ctx["token"]),
    )
    assert response.status_code == 200, response.text
    assert response.json() == {
        "days": ["Wtorek", "Czwartek", "Sobota"],
        "windows": {},
        "session_duration_minutes": 60,
    }
    fetched = client.get("/app/plan/availability", headers=_headers(ctx["token"]))
    assert fetched.status_code == 200
    assert fetched.json() == response.json()


def test_availability_days_constrain_generated_plan():
    ctx = _context()
    headers = _headers(ctx["token"])
    _baseline(ctx, sessions_per_week=4)
    saved = client.put(
        "/app/plan/availability",
        json={"days": ["Wtorek", "Czwartek", "Sobota"]},
        headers=headers,
    )
    assert saved.status_code == 200, saved.text
    generated = client.post(
        "/app/plan/generate",
        json={"force": True},
        headers=headers,
    )
    assert generated.status_code == 200, generated.text
    sessions = [
        day["day"] for day in generated.json()["plan"]["days"]
        if day["day_type"] != "rest"
    ]
    assert sessions
    assert set(sessions).issubset({"Wtorek", "Czwartek", "Sobota"})
    assert len(sessions) <= 3


def test_availability_change_marks_existing_plan_stale():
    ctx = _context()
    headers = _headers(ctx["token"])
    _baseline(ctx, sessions_per_week=3)
    generated = client.post("/app/plan/generate", json={"force": True}, headers=headers)
    assert generated.status_code == 200, generated.text

    updated = client.put(
        "/app/plan/availability",
        json={"days": ["Poniedziałek", "Piątek"]},
        headers=headers,
    )
    assert updated.status_code == 200, updated.text
    readiness = client.get("/app/plan/readiness", headers=headers)
    assert readiness.status_code == 200, readiness.text
    assert readiness.json()["profile_stale"] is True


def test_availability_api_rejects_unknown_weekday():
    ctx = _context()
    response = client.put(
        "/app/plan/availability",
        json={"days": ["Someday"]},
        headers=_headers(ctx["token"]),
    )
    assert response.status_code == 422


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



def test_low_recovery_reduces_session_volume():
    ctx = _context()
    _baseline(ctx, sessions_per_week=3, recovery_score=4)
    generated = client.post(
        "/app/plan/generate",
        json={"force": True},
        headers=_headers(ctx["token"]),
    )
    assert generated.status_code == 200, generated.text
    workout_days = [
        day for day in generated.json()["plan"]["days"]
        if day["day_type"] != "rest"
    ]
    assert workout_days
    assert all(len(day["workout"]["exercises"]) <= 2 for day in workout_days if not day["is_sport_session"])



def test_rolling_endpoint_returns_a_fresh_dated_horizon_and_is_authenticated():
    from datetime import date, timedelta

    ctx = _context()
    missing_plan = client.get("/app/plan/rolling", headers=_headers(ctx["token"]))
    assert missing_plan.status_code == 200, missing_plan.text
    empty = missing_plan.json()
    assert empty["horizon_start"] == date.today().isoformat()
    assert empty["horizon_end"] == (date.today() + timedelta(days=13)).isoformat()
    assert empty["sufficient_data"] is True
    assert empty["planned_days"]
    assert empty["reason_codes"] == []

    _baseline(ctx, sessions_per_week=3)
    generated = client.post(
        "/app/plan/generate",
        json={"force": True},
        headers=_headers(ctx["token"]),
    )
    assert generated.status_code == 200, generated.text
    response = client.get("/app/plan/rolling?horizon_days=14", headers=_headers(ctx["token"]))
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["plan_version"] == "rolling-v1"
    assert data["horizon_start"] == date.today().isoformat()
    assert data["horizon_end"] == (date.today() + timedelta(days=13)).isoformat()
    dates = [item["scheduled_date"] for item in data["upcoming_sessions"]]
    planned_dates = [item["scheduled_date"] for item in data["planned_days"]]
    assert dates == sorted(dates)
    assert len(dates) == len(set(dates))
    assert planned_dates == sorted(planned_dates)
    assert len(planned_dates) == len(set(planned_dates))
    assert all(data["horizon_start"] <= value <= data["horizon_end"] for value in planned_dates)
    assert all(item.get("status") != "completed" for item in data["upcoming_sessions"])
    assert all(item["day_type"] == "rest" for item in data["rest_days"])
    assert all(item["status"] == "rest" for item in data["rest_days"])
    assert all(item["day_type"] != "rest" for item in data["upcoming_sessions"])


def test_rolling_endpoint_rejects_unauthenticated_requests():
    response = client.get("/app/plan/rolling")
    assert response.status_code in (401, 403)

def test_availability_time_windows_are_persisted_and_canonicalized():
    ctx = _context()
    headers = _headers(ctx["token"])
    response = client.put(
        "/app/plan/availability",
        json={
            "days": ["pon", "wt", "śr"],
            "windows": {
                "Poniedziałek": {"start": "16:00", "end": "16:30"},
                "wt": {"start": "17:00", "end": "19:00"},
            },
            "session_duration_minutes": 60,
        },
        headers=headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["days"] == ["Poniedziałek", "Wtorek", "Środa"]
    assert response.json()["windows"] == {
        "Poniedziałek": {"start": "16:00", "end": "16:30"},
        "Wtorek": {"start": "17:00", "end": "19:00"},
    }
    assert response.json()["session_duration_minutes"] == 60


def test_planner_excludes_availability_windows_shorter_than_session_duration():
    ctx = _context()
    headers = _headers(ctx["token"])
    _baseline(ctx, sessions_per_week=3)
    saved = client.put(
        "/app/plan/availability",
        json={
            "days": ["Poniedziałek", "Wtorek", "Środa", "Czwartek"],
            "windows": {
                "Poniedziałek": {"start": "16:00", "end": "16:30"},
                "Wtorek": {"start": "16:00", "end": "18:00"},
            },
            "session_duration_minutes": 60,
        },
        headers=headers,
    )
    assert saved.status_code == 200, saved.text
    generated = client.post(
        "/app/plan/generate",
        json={"force": True},
        headers=headers,
    )
    assert generated.status_code == 200, generated.text
    sessions = [
        day["day"] for day in generated.json()["plan"]["days"]
        if day["day_type"] != "rest"
    ]
    assert "Poniedziałek" not in sessions
    assert set(sessions).issubset({"Wtorek", "Środa", "Czwartek"})


def test_availability_rejects_window_for_unselected_day():
    ctx = _context()
    response = client.put(
        "/app/plan/availability",
        json={
            "days": ["Wtorek"],
            "windows": {"Piątek": {"start": "16:00", "end": "18:00"}},
        },
        headers=_headers(ctx["token"]),
    )
    assert response.status_code == 422


def test_availability_rejects_non_increasing_time_window():
    ctx = _context()
    response = client.put(
        "/app/plan/availability",
        json={
            "days": ["Wtorek"],
            "windows": {"Wtorek": {"start": "18:00", "end": "17:00"}},
        },
        headers=_headers(ctx["token"]),
    )
    assert response.status_code == 422

def test_sport_config_persists_canonical_reserved_time_windows():
    ctx = _context()
    response = client.post(
        "/app/sport-config",
        json={
            "sport_focus": "koszykówka",
            "sport_specialization": "rzuty",
            "sport_training_days": ["śr", "Sob."],
            "sport_training_windows": {
                "śr": {"start": "18:00", "end": "19:30"},
                "Sobota": {"start": "10:00", "end": "11:30"},
            },
        },
        headers=_headers(ctx["token"]),
    )
    assert response.status_code == 200, response.text
    assert response.json()["sport_training_days"] == ["Środa", "Sobota"]
    assert response.json()["sport_training_windows"] == {
        "Środa": {"start": "18:00", "end": "19:30"},
        "Sobota": {"start": "10:00", "end": "11:30"},
    }


def test_sport_config_rejects_window_for_unconfigured_day():
    ctx = _context()
    response = client.post(
        "/app/sport-config",
        json={
            "sport_focus": "koszykówka",
            "sport_training_days": ["Środa"],
            "sport_training_windows": {"Piątek": {"start": "18:00", "end": "19:30"}},
        },
        headers=_headers(ctx["token"]),
    )
    assert response.status_code == 422


def test_generated_sport_session_exposes_reserved_time_window():
    ctx = _context()
    headers = _headers(ctx["token"])
    _baseline(ctx, sessions_per_week=3)
    configured = client.post(
        "/app/sport-config",
        json={
            "sport_focus": "koszykówka",
            "sport_specialization": "rzuty",
            "sport_training_days": ["śr"],
            "sport_training_windows": {"Środa": {"start": "18:00", "end": "19:30"}},
        },
        headers=headers,
    )
    assert configured.status_code == 200, configured.text
    generated = client.post("/app/plan/generate", json={"force": True}, headers=headers)
    assert generated.status_code == 200, generated.text
    sport_days = [day for day in generated.json()["plan"]["days"] if day["is_sport_session"]]
    assert len(sport_days) == 1
    assert sport_days[0]["day"] == "Środa"
    assert sport_days[0]["workout"]["scheduled_time"] == {"start": "18:00", "end": "19:30"}

