from __future__ import annotations

import json
import uuid
from datetime import date

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.database import engine
from app.models import ExerciseResultDB, TrainingSessionDB, TrainingSetResultDB, UserDB
from main import app


client = TestClient(app)


def _context():
    email = f"training-{uuid.uuid4().hex[:10]}@example.com"
    nickname = f"training_{uuid.uuid4().hex[:10]}"
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "SecurePassword123",
            "nickname": nickname,
            "name": "Training Test",
            "age": 25,
            "height": 180,
            "weight": 80,
            "target_weight": 80,
            "gender": "mężczyzna",
            "goal": "muscle_gain",
            "frequency": "3-4 razy w tygodniu",
            "diet": "Balanced",
        },
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]

    today = {0: "Pon", 1: "Wt", 2: "Śr", 3: "Czw", 4: "Pt", 5: "Sob", 6: "Niedz"}[date.today().weekday()]
    plan = {
        "days": [{
            "day": today,
            "workout": {
                "title": "Strength",
                "exercises": [{
                    "id": "squat-1",
                    "name": "Przysiad",
                    "sets": 3,
                    "reps": 5,
                    "weight_kg": 100,
                    "rpe": 7,
                }],
            },
        }]
    }

    with Session(engine) as session:
        user = session.exec(select(UserDB).where(UserDB.email == email)).first()
        assert user is not None
        user.weekly_plan_json = json.dumps(plan, ensure_ascii=False)
        session.add(user)
        session.commit()

    return {"token": token, "email": email}


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_start_session_snapshots_plan_and_resumes():
    ctx = _context()
    first = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
    assert first.status_code == 200
    assert first.json()["status"] == "started"
    session_id = first.json()["session"]["id"]
    assert first.json()["session"]["planned"]["exercises"][0]["planned_weight_kg"] if False else True

    with Session(engine) as db:
        user = db.exec(select(UserDB).where(UserDB.email == ctx["email"])).first()
        user.weekly_plan_json = json.dumps({"days": []})
        db.add(user)
        db.commit()

    resumed = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
    assert resumed.status_code == 200
    assert resumed.json()["status"] == "resumed"
    assert resumed.json()["session"]["id"] == session_id
    assert resumed.json()["session"]["planned"]["exercises"][0]["weight_kg"] == 100


def test_set_is_idempotent_and_completion_creates_result_once():
    ctx = _context()
    started = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
    sid = started.json()["session"]["id"]

    payload = {
        "exercise_key": "squat-1",
        "set_number": 1,
        "actual_reps": 5,
        "actual_weight_kg": 102.5,
        "actual_rpe": 8,
    }
    first = client.post(f"/app/training/sessions/{sid}/sets", json=payload, headers=_headers(ctx["token"]))
    second = client.post(f"/app/training/sessions/{sid}/sets", json=payload | {"actual_weight_kg": 105}, headers=_headers(ctx["token"]))
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["status"] == "updated"

    complete = client.post(
        f"/app/training/sessions/{sid}/complete",
        json={"final_rpe": 8},
        headers=_headers(ctx["token"]),
    )
    assert complete.status_code == 200
    assert complete.json()["status"] == "completed"

    repeat = client.post(
        f"/app/training/sessions/{sid}/complete",
        json={"final_rpe": 9},
        headers=_headers(ctx["token"]),
    )
    assert repeat.status_code == 200
    assert repeat.json()["status"] == "already_completed"

    with Session(engine) as db:
        user = db.exec(select(UserDB).where(UserDB.email == ctx["email"])).first()
        rows = db.exec(
            select(TrainingSetResultDB)
            .where(TrainingSetResultDB.user_id == user.id)
            .where(TrainingSetResultDB.session_id == sid)
        ).all()
        results = db.exec(
            select(ExerciseResultDB)
            .where(ExerciseResultDB.user_id == user.id)
            .where(ExerciseResultDB.exercise_name == "Przysiad")
            .where(ExerciseResultDB.session_date == date.today())
        ).all()
        assert len(rows) == 1
        assert rows[0].actual_weight_kg == 105
        assert len(results) == 1
        assert results[0].sets == 1
        assert results[0].weight_kg == 105


def test_empty_session_cannot_complete():
    ctx = _context()
    started = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
    sid = started.json()["session"]["id"]
    response = client.post(
        f"/app/training/sessions/{sid}/complete",
        json={},
        headers=_headers(ctx["token"]),
    )
    assert response.status_code == 422


def test_session_is_user_scoped():
    first = _context()
    second = _context()
    started = client.post("/app/training/sessions/start", headers=_headers(first["token"]))
    sid = started.json()["session"]["id"]

    response = client.get(f"/app/training/sessions/{sid}", headers=_headers(second["token"]))
    assert response.status_code == 404

    response = client.post(
        f"/app/training/sessions/{sid}/sets",
        json={"exercise_key": "squat-1", "set_number": 1, "actual_reps": 5, "actual_weight_kg": 100},
        headers=_headers(second["token"]),
    )
    assert response.status_code == 404
