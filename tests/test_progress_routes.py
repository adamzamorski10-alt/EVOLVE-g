from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlmodel import Session

from app.database import engine
from app.models import TrainingSessionDB, TrainingSetResultDB, UserDB
from app.training.progress_routes import get_progress_changes, get_progress_evidence


def _user() -> UserDB:
    suffix = uuid.uuid4().hex[:10]
    user = UserDB(user_key=f"progress-api:{suffix}", email=f"progress-api-{suffix}@example.com", nickname=f"progress_{suffix}", name="Progress API", age=30, height=180.0, weight=80.0, start_weight=80.0, target_weight=78.0, gender="mężczyzna", goal="weight_loss", frequency="3-4 razy w tygodniu", diet="Balanced", calories_target=2200, protein_target=180)
    with Session(engine) as db:
        db.add(user); db.commit(); db.refresh(user)
    return user


def _session(user: UserDB, when: date, weight: float) -> TrainingSessionDB:
    row = TrainingSessionDB(user_id=user.id, session_date=when, status="completed", planned_snapshot_json="{\"exercises\": []}", started_at=datetime.now(), completed_at=datetime.now(), final_rpe=7)
    with Session(engine) as db:
        db.add(row); db.commit(); db.refresh(row)
        db.add(TrainingSetResultDB(session_id=row.id, user_id=user.id, exercise_key="squat", exercise_name="Squat", set_number=1, planned_reps=5, planned_weight_kg=weight, actual_reps=5, actual_weight_kg=weight, actual_rpe=7, completed=True)); db.commit()
    return row


def test_progress_api_is_user_scoped_and_read_only():
    user_a, user_b = _user(), _user()
    _session(user_a, date(2026, 10, 1), 100)
    _session(user_a, date(2026, 10, 5), 105)
    _session(user_b, date(2026, 10, 6), 200)
    with Session(engine) as db:
        evidence = get_progress_evidence("squat", limit=12, user=user_a, session=db)
        changes = get_progress_changes("squat", limit=12, user=user_a, session=db)
    assert evidence["exercise_key"] == "squat"
    assert evidence["changes"]["average_weight_kg_delta"] == 5.0
    assert changes["status"] == "sufficient"
    assert changes["changes"][0]["delta"] == 5.0

    with Session(engine) as db:
        foreign = get_progress_evidence("squat", limit=12, user=user_b, session=db)
    assert foreign["changes"] == {}
    assert foreign["status"] == "insufficient_data"