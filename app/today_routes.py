"""Canonical read-only TODAY aggregation for the EVOLVE daily action surface."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.auth.dependencies import get_current_user
from app.database import get_session
from app.decision_routes import decision_today
from app.models import UserDB
from app.today import build_today_action
from app.training.routes import get_training_today

router = APIRouter(prefix="/app/today", tags=["today"])


@router.get("")
def get_today(
    user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Return the stable semantic TODAY contract without mutating state."""
    decision = decision_today(user=user, db=db)
    training = get_training_today(user=user, session=db)
    action = build_today_action(decision=decision, training=training)

    return {
        "date": training["date"],
        "status": action["state"],
        "primary_action": action["primary_action"],
        "explanation": action["explanation"],
        "safety": action["safety"],
        "workout": {
            **action["workout"],
            "day_label": training.get("day_label"),
            "plan": training.get("plan"),
            "exercises": training.get("exercises", []),
            "session": training.get("session", {}),
            "message": training.get("message"),
            "plan_stale": training.get("plan_stale"),
        },
        "evidence": action["evidence"],
        "data_quality": action["data_quality"],
        "decision": decision,
        "read_only": True,
    }
