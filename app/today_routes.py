"""Canonical read-only TODAY aggregation for the EVOLVE daily action surface."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.auth.dependencies import get_current_user
from app.database import get_session
from app.decision_routes import decision_today
from app.models import UserDB
from app.training.routes import get_training_today

router = APIRouter(prefix="/app/today", tags=["today"])


@router.get("")
def get_today(
    user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Aggregate today's decision and effective training action without mutating state."""
    decision = decision_today(user=user, db=db)
    training = get_training_today(user=user, session=db)

    return {
        "date": training["date"],
        "decision": decision,
        "training": training,
        "action": {
            "decision": decision["decision"],
            "priority": decision["priority"],
            "action": decision["action"],
            "can_start": training["can_start"],
            "has_workout": training["has_workout"],
        },
        "read_only": True,
    }
