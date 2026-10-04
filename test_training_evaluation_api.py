from __future__ import annotations

import json
import uuid
from datetime import date

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.database import engine
from app.models import UserDB
from main import app


client = TestClient(app)


def _context():
    email = f"evaluation-{uuid.uuid4().hex[:10]}@example.com"
    nickname = f"evaluation_{uuid.uuid4().hex[:10]}"
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "SecurePassword123",
            "nickname": nickname,
            "name": "Evaluation Test",
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
    assert response.status_code == 200
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

    return {"token": token}


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def _start_and_log(ctx, *, reps=5, rpe=7, count=3):
    started = client.post(
        "/app/training/sessions/start",
        headers=_headers(ctx["token"]),
    )
    assert started.status_code == 200
    sid = started.json()["session"]["id"]
    for number in range(1, count + 1):
        response = client.post(
            f"/app/training/sessions/{sid}/sets",
            json={
                "exercise_key": "squat-1",
                "set_number": number,
                "actual_reps": reps,
                "actual_weight_kg": 100,
                "actual_rpe": rpe,
            },
            headers=_headers(ctx["token"]),
        )
        assert response.status_code == 200
    completed = client.post(
        f"/app/training/sessions/{sid}/complete",
        json={"final_rpe": rpe},
        headers=_headers(ctx["token"]),
    )
    assert completed.status_code == 200
    return sid


def test_evaluation_endpoint_returns_deterministic_result():
    ctx = _context()
    sid = _start_and_log(ctx)

    response = client.get(
        f"/app/training/sessions/{sid}/evaluation",
        headers=_headers(ctx["token"]),
    )
    assert response.status_code == 200
    data = response.json()["evaluation"]
    assert data["overall_decision"] == "progress"
    assert data["summary"]["progress"] == 1
    assert data["rules"]["mutates_plan"] is False


def test_evaluation_endpoint_requires_completed_session():
    ctx = _context()
    started = client.post(
        "/app/training/sessions/start",
        headers=_headers(ctx["token"]),
    )
    sid = started.json()["session"]["id"]

    response = client.get(
        f"/app/training/sessions/{sid}/evaluation",
        headers=_headers(ctx["token"]),
    )
    assert response.status_code == 409


def test_evaluation_endpoint_is_user_scoped():
    first = _context()
    second = _context()
    sid = _start_and_log(first)

    response = client.get(
        f"/app/training/sessions/{sid}/evaluation",
        headers=_headers(second["token"]),
    )
    assert response.status_code == 404


def test_evaluation_high_rpe_is_maintain():
    ctx = _context()
    sid = _start_and_log(ctx, rpe=9)

    response = client.get(
        f"/app/training/sessions/{sid}/evaluation",
        headers=_headers(ctx["token"]),
    )
    assert response.status_code == 200
    assert response.json()["evaluation"]["overall_decision"] == "maintain"
