from __future__ import annotations

import json

from sqlmodel import Session, select

from app.database import engine
from app.models import AdaptivePlanRevisionDB, UserDB
from test_training_execution import _context, _headers, client


def _complete_one(ctx):
    started = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
    assert started.status_code == 200, started.text
    sid = started.json()["session"]["id"]
    logged = client.post(
        f"/app/training/sessions/{sid}/sets",
        json={
            "exercise_key": "squat-1",
            "set_number": 1,
            "actual_reps": 5,
            "actual_weight_kg": 100,
            "actual_rpe": 7,
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
    return sid


def test_today_uses_base_plan_without_adaptation():
    ctx = _context()
    response = client.get("/app/training/today", headers=_headers(ctx["token"]))
    assert response.status_code == 200
    data = response.json()
    assert data["has_workout"] is True
    assert data["plan"]["source"] == "base"
    assert data["plan"]["version"] == 0
    assert data["exercises"][0]["weight_kg"] == 100


def test_apply_adaptation_becomes_effective_today_plan_and_start_snapshot():
    ctx = _context()
    sid = _complete_one(ctx)

    applied = client.post("/app/training/adaptive/apply", headers=_headers(ctx["token"]))
    assert applied.status_code == 200, applied.text
    data = applied.json()
    assert data["status"] == "applied"
    assert data["version"] == 1

    today = client.get("/app/training/today", headers=_headers(ctx["token"]))
    assert today.status_code == 200
    today_data = today.json()
    assert today_data["plan"]["source"] == "adaptive"
    assert today_data["plan"]["version"] == 1
    assert today_data["exercises"][0]["weight_kg"] == 95

    started = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
    assert started.status_code == 200
    snapshot = started.json()["session"]["planned"]
    assert snapshot["plan_source"] == "adaptive"
    assert snapshot["plan_version"] == 1
    assert snapshot["exercises"][0]["weight_kg"] == 95

    with Session(engine) as db:
        revision = db.exec(
            select(AdaptivePlanRevisionDB)
            .where(AdaptivePlanRevisionDB.user_id == db.exec(select(UserDB).where(UserDB.email == ctx["email"])).first().id)
        ).first()
        assert revision is not None
        applied_plan = json.loads(revision.applied_plan_json)
        assert applied_plan["days"][0]["workout"]["exercises"][0]["weight_kg"] == 95
        assert sid in revision.source_session_ids()


def test_effective_adaptive_plan_is_user_scoped():
    first = _context()
    second = _context()
    _complete_one(first)
    applied = client.post("/app/training/adaptive/apply", headers=_headers(first["token"]))
    assert applied.status_code == 200

    first_today = client.get("/app/training/today", headers=_headers(first["token"]))
    second_today = client.get("/app/training/today", headers=_headers(second["token"]))
    assert first_today.status_code == 200
    assert second_today.status_code == 200
    assert first_today.json()["plan"]["source"] == "adaptive"
    assert first_today.json()["exercises"][0]["weight_kg"] == 95
    assert second_today.json()["plan"]["source"] == "base"
    assert second_today.json()["plan"]["version"] == 0
    assert second_today.json()["exercises"][0]["weight_kg"] == 100


def test_today_ui_exposes_effective_plan_and_start_action():
    response = client.get("/app/training/today-ui")
    assert response.status_code == 200
    assert "Mój dzień" in response.text
    assert "/app/training/today" in response.text
    assert "/app/training/session-ui" in response.text
    assert "dostosowany na podstawie ostatnich treningów" in response.text
