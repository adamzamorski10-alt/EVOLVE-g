"""Read-only Decision Engine API boundary."""
from datetime import date
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.auth.dependencies import get_current_user
from app.database import get_session
from app.decision_engine import build_decision
from app.goals.routes import _metric_snapshots
from app.goals.service import list_goals_for_user
from app.goals.training_state import build_goal_training_state
from app.models import UserDB
from app.recovery.routes import recovery_for_date

router = APIRouter(prefix="/app/decision", tags=["decision"])


@router.get("/today")
def decision_today(
    user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Return today's deterministic recommendation without mutating state."""
    goals = [goal for goal in list_goals_for_user(db, user.id) if goal.status == "active"]
    goal_states = [
        build_goal_training_state(
            goal,
            _metric_snapshots(db, user, goal),
        )
        for goal in goals
    ]
    recovery = recovery_for_date(db, user.id, date.today())

    return build_decision(
        goal_states=goal_states,
        recovery=recovery,
    )
