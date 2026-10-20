"""Canonical Progress API for completed training history."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.auth.dependencies import get_current_user
from app.database import get_session
from app.models import UserDB
from app.training.history import list_completed_training_history
from app.training.progress import build_progress_evidence
from app.training.progress_explanation import explain_progress

router = APIRouter(prefix="/app/progress", tags=["progress"])


@router.get("/evidence/{exercise_key}")
def get_progress_evidence(
    exercise_key: str,
    limit: int = Query(12, ge=1, le=100),
    user: UserDB = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    history = list_completed_training_history(session, user.id, limit=limit)
    return build_progress_evidence(history, exercise_key=exercise_key)


@router.get("/changes/{exercise_key}")
def get_progress_changes(
    exercise_key: str,
    limit: int = Query(12, ge=1, le=100),
    user: UserDB = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    history = list_completed_training_history(session, user.id, limit=limit)
    evidence = build_progress_evidence(history, exercise_key=exercise_key)
    return explain_progress(evidence)
