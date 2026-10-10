from __future__ import annotations

import uuid
from datetime import date, datetime

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.auth import routes as auth_routes
from app.database import engine
from app.models import GoalDB, NutritionEntryDB, TrainingSessionDB, TrainingSetResultDB, UserDB
from main import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def _disable_registration_rate_limit():
    previous = auth_routes.limiter.enabled
    auth_routes.limiter.enabled = False
    yield
    auth_routes.limiter.enabled = previous


def _register(prefix: str):
    suffix = uuid.uuid4().hex[:10]
    response = client.post("/auth/register", json={
        "email": f"{prefix}-{suffix}@example.com",
        "password": "SecurePassword123",
        "nickname": f"{prefix}_{suffix}",
        "name": prefix,
        "age": 25,
        "height": 180,
        "weight": 80,
        "target_weight": 80,
        "gender": "mężczyzna",
        "goal": "performance",
        "frequency": "3",
        "diet": "balanced",
    })
    assert response.status_code == 200, response.text
    return response.json()["access_token"], suffix


def _headers(token: str):
    return {"Authorization": f"Bearer {token}"}


def test_stage_0_5_cross_user_resources_are_isolated():
    owner, suffix = _register("owner")
    other, _ = _register("other")

    owner_profile = client.get("/app/profile", headers=_headers(owner))
    assert owner_profile.status_code == 200

    # Assessment/plan resources are user-scoped even when another user's IDs or state exist.
    assessment = client.post("/app/assessment", headers=_headers(owner), json={
        "training_level": "intermediate",
        "training_experience_years": 2,
        "sessions_per_week": 3,
        "availability_hours_per_week": 5,
        "recovery_score": 7,
        "basketball_level": "amateur",
    })
    assert assessment.status_code in {200, 201}
    assessment_id = assessment.json().get("id")
    if assessment_id:
        assert client.get(f"/app/assessment/history/{assessment_id}", headers=_headers(other)).status_code in {404, 405}

    # Create a concrete training session/set owned by the first account.
    with Session(engine) as db:
        owner_row = db.exec(select(UserDB).where(UserDB.email.like(f"owner-{suffix}@example.com"))).first()
        assert owner_row is not None
        session_row = TrainingSessionDB(
            user_id=owner_row.id,
            session_date=date.today(),
            status="active",
            planned_snapshot_json='{"exercises":[{"id":"squat-1","name":"Przysiad","sets":1,"reps":5,"weight_kg":100}]}',
            started_at=datetime.now(),
        )
        db.add(session_row)
        db.commit()
        db.refresh(session_row)
        set_row = TrainingSetResultDB(
            session_id=session_row.id,
            user_id=owner_row.id,
            exercise_key="squat-1",
            exercise_name="Przysiad",
            set_number=1,
            planned_reps=5,
            planned_weight_kg=100,
            actual_reps=5,
            actual_weight_kg=100,
            completed=True,
        )
        db.add(set_row)
        db.commit()
        session_id = session_row.id

    assert client.get(f"/app/training/sessions/{session_id}", headers=_headers(other)).status_code == 404
    assert client.post(
        f"/app/training/sessions/{session_id}/sets",
        headers=_headers(other),
        json={"exercise_key":"squat-1","set_number":1,"actual_reps":1,"actual_weight_kg":1,"completed":True},
    ).status_code == 404
    assert client.post(
        f"/app/training/sessions/{session_id}/complete",
        headers=_headers(other),
        json={"final_rpe":5},
    ).status_code == 404

    # Goal ID cannot be read/changed/archived by another account.
    created_goal = client.post("/app/goals", headers=_headers(owner), json={
        "goal_type": "strength",
        "title": "Owner squat",
        "metric_key": "best_weight_kg",
        "baseline_value": 100,
        "target_value": 120,
        "metadata": {"exercise_key":"squat-1"},
    })
    assert created_goal.status_code == 200, created_goal.text
    goal_id = created_goal.json()["id"]
    assert client.get(f"/app/goals/{goal_id}", headers=_headers(other)).status_code == 404
    assert client.get(f"/app/goals/{goal_id}/progress", headers=_headers(other)).status_code == 404
    assert client.patch(f"/app/goals/{goal_id}", headers=_headers(other), json={"title":"stolen"}).status_code == 404
    assert client.delete(f"/app/goals/{goal_id}", headers=_headers(other)).status_code == 404

    # Nutrition entry ID cannot be read/deleted by another account.
    created_entry = client.post("/app/nutrition/entries", headers=_headers(owner), json={
        "name":"Owner meal","calories_kcal":500,"protein_g":30
    })
    assert created_entry.status_code == 201, created_entry.text
    entry_id = created_entry.json()["id"]
    assert client.delete(f"/app/nutrition/entries/{entry_id}", headers=_headers(other)).status_code == 404

    other_today = client.get("/app/nutrition/today", headers=_headers(other))
    assert other_today.status_code == 200
    assert all(item["id"] != entry_id for item in other_today.json().get("entries", []))
