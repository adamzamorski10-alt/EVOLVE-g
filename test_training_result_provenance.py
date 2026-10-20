from __future__ import annotations

import json
import uuid
from datetime import date

from sqlmodel import Session, select

from app.auth import routes as auth_routes
from app.database import engine
from app.models import ExerciseResultDB, UserDB
from main import app
from fastapi.testclient import TestClient

from test_training_execution import _context, _headers

client = TestClient(app)


def test_each_completed_session_materializes_its_own_provenance_bound_result():
    previous = auth_routes.limiter.enabled
    auth_routes.limiter.enabled = False
    try:
        ctx = _context()
        session_ids = []
        for _ in range(2):
            started = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
            assert started.status_code == 200
            sid = started.json()["session"]["id"]
            session_ids.append(sid)
            logged = client.post(
                f"/app/training/sessions/{sid}/sets",
                json={
                    "exercise_key": "squat-1",
                    "set_number": 1,
                    "actual_reps": 5,
                    "actual_weight_kg": 105,
                    "actual_rpe": 8,
                },
                headers=_headers(ctx["token"]),
            )
            assert logged.status_code == 200
            completed = client.post(
                f"/app/training/sessions/{sid}/complete",
                json={"final_rpe": 8},
                headers=_headers(ctx["token"]),
            )
            assert completed.status_code == 200

        with Session(engine) as db:
            user = db.exec(select(UserDB).where(UserDB.email == ctx["email"])).first()
            results = db.exec(
                select(ExerciseResultDB)
                .where(ExerciseResultDB.user_id == user.id)
                .where(ExerciseResultDB.source_exercise_key == "squat-1")
            ).all()
            assert len(results) == 2
            assert {result.source_session_id for result in results} == set(session_ids)
            assert all(result.exercise_name == "Przysiad" for result in results)
    finally:
        auth_routes.limiter.enabled = previous
