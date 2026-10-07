"""Read-only Decision Engine API boundary."""
from datetime import date
import json

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.auth.dependencies import get_current_user
from app.database import get_session
from app.decision_engine import build_decision
from app.goals.routes import _metric_snapshots
from app.goals.service import list_goals_for_user
from app.goals.training_state import build_goal_training_state
from app.models import TrainingSessionDB, TrainingSetResultDB, UserDB
from app.recovery.routes import recovery_for_date
from app.training.evaluation import evaluate_session

router = APIRouter(prefix="/app/decision", tags=["decision"])


def _latest_training_signal(db: Session, user: UserDB) -> dict:
    session = db.exec(
        select(TrainingSessionDB)
        .where(TrainingSessionDB.user_id == user.id)
        .where(TrainingSessionDB.status == "completed")
        .order_by(TrainingSessionDB.session_date.desc(), TrainingSessionDB.completed_at.desc())
    ).first()
    if not session:
        return {"status": "insufficient_data", "overall_decision": "insufficient_data", "session_id": None}
    try:
        snapshot = json.loads(session.planned_snapshot_json or "{}")
    except (TypeError, json.JSONDecodeError):
        snapshot = {}
    planned = snapshot.get("exercises") if isinstance(snapshot.get("exercises"), list) else []
    results = db.exec(
        select(TrainingSetResultDB)
        .where(TrainingSetResultDB.session_id == session.id)
        .where(TrainingSetResultDB.user_id == user.id)
        .where(TrainingSetResultDB.completed == True)
        .order_by(TrainingSetResultDB.exercise_key, TrainingSetResultDB.set_number)
    ).all()
    grouped = {}
    for result in results:
        grouped.setdefault(result.exercise_key, []).append(result)
    evaluation = evaluate_session(planned, grouped)
    return {
        "status": "ready",
        "overall_decision": evaluation.get("overall_decision"),
        "session_id": session.id,
        "reason_codes": evaluation.get("overall_reason_codes", []),
    }


@router.get("/today")
def decision_today(user: UserDB = Depends(get_current_user), db: Session = Depends(get_session)):
    goals = [goal for goal in list_goals_for_user(db, user.id) if goal.status == "active"]
    goal_states = [build_goal_training_state(goal, _metric_snapshots(db, user, goal)) for goal in goals]
    recovery = recovery_for_date(db, user.id, date.today())
    training = _latest_training_signal(db, user)
    return build_decision(goal_states=goal_states, recovery=recovery, training=training)
