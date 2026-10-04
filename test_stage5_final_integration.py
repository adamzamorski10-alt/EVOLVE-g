from __future__ import annotations

import json
from datetime import date, datetime, timedelta

import pytest

from sqlmodel import Session, select

from app.database import engine
from app.models import UserDB
from test_training_execution import _context, _headers, client


class _FrozenDate(date):
    @classmethod
    def today(cls):
        # Monday keeps the production planner's deterministic Sunday rest day
        # out of the integration path while preserving real endpoint behavior.
        return cls(2026, 10, 5)


@pytest.fixture(autouse=True)
def freeze_core_loop_clock(monkeypatch):
    import app.nutrition.routes as nutrition_routes
    import app.training.routes as training_routes

    monkeypatch.setattr(__name__, "date", _FrozenDate)
    monkeypatch.setattr(training_routes, "date", _FrozenDate)
    monkeypatch.setattr(nutrition_routes, "date", _FrozenDate)


def _assessment_payload(**overrides):
    payload = {
        "training_level": "średniozaawansowany",
        "training_experience_years": 2,
        "sessions_per_week": 6,
        "availability_hours_per_week": 10,
        "recovery_score": 8,
        "basketball_level": "średniozaawansowany",
    }
    payload.update(overrides)
    return payload


def _create_core_user():
    ctx = _context()
    profile = client.put(
        "/app/profile",
        json={
            "name": "Integration User",
            "sports": ["koszykówka"],
            "training_focus": ["klatka", "plecy"],
            "improvement_areas": [],
            "available_equipment": ["hantle"],
            "avoid_exercises": [],
            "sport_focus": "",
            "sport_specialization": "",
            "sport_training_days": [],
        },
        headers=_headers(ctx["token"]),
    )
    assert profile.status_code == 200, profile.text
    assessment = client.post(
        "/app/assessment",
        json=_assessment_payload(),
        headers=_headers(ctx["token"]),
    )
    assert assessment.status_code == 200, assessment.text
    return ctx, assessment.json()["assessment"]


def test_core_loop_profile_assessment_plan_training_progress_goal():
    ctx, assessment = _create_core_user()

    readiness = client.get("/app/plan/readiness", headers=_headers(ctx["token"]))
    assert readiness.status_code == 200
    assert readiness.json()["ready"] is True
    assert readiness.json()["assessment_version"] == assessment["version"]

    generated = client.post(
        "/app/plan/generate",
        json={"force": True},
        headers=_headers(ctx["token"]),
    )
    assert generated.status_code == 200, generated.text
    plan = generated.json()["plan"]
    assert plan["_evolve_core"]["assessment_id"] == assessment["id"]
    assert plan["_evolve_core"]["assessment_version"] == assessment["version"]

    # Planner day labels are Polish; use the same deterministic weekday mapping.
    today_name = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"][_FrozenDate.today().weekday()]
    today = next(day for day in plan["days"] if day["day"] == today_name)
    assert today["day_type"] != "rest"
    assert today["workout"]["exercises"]

    started = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
    assert started.status_code == 200, started.text
    sid = started.json()["session"]["id"]
    exercise = started.json()["session"]["planned"]["exercises"][0]
    exercise_key = exercise.get("exercise_key") or exercise.get("id") or "squat-1"

    logged = client.post(
        f"/app/training/sessions/{sid}/sets",
        json={
            "exercise_key": exercise_key,
            "set_number": 1,
            "actual_reps": 5,
            "actual_weight_kg": 80,
            "actual_rpe": 7,
            "completed": True,
        },
        headers=_headers(ctx["token"]),
    )
    assert logged.status_code == 200, logged.text

    completed = client.post(
        f"/app/training/sessions/{sid}/complete",
        json={"final_rpe": 7},
        headers=_headers(ctx["token"]),
    )
    assert completed.status_code == 200, completed.text

    progress = client.get("/app/training/progress", headers=_headers(ctx["token"]))
    assert progress.status_code == 200, progress.text
    assert progress.json()["period_sessions"] == 1
    assert progress.json()["total_completed_sets"] == 1
    assert progress.json()["total_volume_kg"] == 400

    goal = client.post(
        "/app/goals",
        json={
            "goal_type": "strength",
            "title": "Integration strength goal",
            "metric_key": "best_weight_kg",
            "baseline_value": 80,
            "target_value": 100,
            "metadata": {"exercise_key": exercise_key},
        },
        headers=_headers(ctx["token"]),
    )
    assert goal.status_code == 200, goal.text
    goal_id = goal.json()["id"]

    goal_progress = client.get(
        f"/app/goals/{goal_id}/progress",
        headers=_headers(ctx["token"]),
    )
    assert goal_progress.status_code == 200, goal_progress.text
    assert goal_progress.json()["current_value"] == 80
    assert goal_progress.json()["progress_pct"] == 0
    assert goal_progress.json()["history"]


def test_nutrition_adaptation_changes_target_and_plan_macros():
    ctx, _ = _create_core_user()

    generated = client.post(
        "/app/plan/generate",
        json={"force": True},
        headers=_headers(ctx["token"]),
    )
    assert generated.status_code == 200, generated.text

    with Session(engine) as db:
        user = db.exec(select(UserDB).where(UserDB.email == ctx["email"])).first()
        assert user is not None
        base_target = float(user.calories_target or 0)
        assert base_target > 0

    # Seven distinct logged days create the minimum nutrition evidence window.
    for offset in range(7):
        consumed_at = datetime.combine(
            date.today() - timedelta(days=offset),
            datetime.min.time(),
        ).isoformat()
        response = client.post(
            "/app/nutrition/entries",
            json={
                "name": f"Integration meal {offset}",
                "meal_type": "other",
                "consumed_at": consumed_at,
                "calories_kcal": max(0, base_target * 0.70),
                "protein_g": 120,
            },
            headers=_headers(ctx["token"]),
        )
        assert response.status_code == 201, response.text

    # The adaptation contract also requires two completed training sessions.
    for _ in range(2):
        started = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
        assert started.status_code == 200, started.text
        sid = started.json()["session"]["id"]
        exercise = started.json()["session"]["planned"]["exercises"][0]
        exercise_key = exercise.get("id") or exercise.get("exercise_key") or "squat-1"
        logged = client.post(
            f"/app/training/sessions/{sid}/sets",
            json={
                "exercise_key": exercise_key,
                "set_number": 1,
                "actual_reps": 5,
                "actual_weight_kg": 80,
                "actual_rpe": 7,
                "completed": True,
            },
            headers=_headers(ctx["token"]),
        )
        assert logged.status_code == 200, logged.text
        completed = client.post(
            f"/app/training/sessions/{sid}/complete",
            json={"final_rpe": 7},
            headers=_headers(ctx["token"]),
        )
        assert completed.status_code == 200, completed.text

    preview = client.get(
        "/app/nutrition/adaptation?days=14",
        headers=_headers(ctx["token"]),
    )
    assert preview.status_code == 200, preview.text
    preview_data = preview.json()
    assert preview_data["status"] == "ready"
    assert preview_data["adaptation_allowed"] is True
    assert preview_data["change_kcal"] == 100

    applied = client.post(
        "/app/nutrition/adaptation/apply?days=14",
        headers=_headers(ctx["token"]),
    )
    assert applied.status_code == 200, applied.text
    applied_data = applied.json()
    assert applied_data["status"] == "applied"
    assert applied_data["change_kcal"] == 100

    with Session(engine) as db:
        user = db.exec(select(UserDB).where(UserDB.email == ctx["email"])).first()
        assert user is not None
        assert float(user.calories_target) == base_target + 100

    regenerated = client.post(
        "/app/plan/generate",
        json={"force": True},
        headers=_headers(ctx["token"]),
    )
    assert regenerated.status_code == 200, regenerated.text
    regenerated_plan = regenerated.json()["plan"]
    workout_day = next(day for day in regenerated_plan["days"] if day["day_type"] != "rest")
    assert workout_day["macros"]["kcal"] == base_target + 100


def test_assessment_change_invalidates_plan_before_training_and_regeneration_restores_provenance():
    ctx, first = _create_core_user()
    generated = client.post(
        "/app/plan/generate",
        json={"force": True},
        headers=_headers(ctx["token"]),
    )
    assert generated.status_code == 200, generated.text

    second = client.post(
        "/app/assessment",
        json=_assessment_payload(sessions_per_week=6, shooting_pct=61),
        headers=_headers(ctx["token"]),
    )
    assert second.status_code == 200, second.text

    readiness = client.get("/app/plan/readiness", headers=_headers(ctx["token"]))
    assert readiness.status_code == 200
    assert readiness.json()["plan_stale"] is True
    assert readiness.json()["assessment_version"] == 2

    blocked = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
    assert blocked.status_code == 409, blocked.text

    today = client.get("/app/training/today", headers=_headers(ctx["token"]))
    assert today.status_code == 200, today.text
    assert today.json()["plan_stale"] is True
    assert today.json()["can_start"] is False

    regenerated = client.post(
        "/app/plan/generate",
        json={"force": False},
        headers=_headers(ctx["token"]),
    )
    assert regenerated.status_code == 200, regenerated.text
    new_plan = regenerated.json()["plan"]
    assert new_plan["_evolve_core"]["assessment_id"] == second.json()["assessment"]["id"]
    assert new_plan["_evolve_core"]["assessment_version"] == 2

    resumed_after_regeneration = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
    assert resumed_after_regeneration.status_code == 200, resumed_after_regeneration.text

    with Session(engine) as db:
        user = db.exec(select(UserDB).where(UserDB.email == ctx["email"])).first()
        assert user is not None
        stored_plan = json.loads(user.weekly_plan_json)
        assert stored_plan["_evolve_core"]["assessment_id"] == second.json()["assessment"]["id"]
        assert stored_plan["_evolve_core"]["assessment_id"] != first["id"]
