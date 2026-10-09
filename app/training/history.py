"""Canonical read-only training history for completed execution.

History is derived from the canonical execution tables. It deliberately does
not use ExerciseResultDB, which is a compatibility/materialized legacy model.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlmodel import Session, select

from app.models import TrainingSessionDB, TrainingSetResultDB


def list_completed_training_history(
    db: Session,
    user_id: str,
    *,
    limit: int = 20,
    session_date_from: date | None = None,
    session_date_to: date | None = None,
) -> list[dict[str, Any]]:
    """Return deterministic, user-scoped completed-session history.

    Only completed sessions are included. Results are attached by both
    session_id and user_id so a foreign user's result can never become part of
    the authenticated user's history.
    """
    safe_limit = max(1, min(int(limit), 100))
    query = (
        select(TrainingSessionDB)
        .where(
            TrainingSessionDB.user_id == user_id,
            TrainingSessionDB.status == "completed",
        )
        .order_by(
            TrainingSessionDB.session_date.desc(),
            TrainingSessionDB.id.desc(),
        )
        .limit(safe_limit)
    )
    if session_date_from is not None:
        query = query.where(TrainingSessionDB.session_date >= session_date_from)
    if session_date_to is not None:
        query = query.where(TrainingSessionDB.session_date <= session_date_to)

    sessions = list(db.exec(query).all())
    if not sessions:
        return []

    session_ids = [item.id for item in sessions]
    results = list(
        db.exec(
            select(TrainingSetResultDB)
            .where(
                TrainingSetResultDB.user_id == user_id,
                TrainingSetResultDB.session_id.in_(session_ids),
            )
            .order_by(
                TrainingSetResultDB.session_id.asc(),
                TrainingSetResultDB.exercise_key.asc(),
                TrainingSetResultDB.set_number.asc(),
                TrainingSetResultDB.id.asc(),
            )
        ).all()
    )

    by_session: dict[str, list[TrainingSetResultDB]] = {}
    for result in results:
        by_session.setdefault(result.session_id, []).append(result)

    history: list[dict[str, Any]] = []
    for training_session in sessions:
        sets = by_session.get(training_session.id, [])
        exercises: dict[str, dict[str, Any]] = {}

        for result in sets:
            exercise = exercises.setdefault(
                result.exercise_key,
                {
                    "exercise_key": result.exercise_key,
                    "exercise_name": result.exercise_name,
                    "sets": [],
                },
            )
            exercise["sets"].append(
                {
                    "set_number": result.set_number,
                    "planned_reps": result.planned_reps,
                    "planned_weight_kg": result.planned_weight_kg,
                    "actual_reps": result.actual_reps,
                    "actual_weight_kg": result.actual_weight_kg,
                    "actual_rpe": result.actual_rpe,
                    "completed": bool(result.completed),
                    "note": result.note,
                }
            )

        completed_sets = sum(1 for result in sets if result.completed)
        total_sets = len(sets)
        history.append(
            {
                "session_id": training_session.id,
                "session_date": training_session.session_date,
                "status": training_session.status,
                "final_rpe": training_session.final_rpe,
                "notes": training_session.notes,
                "started_at": training_session.started_at,
                "completed_at": training_session.completed_at,
                "total_sets": total_sets,
                "completed_sets": completed_sets,
                "completion_pct": (
                    round((completed_sets / total_sets) * 100, 1)
                    if total_sets
                    else None
                ),
                "exercises": list(exercises.values()),
                "sufficient_data": bool(completed_sets),
            }
        )

    return history
