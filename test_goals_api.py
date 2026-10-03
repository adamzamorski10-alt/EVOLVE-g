from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.auth import routes as auth_routes
from app.database import engine
from app.models import TrainingSessionDB, TrainingSetResultDB, UserDB
from main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def _disable_rate_limit():
    previous = auth_routes.limiter.enabled
    auth_routes.limiter.enabled = False
    yield
    auth_routes.limiter.enabled = previous

def _user_context():
    suffix = uuid.uuid4().hex[:10]
    email = f"goal-api-{suffix}@example.com"
    response = client.post("/auth/register", json={"email": email, "password": "SecurePassword123", "name": "Goal API", "age": 25, "height": 180, "weight": 80, "target_weight": 80, "gender": "mężczyzna", "goal": "performance", "frequency": "3", "diet": "balanced"})
    assert response.status_code == 200, response.text
    return response.json()["access_token"], email

def _headers(token):
    return {"Authorization": f"Bearer {token}"}

def _completed_session(email: str, day: date, weight: float, reps: int = 5):
    with Session(engine) as db:
        user = db.exec(select(UserDB).where(UserDB.email == email)).first()
        assert user is not None
        training = TrainingSessionDB(user_id=user.id, session_date=day, status="completed", planned_snapshot_json=json.dumps({"exercises": [{"sets": 1, "reps": reps, "weight_kg": weight, "name": "Przysiad"}]}), started_at=datetime.now(), completed_at=datetime.now())
        db.add(training); db.commit(); db.refresh(training)
        db.add(TrainingSetResultDB(session_id=training.id, user_id=user.id, exercise_key="squat", exercise_name="Przysiad", set_number=1, planned_reps=reps, planned_weight_kg=weight, actual_reps=reps, actual_weight_kg=weight, actual_rpe=7, completed=True))
        db.commit()

def test_goal_crud_is_authenticated_and_user_scoped():
    token, _ = _user_context()
    other_token, _ = _user_context()
    created = client.post("/app/goals", headers=_headers(token), json={"goal_type": "strength", "title": "Przysiad 120 kg", "metric_key": "best_weight_kg", "baseline_value": 100, "target_value": 120, "metadata": {"exercise_key": "squat"}})
    assert created.status_code == 200, created.text
    goal_id = created.json()["id"]
    assert client.get(f"/app/goals/{goal_id}", headers=_headers(other_token)).status_code == 404
    assert client.get("/app/goals", headers=_headers(token)).json()["count"] == 1
    updated = client.patch(f"/app/goals/{goal_id}", headers=_headers(token), json={"priority": 90})
    assert updated.status_code == 200
    assert updated.json()["priority"] == 90
    archived = client.delete(f"/app/goals/{goal_id}", headers=_headers(token))
    assert archived.status_code == 200
    assert archived.json()["goal"]["status"] == "archived"

def test_goal_api_rejects_invalid_metric_dates_and_values():
    token, _ = _user_context()
    assert client.post("/app/goals", headers=_headers(token), json={"goal_type": "strength", "title": "Test", "metric_key": "unknown", "target_value": 1}).status_code == 422
    assert client.post("/app/goals", headers=_headers(token), json={"goal_type": "strength", "title": "Test", "metric_key": "best_weight_kg"}).status_code == 422
    assert client.post("/app/goals", headers=_headers(token), json={"goal_type": "strength", "title": "Test", "start_date": "2026-10-10", "target_date": "2026-10-01"}).status_code == 422

def test_goal_progress_uses_only_completed_owned_execution():
    token, email = _user_context()
    _, other_email = _user_context()
    today = date.today()
    _completed_session(email, today - timedelta(days=2), 100, 5)
    _completed_session(email, today - timedelta(days=1), 110, 5)
    _completed_session(other_email, today, 999, 1)
    created = client.post("/app/goals", headers=_headers(token), json={"goal_type": "strength", "title": "Przysiad 120 kg", "metric_key": "best_weight_kg", "baseline_value": 100, "target_value": 120, "metadata": {"exercise_key": "squat"}})
    goal_id = created.json()["id"]
    progress = client.get(f"/app/goals/{goal_id}/progress", headers=_headers(token))
    assert progress.status_code == 200, progress.text
    data = progress.json()
    assert data["current_value"] == 110
    assert data["progress_pct"] == 50.0
    assert data["remaining"] == 10.0
    assert len(data["history"]) == 2
    assert data["history"][-1]["value"] == 110

def test_goal_progress_supports_session_metric_and_reaches_target():
    token, email = _user_context()
    for offset in (3, 2, 1):
        _completed_session(email, date.today() - timedelta(days=offset), 100, 5)
    created = client.post("/app/goals", headers=_headers(token), json={"goal_type": "habit", "title": "3 treningi", "metric_key": "sessions", "baseline_value": 0, "target_value": 3})
    goal_id = created.json()["id"]
    progress = client.get(f"/app/goals/{goal_id}/progress", headers=_headers(token))
    assert progress.status_code == 200
    assert progress.json()["current_value"] == 3
    assert progress.json()["progress_pct"] == 100.0
    assert progress.json()["on_track"] is True

def test_goal_metrics_endpoint_is_explicit():
    token, _ = _user_context()
    response = client.get("/app/goals/metrics", headers=_headers(token))
    assert response.status_code == 200
    keys = {item["key"] for item in response.json()["metrics"]}
    assert {"best_weight_kg", "best_reps_at_best_weight", "total_volume_kg", "sessions", "training_days", "average_rpe"} <= keys


def test_goal_progress_matches_training_progress_records_and_ignores_invalid_execution():
    token, email = _user_context()
    today = date.today()
    _completed_session(email, today - timedelta(days=3), 100, 5)
    _completed_session(email, today - timedelta(days=2), 110, 5)
    _completed_session(email, today - timedelta(days=1), 120, 5)

    with Session(engine) as db:
        user = db.exec(select(UserDB).where(UserDB.email == email)).first()
        assert user is not None
        cancelled = TrainingSessionDB(
            user_id=user.id, session_date=today, status="cancelled",
            planned_snapshot_json=json.dumps({"exercises": [{"sets": 1, "reps": 5, "weight_kg": 999, "name": "Przysiad"}]}),
            started_at=datetime.now(), completed_at=datetime.now(),
        )
        db.add(cancelled)
        db.commit()
        db.refresh(cancelled)
        db.add(TrainingSetResultDB(
            session_id=cancelled.id, user_id=user.id, exercise_key="squat",
            exercise_name="Przysiad", set_number=1, planned_reps=5,
            planned_weight_kg=999, actual_reps=5, actual_weight_kg=999,
            actual_rpe=1, completed=True,
        ))
        db.commit()

    created = client.post("/app/goals", headers=_headers(token), json={
        "goal_type": "strength", "title": "Squat volume", "metric_key": "total_volume_kg",
        "baseline_value": 0, "target_value": 1650, "metadata": {"exercise_key": "squat"},
    })
    assert created.status_code == 200, created.text
    goal_id = created.json()["id"]

    goal_progress = client.get(f"/app/goals/{goal_id}/progress", headers=_headers(token))
    training_progress = client.get("/app/training/progress?limit=52", headers=_headers(token))
    assert goal_progress.status_code == training_progress.status_code == 200
    gp = goal_progress.json()
    tp = next(item for item in training_progress.json()["exercises"] if item["exercise_key"] == "squat")
    assert gp["current_value"] == tp["total_volume_kg"] == 1650.0
    assert gp["history"][-1]["value"] == 1650.0
    assert all(item["value"] <= 1650.0 for item in gp["history"])


def test_goal_best_metrics_are_cumulative_not_last_session_only():
    token, email = _user_context()
    today = date.today()
    _completed_session(email, today - timedelta(days=2), 120, 3)
    _completed_session(email, today - timedelta(days=1), 100, 10)
    created = client.post("/app/goals", headers=_headers(token), json={
        "goal_type": "strength", "title": "Squat record", "metric_key": "best_weight_kg",
        "baseline_value": 100, "target_value": 130, "metadata": {"exercise_key": "squat"},
    })
    goal_id = created.json()["id"]
    progress = client.get(f"/app/goals/{goal_id}/progress", headers=_headers(token))
    assert progress.status_code == 200
    data = progress.json()
    assert data["current_value"] == 120
    assert data["history"][-1]["value"] == 120
