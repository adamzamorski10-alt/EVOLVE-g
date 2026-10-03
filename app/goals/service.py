"""Goal domain service foundation for Stage 3."""
from __future__ import annotations

import json
from datetime import date, datetime

from sqlmodel import Session, select

from app.models import GoalDB, UserDB

GOAL_TYPES = frozenset({
    "performance", "skill", "strength", "basketball",
    "body_composition", "habit", "custom",
})
GOAL_STATUSES = frozenset({"active", "completed", "cancelled", "archived"})

_ALLOWED_TRANSITIONS = {
    "active": {"completed", "cancelled", "archived"},
    "completed": {"archived"},
    "cancelled": {"archived"},
    "archived": set(),
}


def validate_goal_type(goal_type: str) -> str:
    value = str(goal_type or "").strip().lower()
    if value not in GOAL_TYPES:
        raise ValueError("Unsupported goal type")
    return value


def validate_goal_status(status: str) -> str:
    value = str(status or "").strip().lower()
    if value not in GOAL_STATUSES:
        raise ValueError("Unsupported goal status")
    return value


def create_goal(session: Session, user: UserDB, *, goal_type: str, title: str,
                description: str = "", start_date: date | None = None,
                target_date: date | None = None, priority: int = 0,
                metadata: dict | None = None) -> GoalDB:
    goal_type = validate_goal_type(goal_type)
    title = str(title or "").strip()
    if not title or len(title) > 200:
        raise ValueError("Goal title must contain 1-200 characters")
    start = start_date or date.today()
    if target_date is not None and target_date < start:
        raise ValueError("Goal target_date cannot precede start_date")
    if not 0 <= priority <= 100:
        raise ValueError("Goal priority must be between 0 and 100")

    row = GoalDB(
        user_id=user.id,
        goal_type=goal_type,
        title=title,
        description=str(description or ""),
        start_date=start,
        target_date=target_date,
        priority=priority,
        metadata_json=json.dumps(metadata or {}, ensure_ascii=False, sort_keys=True),
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def get_goal_for_user(session: Session, user: UserDB, goal_id: str) -> GoalDB | None:
    return session.exec(
        select(GoalDB)
        .where(GoalDB.id == goal_id)
        .where(GoalDB.user_id == user.id)
    ).first()


def list_goals_for_user(session: Session, user: UserDB, *, status: str | None = None) -> list[GoalDB]:
    if status is not None:
        status = validate_goal_status(status)
    query = select(GoalDB).where(GoalDB.user_id == user.id)
    if status is not None:
        query = query.where(GoalDB.status == status)
    return list(session.exec(
        query.order_by(GoalDB.priority.desc(), GoalDB.created_at.desc())
    ).all())


def transition_goal(session: Session, user: UserDB, goal_id: str, new_status: str) -> GoalDB:
    row = get_goal_for_user(session, user, goal_id)
    if row is None:
        raise LookupError("Goal not found")
    new_status = validate_goal_status(new_status)
    if new_status == row.status:
        return row
    if new_status not in _ALLOWED_TRANSITIONS[row.status]:
        raise ValueError("Invalid goal lifecycle transition")

    now = datetime.now()
    row.status = new_status
    row.updated_at = now
    if new_status == "completed":
        row.completed_at = now
    elif new_status == "archived":
        row.archived_at = now
    session.add(row)
    session.commit()
    session.refresh(row)
    return row
