from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timedelta

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.auth import routes as auth_routes
from app.database import engine
from app.models import TrainingSessionDB, TrainingSetResultDB, UserDB
from main import app

client = TestClient(app)

def _headers(token):
    return {"Authorization": f"Bearer {token}"}

def _user_context():
    suffix = uuid.uuid4().hex[:10]
    email = f"goal-state-{suffix}@example.com"
    response = client.post("/auth/register", json={"email": email, "password": "SecurePassword123", "name": "Goal State", "age": 25, "height": 180, "weight": 80, "target_weight": 80, "gender": "mężczyzna", "goal": "performance", "frequency": "3", "diet": "balanced"})
    assert response.status_code == 200, response.text
    return response.json()["access_token"], email

def _completed_session(email: str, day: date, weight: float):
    with Session(engine) as db:
        user = db.exec(select(UserDB).where(UserDB.email == email)).first()
        training = TrainingSessionDB(user_id=user.id, session_date=day, status="completed", planned_snapshot_json=json.dumps({"exercises": []}), started_at=datetime.now(), completed_at=datetime.now())
        db.add(training); db.commit(); db.refresh(training)
        db.add(TrainingSetResultDB(session_id=training.id, user_id=user.id, exercise_key="squat", exercise_name="Squat", set_number=1, planned_reps=5, planned_weight_kg=weight, actual_reps=5, actual_weight_kg=weight, actual_rpe=7, completed=True))
        db.commit()

def test_goal_training_state_api_is_user_scoped_and_read_only():
    previous = auth_routes.limiter.enabled
    auth_routes.limiter.enabled = False
    try:
        token, email = _user_context()
        other_token, other_email = _user_context()
        today = date.today()
        _completed_session(email, today - timedelta(days=2), 100)
        _completed_session(email, today - timedelta(days=1), 110)
        _completed_session(other_email, today, 999)
        created = client.post("/app/goals", headers=_headers(token), json={"goal_type": "strength", "title": "Squat 120", "metric_key": "best_weight_kg", "baseline_value": 100, "target_value": 120, "metadata": {"exercise_key": "squat"}, "start_date": (today - timedelta(days=3)).isoformat()})
        assert created.status_code == 200, created.text
        goal_id = created.json()["id"]

        response = client.get(f"/app/goals/{goal_id}/training-state", headers=_headers(token))
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["current_value"] == 110
        assert data["progress_pct"] == 50.0
        assert data["supporting_session_ids"] and len(data["supporting_session_ids"]) == 2
        assert data["evidence_count"] == 2
        assert data["sufficient_data"] is True

        foreign = client.get(f"/app/goals/{goal_id}/training-state", headers=_headers(other_token))
        assert foreign.status_code == 404

        before = client.get(f"/app/goals/{goal_id}", headers=_headers(token)).json()
        client.get(f"/app/goals/{goal_id}/training-state", headers=_headers(token))
        after = client.get(f"/app/goals/{goal_id}", headers=_headers(token)).json()
        assert after["updated_at"] == before["updated_at"]
    finally:
        auth_routes.limiter.enabled = previous

def test_goal_training_state_api_reports_insufficient_evidence():
    previous = auth_routes.limiter.enabled
    auth_routes.limiter.enabled = False
    try:
        token, _ = _user_context()
        created = client.post("/app/goals", headers=_headers(token), json={"goal_type": "strength", "title": "No evidence", "metric_key": "best_weight_kg", "baseline_value": 100, "target_value": 120})
        goal_id = created.json()["id"]
        response = client.get(f"/app/goals/{goal_id}/training-state", headers=_headers(token))
        assert response.status_code == 200
        data = response.json()
        assert data["current_value"] is None
        assert data["progress_pct"] is None
        assert data["sufficient_data"] is False
        assert data["reason_codes"] == ["INSUFFICIENT_TRAINING_EVIDENCE"]
    finally:
        auth_routes.limiter.enabled = previous
