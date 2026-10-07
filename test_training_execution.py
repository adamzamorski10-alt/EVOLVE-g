from __future__ import annotations

import json
import uuid

import pytest
from datetime import date

from app.auth import routes as auth_routes

from fastapi.testclient import TestClient
from sqlmodel import Session, select, delete

from app.database import engine
from app.models import DailyLogDB, ExerciseResultDB, TrainingSessionDB, TrainingSetResultDB, UserDB
from main import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def _isolate_training_data():
    with Session(engine) as db:
        db.exec(delete(TrainingSetResultDB))
        db.exec(delete(ExerciseResultDB))
        db.exec(delete(TrainingSessionDB))
        db.commit()
    yield

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


def _log_set(token, session_id, set_number, reps=5, weight=100, rpe=7):
    return client.post(
        f"/app/training/sessions/{session_id}/sets",
        json={
            "exercise_key": "squat-1",
            "set_number": set_number,
            "actual_reps": reps,
            "actual_weight_kg": weight,
            "actual_rpe": rpe,
            "completed": True,
        },
        headers=_headers(token),
    )


def test_start_session_snapshots_plan_and_resumes():
    ctx = _context()
    first = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
    assert first.status_code == 200
    assert first.json()["status"] == "started"
    session_id = first.json()["session"]["id"]
    assert first.json()["session"]["planned"]["exercises"][0]["weight_kg"] == 100

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



def test_effective_plan_rejects_adaptation_derived_from_stale_base():
    ctx = _context()
    started = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
    assert started.status_code == 200
    original_plan = started.json()["session"]["planned"]

    with Session(engine) as db:
        user = db.exec(select(UserDB).where(UserDB.email == ctx["email"])).first()
        base = json.loads(user.weekly_plan_json)
        adapted = json.loads(json.dumps(base))
        adapted["_evolve_adaptation"] = {
            "base_plan_fingerprint": "stale-fingerprint",
            "source_session_ids": [started.json()["session"]["id"]],
            "algorithm": "deterministic-v1",
        }
        from app.models import AdaptivePlanRevisionDB
        db.add(
            AdaptivePlanRevisionDB(
                user_id=user.id,
                source_session_ids_json=json.dumps([started.json()["session"]["id"]]),
                previous_plan_json=json.dumps(base),
                applied_plan_json=json.dumps(adapted),
                decision_summary_json=json.dumps({"progress": 1}),
                version=1,
            )
        )
        base["days"][0]["workout"]["exercises"][0]["weight_kg"] = 999
        user.weekly_plan_json = json.dumps(base, ensure_ascii=False)
        db.add(user)
        db.commit()

    today = client.get("/app/training/today", headers=_headers(ctx["token"]))
    assert today.status_code == 200
    assert today.json()["plan"]["source"] == "base"
    assert today.json()["exercises"][0]["weight_kg"] == 999
    assert original_plan["exercises"][0]["weight_kg"] == 100



def test_uncompleted_sets_do_not_materialize_into_exercise_result():
    ctx = _context()
    started = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
    assert started.status_code == 200
    sid = started.json()["session"]["id"]

    response = client.post(
        f"/app/training/sessions/{sid}/sets",
        json={
            "exercise_key": "squat-1",
            "set_number": 1,
            "actual_reps": 5,
            "actual_weight_kg": 105,
            "actual_rpe": 8,
            "completed": False,
        },
        headers=_headers(ctx["token"]),
    )
    assert response.status_code == 200

    completed = client.post(
        f"/app/training/sessions/{sid}/complete",
        json={"final_rpe": 8},
        headers=_headers(ctx["token"]),
    )
    assert completed.status_code == 422

    with Session(engine) as db:
        user = db.exec(select(UserDB).where(UserDB.email == ctx["email"])).first()
        results = db.exec(
            select(ExerciseResultDB)
            .where(ExerciseResultDB.user_id == user.id)
            .where(ExerciseResultDB.session_date == date.today())
        ).all()
        assert results == []


def test_partial_completion_materializes_only_completed_sets():
    ctx = _context()
    started = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
    sid = started.json()["session"]["id"]

    assert client.post(
        f"/app/training/sessions/{sid}/sets",
        json={"exercise_key":"squat-1","set_number":1,"actual_reps":5,"actual_weight_kg":105,"actual_rpe":8,"completed":True},
        headers=_headers(ctx["token"]),
    ).status_code == 200
    assert client.post(
        f"/app/training/sessions/{sid}/sets",
        json={"exercise_key":"squat-1","set_number":2,"actual_reps":2,"actual_weight_kg":80,"actual_rpe":9,"completed":False},
        headers=_headers(ctx["token"]),
    ).status_code == 200

    completed = client.post(
        f"/app/training/sessions/{sid}/complete",
        json={"final_rpe":8},
        headers=_headers(ctx["token"]),
    )
    assert completed.status_code == 200

    with Session(engine) as db:
        user = db.exec(select(UserDB).where(UserDB.email == ctx["email"])).first()
        results = db.exec(
            select(ExerciseResultDB)
            .where(ExerciseResultDB.user_id == user.id)
            .where(ExerciseResultDB.source_session_id == sid)
        ).all()
        assert len(results) == 1
        assert results[0].sets == 1
        assert results[0].reps == 5
        assert results[0].weight_kg == 105


def test_progress_aggregates_only_completed_owned_execution_data():
    first = _context()
    second = _context()
    started = client.post("/app/training/sessions/start", headers=_headers(first["token"]))
    assert started.status_code == 200
    sid = started.json()["session"]["id"]
    for number in (1, 2, 3):
        assert _log_set(first["token"], sid, number, reps=5, weight=100, rpe=7).status_code == 200
    assert client.post(
        f"/app/training/sessions/{sid}/complete",
        json={"final_rpe": 7},
        headers=_headers(first["token"]),
    ).status_code == 200

    own = client.get("/app/training/progress", headers=_headers(first["token"]))
    foreign = client.get("/app/training/progress", headers=_headers(second["token"]))
    assert own.status_code == 200
    assert own.json()["period_sessions"] == 1
    assert own.json()["total_completed_sets"] == 3
    assert own.json()["total_volume_kg"] == 1500
    assert own.json()["exercises"][0]["best_weight_kg"] == 100
    assert foreign.status_code == 200
    assert foreign.json()["period_sessions"] == 0
    assert foreign.json()["total_completed_sets"] == 0


def test_progress_endpoint_ignores_incomplete_sets():
    ctx = _context()
    started = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
    sid = started.json()["session"]["id"]
    assert _log_set(ctx["token"], sid, 1, reps=5, weight=100, rpe=7).status_code == 200
    assert client.post(
        f"/app/training/sessions/{sid}/sets",
        json={"exercise_key":"squat-1","set_number":2,"actual_reps":20,"actual_weight_kg":200,"actual_rpe":10,"completed":False},
        headers=_headers(ctx["token"]),
    ).status_code == 200
    assert client.post(
        f"/app/training/sessions/{sid}/complete",
        json={"final_rpe": 7},
        headers=_headers(ctx["token"]),
    ).status_code == 200
    progress = client.get("/app/training/progress", headers=_headers(ctx["token"]))
    assert progress.status_code == 200
    assert progress.json()["total_completed_sets"] == 1
    assert progress.json()["total_volume_kg"] == 500


def test_progress_excludes_active_and_cancelled_sessions():
    ctx = _context()

    active = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
    assert active.status_code == 200
    active_id = active.json()["session"]["id"]
    assert _log_set(ctx["token"], active_id, 1, reps=5, weight=100, rpe=7).status_code == 200

    with Session(engine) as db:
        cancelled_row = TrainingSessionDB(
            user_id=db.exec(select(UserDB).where(UserDB.email == ctx["email"])).first().id,
            session_date=date.today(),
            status="cancelled",
            planned_snapshot_json=json.dumps({"exercises": []}),
        )
        db.add(cancelled_row)
        db.commit()

    progress = client.get("/app/training/progress?limit=52", headers=_headers(ctx["token"]))
    assert progress.status_code == 200
    assert progress.json()["period_sessions"] == 0
    assert progress.json()["total_completed_sets"] == 0
    assert progress.json()["exercises"] == []


def test_progress_limit_is_bounded():
    ctx = _context()
    response = client.get("/app/training/progress?limit=9999", headers=_headers(ctx["token"]))
    assert response.status_code == 200
    assert response.json()["limit"] == 52
    assert len(response.json()["sessions"]) <= 52

    response = client.get("/app/training/progress?limit=0", headers=_headers(ctx["token"]))
    assert response.status_code == 200
    assert response.json()["limit"] == 1


def test_exercise_progress_is_completed_and_user_scoped():
    first = _context()
    second = _context()

    started = client.post("/app/training/sessions/start", headers=_headers(first["token"]))
    sid = started.json()["session"]["id"]
    logged = client.post(
        f"/app/training/sessions/{sid}/sets",
        json={"exercise_key": "squat-1", "set_number": 1, "actual_reps": 5, "actual_weight_kg": 110, "actual_rpe": 8},
        headers=_headers(first["token"]),
    )
    assert logged.status_code == 200
    completed = client.post(
        f"/app/training/sessions/{sid}/complete",
        json={"final_rpe": 8},
        headers=_headers(first["token"]),
    )
    assert completed.status_code == 200

    own = client.get("/app/training/progress/exercises/squat-1", headers=_headers(first["token"]))
    assert own.status_code == 200
    data = own.json()
    assert data["exercise_name"] == "Przysiad"
    assert data["sessions"] == 1
    assert data["best_weight_kg"] == 110
    assert data["best_reps_at_best_weight"] == 5
    assert data["total_volume_kg"] == 550
    assert len(data["history"]) == 1

    other = client.get("/app/training/progress/exercises/squat-1", headers=_headers(second["token"]))
    assert other.status_code == 200
    assert other.json()["sessions"] == 0
    assert other.json()["history"] == []


def test_training_trends_are_deterministic_and_completed_only():
    ctx = _context()
    first = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
    sid1 = first.json()["session"]["id"]
    assert _log_set(ctx["token"], sid1, 1, reps=5, weight=100, rpe=7).status_code == 200
    assert client.post(f"/app/training/sessions/{sid1}/complete", json={"final_rpe": 7}, headers=_headers(ctx["token"])).status_code == 200

    second = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
    sid2 = second.json()["session"]["id"]
    assert _log_set(ctx["token"], sid2, 1, reps=5, weight=120, rpe=7).status_code == 200
    assert client.post(f"/app/training/sessions/{sid2}/complete", json={"final_rpe": 7}, headers=_headers(ctx["token"])).status_code == 200

    response = client.get("/app/training/progress/trends?limit=12", headers=_headers(ctx["token"]))
    assert response.status_code == 200
    exercise = next(item for item in response.json()["exercises"] if item["exercise_key"] == "squat-1")
    assert exercise["sessions"] == 2
    assert exercise["weight"]["trend"] == "up"
    assert exercise["weight"]["change_pct"] > 0
    assert exercise["history"][0]["best_weight_kg"] == 120
    assert exercise["history"][1]["best_weight_kg"] == 100


def test_training_records_are_user_scoped_and_completed_only():
    first = _context()
    second = _context()
    started = client.post("/app/training/sessions/start", headers=_headers(first["token"]))
    sid = started.json()["session"]["id"]
    assert _log_set(first["token"], sid, 1, reps=8, weight=130, rpe=8).status_code == 200
    assert _log_set(first["token"], sid, 2, reps=5, weight=140, rpe=9).status_code == 200
    assert client.post(f"/app/training/sessions/{sid}/complete", json={"final_rpe": 9}, headers=_headers(first["token"])).status_code == 200

    own = client.get("/app/training/progress/records", headers=_headers(first["token"]))
    assert own.status_code == 200
    exercise = next(item for item in own.json()["exercises"] if item["exercise_key"] == "squat-1")
    assert exercise["best_weight"]["value_kg"] == 140
    assert exercise["best_reps"]["value"] == 8
    assert exercise["best_session_volume"]["value_kg"] == 1740

    foreign = client.get("/app/training/progress/records", headers=_headers(second["token"]))
    assert foreign.status_code == 200
    assert foreign.json()["exercises"] == []


def test_consistency_endpoint_returns_only_completed_owned_sessions():
    ctx = _context()
    started = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
    sid = started.json()["session"]["id"]
    assert _log_set(ctx["token"], sid, 1, reps=5, weight=100, rpe=7).status_code == 200
    assert client.post(f"/app/training/sessions/{sid}/complete", json={"final_rpe": 7}, headers=_headers(ctx["token"])).status_code == 200
    response = client.get("/app/training/progress/consistency", headers=_headers(ctx["token"]))
    assert response.status_code == 200
    assert response.json()["sessions"] == 1
    assert response.json()["training_days"] == 1


def test_completed_session_history_detail_is_owned():
    ctx = _context()
    started = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
    sid = started.json()["session"]["id"]
    assert _log_set(ctx["token"], sid, 1, reps=5, weight=100, rpe=7).status_code == 200
    assert client.post(f"/app/training/sessions/{sid}/complete", json={"final_rpe": 7}, headers=_headers(ctx["token"])).status_code == 200
    response = client.get(f"/app/training/sessions/history/{sid}", headers=_headers(ctx["token"]))
    assert response.status_code == 200
    assert response.json()["id"] == sid
    assert len(response.json()["sets"]) == 1


def test_completion_rejects_empty_and_is_idempotent_and_user_scoped():
    first = _context()
    second = _context()
    started = client.post("/app/training/sessions/start", headers=_headers(first["token"]))
    sid = started.json()["session"]["id"]

    foreign = client.post(
        f"/app/training/sessions/{sid}/complete",
        json={"final_rpe": 7},
        headers=_headers(second["token"]),
    )
    assert foreign.status_code in (403, 404)

    empty = client.post(
        f"/app/training/sessions/{sid}/complete",
        json={"final_rpe": 7},
        headers=_headers(first["token"]),
    )
    assert empty.status_code == 422

    assert _log_set(first["token"], sid, 1, reps=5, weight=100, rpe=7).status_code == 200
    done = client.post(
        f"/app/training/sessions/{sid}/complete",
        json={"final_rpe": 7},
        headers=_headers(first["token"]),
    )
    assert done.status_code == 200
    repeat = client.post(
        f"/app/training/sessions/{sid}/complete",
        json={"final_rpe": 9},
        headers=_headers(first["token"]),
    )
    assert repeat.status_code == 200
    assert repeat.json()["status"] == "already_completed"
    assert repeat.json()["session"]["final_rpe"] == 7


def test_start_session_is_blocked_by_recovery_decision():
    ctx = _context()
    with Session(engine) as db:
        user = db.exec(select(UserDB).where(UserDB.email == ctx["email"])).first()
        assert user is not None
        log = db.exec(
            select(DailyLogDB)
            .where(DailyLogDB.user_id == user.id)
            .where(DailyLogDB.log_date == date.today())
        ).first()
        if log is None:
            log = DailyLogDB(user_id=user.id, log_date=date.today())
        log.sleep_hours = 4
        log.sleep_quality = 3
        log.energy_level = 3
        log.stress_level = 9
        db.add(log)
        db.commit()

    blocked = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
    assert blocked.status_code == 409
    detail = blocked.json()["detail"]
    assert detail["code"] == "TRAINING_START_BLOCKED"
    assert detail["decision"] == "recover"

    with Session(engine) as db:
        user = db.exec(select(UserDB).where(UserDB.email == ctx["email"])).first()
        assert user is not None
        active = db.exec(
            select(TrainingSessionDB)
            .where(TrainingSessionDB.user_id == user.id)
            .where(TrainingSessionDB.session_date == date.today())
            .where(TrainingSessionDB.status == "active")
        ).first()
        assert active is None


def _add_recovery_for_today(ctx):
    with Session(engine) as db:
        user = db.exec(select(UserDB).where(UserDB.email == ctx["email"])).first()
        assert user is not None
        log = db.exec(
            select(DailyLogDB)
            .where(DailyLogDB.user_id == user.id)
            .where(DailyLogDB.log_date == date.today())
        ).first()
        if log is None:
            log = DailyLogDB(user_id=user.id, log_date=date.today())
        log.sleep_hours = 4
        log.sleep_quality = 3
        log.energy_level = 3
        log.stress_level = 9
        db.add(log)
        db.commit()


def test_active_session_cannot_be_resumed_when_recovery_blocks_execution():
    ctx = _context()
    started = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
    assert started.status_code == 200
    sid = started.json()["session"]["id"]

    _add_recovery_for_today(ctx)
    blocked = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
    assert blocked.status_code == 409
    detail = blocked.json()["detail"]
    assert detail["code"] == "TRAINING_START_BLOCKED"
    assert detail["decision"] == "recover"

    with Session(engine) as db:
        user = db.exec(select(UserDB).where(UserDB.email == ctx["email"])).first()
        row = db.exec(select(TrainingSessionDB).where(TrainingSessionDB.id == sid).where(TrainingSessionDB.user_id == user.id)).first()
        assert row is not None
        assert row.status == "active"


def test_active_session_set_logging_is_blocked_when_recovery_blocks_execution():
    ctx = _context()
    started = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
    assert started.status_code == 200
    sid = started.json()["session"]["id"]

    _add_recovery_for_today(ctx)
    blocked = client.post(
        f"/app/training/sessions/{sid}/sets",
        json={"exercise_key": "squat-1", "set_number": 1, "actual_reps": 5, "actual_weight_kg": 100},
        headers=_headers(ctx["token"]),
    )
    assert blocked.status_code == 409
    detail = blocked.json()["detail"]
    assert detail["code"] == "TRAINING_EXECUTION_BLOCKED"
    assert detail["decision"] == "recover"

    with Session(engine) as db:
        user = db.exec(select(UserDB).where(UserDB.email == ctx["email"])).first()
        rows = db.exec(
            select(TrainingSetResultDB)
            .where(TrainingSetResultDB.user_id == user.id)
            .where(TrainingSetResultDB.session_id == sid)
        ).all()
        assert rows == []


def test_training_today_remains_readable_when_recovery_blocks_execution():
    ctx = _context()
    _add_recovery_for_today(ctx)
    response = client.get("/app/training/today", headers=_headers(ctx["token"]))
    assert response.status_code == 200
    assert response.json()["can_start"] is False


def test_malformed_training_decision_fails_closed():
    from app.decision_engine import training_execution_allowed

    assert training_execution_allowed({}) is True
    assert training_execution_allowed({"decision": "unknown"}) is False
    assert training_execution_allowed({"decision": "recover"}) is False
    assert training_execution_allowed({"decision": "insufficient_data"}) is True


def test_legacy_day_workout_logging_is_blocked_by_recovery():
    ctx = _context()
    added = client.post(
        "/app/day/item/add",
        json={
            "item_type": "workout",
            "name": "Przysiad",
            "sets": 3,
            "reps": 5,
            "weight_kg": 100,
        },
        headers=_headers(ctx["token"]),
    )
    assert added.status_code == 200, added.text
    item = next(item for item in added.json()["log"]["workouts"] if item["name"] == "Przysiad")

    _add_recovery_for_today(ctx)
    blocked = client.post(
        "/app/day/item/toggle",
        json={"item_id": item["item_id"], "item_type": "workout", "checked": True},
        headers=_headers(ctx["token"]),
    )
    assert blocked.status_code == 409
    assert blocked.json()["detail"]["code"] == "TRAINING_EXECUTION_BLOCKED"
    assert blocked.json()["detail"]["decision"] == "recover"


def test_active_session_completion_is_blocked_when_recovery_blocks_execution():
    ctx = _context()
    started = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
    assert started.status_code == 200
    sid = started.json()["session"]["id"]
    assert _log_set(ctx["token"], sid, 1).status_code == 200

    _add_recovery_for_today(ctx)
    blocked = client.post(
        f"/app/training/sessions/{sid}/complete",
        json={"final_rpe": 8},
        headers=_headers(ctx["token"]),
    )
    assert blocked.status_code == 409
    assert blocked.json()["detail"]["code"] == "TRAINING_EXECUTION_BLOCKED"
    assert blocked.json()["detail"]["decision"] == "recover"

    with Session(engine) as db:
        user = db.exec(select(UserDB).where(UserDB.email == ctx["email"])).first()
        row = db.exec(select(TrainingSessionDB).where(TrainingSessionDB.id == sid).where(TrainingSessionDB.user_id == user.id)).first()
        assert row is not None
        assert row.status == "active"
        results = db.exec(select(ExerciseResultDB).where(ExerciseResultDB.user_id == user.id).where(ExerciseResultDB.source_session_id == sid)).all()
        assert results == []


def test_completion_path_materializes_owned_result_when_execution_is_allowed():
    ctx = _context()
    started = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
    assert started.status_code == 200
    sid = started.json()["session"]["id"]
    assert _log_set(ctx["token"], sid, 1, reps=5, weight=105, rpe=8).status_code == 200
    completed = client.post(f"/app/training/sessions/{sid}/complete", json={"final_rpe": 8}, headers=_headers(ctx["token"]))
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"


def test_cross_user_session_read_analysis_progression_and_completion_are_blocked():
    owner = _context()
    attacker = _context()
    started = client.post("/app/training/sessions/start", headers=_headers(owner["token"]))
    assert started.status_code == 200
    sid = started.json()["session"]["id"]

    for path in (
        f"/app/training/sessions/{sid}",
        f"/app/training/sessions/history/{sid}",
        f"/app/training/sessions/{sid}/analysis",
        f"/app/training/sessions/{sid}/progression",
    ):
        response = client.get(path, headers=_headers(attacker["token"]))
        assert response.status_code == 404, path

    set_response = client.post(
        f"/app/training/sessions/{sid}/sets",
        json={"exercise_key": "squat-1", "set_number": 1, "actual_reps": 5, "actual_weight_kg": 100},
        headers=_headers(attacker["token"]),
    )
    assert set_response.status_code == 404

    complete_response = client.post(
        f"/app/training/sessions/{sid}/complete",
        json={"final_rpe": 8},
        headers=_headers(attacker["token"]),
    )
    assert complete_response.status_code == 404

    with Session(engine) as db:
        owner_user = db.exec(select(UserDB).where(UserDB.email == owner["email"])).first()
        row = db.exec(
            select(TrainingSessionDB)
            .where(TrainingSessionDB.id == sid)
            .where(TrainingSessionDB.user_id == owner_user.id)
        ).first()
        assert row is not None
        assert row.status == "active"
        assert db.exec(select(TrainingSetResultDB).where(TrainingSetResultDB.session_id == sid)).all() == []


def test_recovery_and_decision_are_user_scoped():
    first = _context()
    second = _context()

    with Session(engine) as db:
        first_user = db.exec(select(UserDB).where(UserDB.email == first["email"])).first()
        second_user = db.exec(select(UserDB).where(UserDB.email == second["email"])).first()
        db.add(DailyLogDB(
            user_id=first_user.id,
            log_date=date.today(),
            sleep_hours=4,
            sleep_quality=3,
            energy_level=3,
            stress_level=9,
        ))
        db.commit()

        from app.decision_service import decision_for_user
        from app.recovery.routes import recovery_for_date

        first_recovery = recovery_for_date(db, first_user.id, date.today())
        second_recovery = recovery_for_date(db, second_user.id, date.today())
        first_decision = decision_for_user(user=first_user, db=db)
        second_decision = decision_for_user(user=second_user, db=db)

    assert first_recovery["status"] == "recovery"
    assert second_recovery["status"] == "insufficient_data"
    assert first_decision["decision"] == "recover"
    assert second_decision["decision"] != "recover"


def test_unauthenticated_execution_and_session_reads_are_rejected():
    ctx = _context()
    started = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
    assert started.status_code == 200
    sid = started.json()["session"]["id"]

    assert client.get(f"/app/training/sessions/{sid}").status_code in {401, 403}
    assert client.post(f"/app/training/sessions/{sid}/sets", json={
        "exercise_key": "squat-1",
        "set_number": 1,
        "actual_reps": 5,
        "actual_weight_kg": 100,
    }).status_code in {401, 403}
    assert client.post(f"/app/training/sessions/{sid}/complete", json={}).status_code in {401, 403}




def test_legacy_exercise_result_is_blocked_by_recovery():
    owner = _context()
    _add_recovery_for_today(owner)
    response = client.post(
        "/app/exercise-result",
        json={"exercise_name": "Przysiad", "sets": 3, "reps": 5, "weight_kg": 100, "rpe": 7},
        headers=_headers(owner["token"]),
    )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "TRAINING_EXECUTION_BLOCKED"
    with Session(engine) as db:
        user = db.exec(select(UserDB).where(UserDB.email == owner["email"])).first()
        results = db.exec(select(ExerciseResultDB).where(ExerciseResultDB.user_id == user.id)).all()
        assert results == []

def test_legacy_day_item_is_user_scoped():
    owner = _context()
    attacker = _context()
    added = client.post(
        "/app/day/item/add",
        json={"item_type": "workout", "name": "Przysiad", "sets": 3, "reps": 5, "weight_kg": 100},
        headers=_headers(owner["token"]),
    )
    assert added.status_code == 200
    item = next(item for item in added.json()["log"]["workouts"] if item["name"] == "Przysiad")

    response = client.post(
        "/app/day/item/toggle",
        json={"item_id": item["item_id"], "item_type": "workout", "checked": True},
        headers=_headers(attacker["token"]),
    )
    assert response.status_code == 404

    with Session(engine) as db:
        attacker_user = db.exec(select(UserDB).where(UserDB.email == attacker["email"])).first()
        attacker_log = db.exec(
            select(DailyLogDB)
            .where(DailyLogDB.user_id == attacker_user.id)
            .where(DailyLogDB.log_date == date.today())
        ).first()
        assert attacker_log is None or item["item_id"] not in {
            str(value.get("item_id"))
            for value in attacker_log.get_workouts()
        }
