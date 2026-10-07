from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlmodel import Session

from app.database import engine
from app.models import TrainingSessionDB, TrainingSetResultDB, UserDB
from app.training.history import list_completed_training_history


def _seed_user() -> UserDB:
    suffix = uuid.uuid4().hex[:10]
    user = UserDB(
        user_key=f"history:{suffix}",
        email=f"history-{suffix}@example.com",
        nickname=f"history_{suffix}",
        name="History Test",
        age=30,
        height=180.0,
        weight=82.0,
        start_weight=82.0,
        target_weight=78.0,
        gender="mężczyzna",
        goal="weight_loss",
        frequency="3-4 razy w tygodniu",
        diet="Balanced",
        calories_target=2200,
        protein_target=180,
    )
    with Session(engine) as db:
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def _completed_session(user: UserDB, session_date: date) -> TrainingSessionDB:
    training = TrainingSessionDB(
        user_id=user.id,
        session_date=session_date,
        status="completed",
        planned_snapshot_json='{"exercises": []}',
        started_at=datetime.now(),
        completed_at=datetime.now(),
        final_rpe=7,
    )
    with Session(engine) as db:
        db.add(training)
        db.commit()
        db.refresh(training)
    return training


def test_history_uses_canonical_execution_data_and_ignores_legacy_rows():
    user = _seed_user()
    training = _completed_session(user, date(2026, 10, 1))

    with Session(engine) as db:
        db.add(
            TrainingSetResultDB(
                session_id=training.id,
                user_id=user.id,
                exercise_key="squat",
                exercise_name="Squat",
                set_number=1,
                planned_reps=5,
                planned_weight_kg=100,
                actual_reps=5,
                actual_weight_kg=100,
                actual_rpe=7,
                completed=True,
            )
        )
        db.commit()

    history = list_completed_training_history(
        Session(engine),
        user.id,
        limit=20,
    )

    assert len(history) == 1
    item = history[0]
    assert item["session_id"] == training.id
    assert item["total_sets"] == 1
    assert item["completed_sets"] == 1
    assert item["completion_pct"] == 100.0
    assert item["exercises"][0]["exercise_key"] == "squat"
    assert item["exercises"][0]["sets"][0]["actual_weight_kg"] == 100


def test_history_excludes_active_sessions_and_is_user_scoped():
    user_a = _seed_user()
    user_b = _seed_user()
    completed_a = _completed_session(user_a, date(2026, 10, 2))

    active_a = TrainingSessionDB(
        user_id=user_a.id,
        session_date=date(2026, 10, 3),
        status="active",
        planned_snapshot_json='{"exercises": []}',
    )
    completed_b = _completed_session(user_b, date(2026, 10, 4))

    with Session(engine) as db:
        db.add(active_a)
        db.commit()

    history_a = list_completed_training_history(Session(engine), user_a.id)
    history_b = list_completed_training_history(Session(engine), user_b.id)

    assert [item["session_id"] for item in history_a] == [completed_a.id]
    assert [item["session_id"] for item in history_b] == [completed_b.id]


def test_history_is_deterministically_ordered_and_limit_is_bounded():
    user = _seed_user()
    older = _completed_session(user, date(2026, 10, 1))
    newer = _completed_session(user, date(2026, 10, 5))

    history = list_completed_training_history(Session(engine), user.id, limit=1)

    assert len(history) == 1
    assert history[0]["session_id"] == newer.id
    assert older.id != newer.id


def test_history_returns_empty_for_no_completed_sessions():
    user = _seed_user()
    assert list_completed_training_history(Session(engine), user.id) == []
