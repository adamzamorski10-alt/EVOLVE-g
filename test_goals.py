from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest
from sqlmodel import Session, select

from app.database import engine
from app.goals.service import (
    GOAL_STATUSES,
    GOAL_TYPES,
    create_goal,
    get_goal_for_user,
    list_goals_for_user,
    transition_goal,
)
from app.models import GoalDB, UserDB


def _user() -> UserDB:
    suffix = uuid.uuid4().hex[:12]
    return UserDB(
        user_key=f"goal-test:{suffix}",
        email=f"{suffix}@example.com",
        nickname=f"goal_{suffix}",
        name="Goal Test",
        age=25,
        height=180,
        weight=80,
        start_weight=80,
        target_weight=80,
        goal="performance",
        frequency="3",
        diet="balanced",
    )


def test_goal_model_is_user_owned_and_lifecycle_is_deterministic():
    first, second = _user(), _user()
    with Session(engine) as db:
        db.add(first)
        db.add(second)
        db.commit()
        db.refresh(first)
        db.refresh(second)

        goal = create_goal(
            db,
            first,
            goal_type="strength",
            title="Przysiad",
            target_date=date.today() + timedelta(days=30),
            priority=80,
            metadata={"metric": "best_weight_kg"},
        )

        assert goal.user_id == first.id
        assert goal.status == "active"
        assert goal.metadata_dict() == {"metric": "best_weight_kg"}
        assert get_goal_for_user(db, first, goal.id) is not None
        assert get_goal_for_user(db, second, goal.id) is None
        assert list_goals_for_user(db, second) == []

        completed = transition_goal(db, first, goal.id, "completed")
        assert completed.status == "completed"
        assert completed.completed_at is not None

        archived = transition_goal(db, first, goal.id, "archived")
        assert archived.status == "archived"
        assert archived.archived_at is not None


def test_goal_lifecycle_rejects_invalid_transition_and_invalid_type():
    user = _user()
    with Session(engine) as db:
        db.add(user)
        db.commit()
        db.refresh(user)

        with pytest.raises(ValueError):
            create_goal(db, user, goal_type="unknown", title="Test")

        goal = create_goal(db, user, goal_type="habit", title="Regularność")
        transition_goal(db, user, goal.id, "cancelled")

        with pytest.raises(ValueError):
            transition_goal(db, user, goal.id, "completed")

        with pytest.raises(ValueError):
            transition_goal(db, user, goal.id, "invalid")


def test_goal_date_and_priority_validation():
    user = _user()
    with Session(engine) as db:
        db.add(user)
        db.commit()
        db.refresh(user)

        with pytest.raises(ValueError):
            create_goal(
                db,
                user,
                goal_type="custom",
                title="Invalid",
                start_date=date.today(),
                target_date=date.today() - timedelta(days=1),
            )

        with pytest.raises(ValueError):
            create_goal(db, user, goal_type="custom", title="Invalid", priority=101)


def test_goal_status_and_type_sets_are_explicit():
    assert "active" in GOAL_STATUSES
    assert "completed" in GOAL_STATUSES
    assert "archived" in GOAL_STATUSES
    assert "performance" in GOAL_TYPES
    assert "basketball" in GOAL_TYPES
