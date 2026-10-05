"""API boundary for deterministic Stage 8 training-result evaluation."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.auth.dependencies import get_current_user
from app.database import get_session
from app.models import TrainingSessionDB, TrainingSetResultDB, UserDB
from app.training.evaluation import evaluate_session

router = APIRouter(prefix="/app/training", tags=["training-evaluation"])


@router.get("/sessions/{session_id}/evaluation")
def get_training_evaluation(
    session_id: str,
    user: UserDB = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Evaluate one completed owned session without mutating any plan."""
    row = session.exec(
        select(TrainingSessionDB)
        .where(TrainingSessionDB.id == session_id)
        .where(TrainingSessionDB.user_id == user.id)
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Sesja treningowa nie istnieje")
    if row.status != "completed":
        raise HTTPException(
            status_code=409,
            detail="Ocena treningu jest dostępna dopiero po zakończeniu sesji",
        )

    try:
        snapshot = json.loads(row.planned_snapshot_json or "{}")
    except (TypeError, json.JSONDecodeError):
        snapshot = {}

    planned_items = snapshot.get("exercises")
    if not isinstance(planned_items, list):
        planned_items = []

    completed = list(
        session.exec(
            select(TrainingSetResultDB)
            .where(TrainingSetResultDB.session_id == row.id)
            .where(TrainingSetResultDB.user_id == user.id)
            .where(TrainingSetResultDB.completed == True)
            .order_by(TrainingSetResultDB.exercise_key, TrainingSetResultDB.set_number)
        ).all()
    )

    completed_by_exercise: dict[str, list[TrainingSetResultDB]] = {}
    for item in completed:
        completed_by_exercise.setdefault(item.exercise_key, []).append(item)

    evaluation = evaluate_session(planned_items, completed_by_exercise)
    return {
        "session_id": row.id,
        "session_date": row.session_date.isoformat(),
        "status": row.status,
        "evaluation": evaluation,
    }
