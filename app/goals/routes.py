"""Goals API and deterministic metric progress."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.auth.dependencies import get_current_user
from app.database import get_session
from app.models import GoalDB, TrainingSessionDB, TrainingSetResultDB, UserDB
from app.schemas import GoalCreateRequest, GoalUpdateRequest
from app.goals.service import (
    SUPPORTED_METRICS, calculate_progress, create_goal, get_goal_for_user,
    list_goals_for_user, transition_goal, validate_metric_key, validate_goal_type,
)

router = APIRouter(prefix="/app/goals", tags=["goals"])


def _parse_date(value: str | None, field: str) -> date | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail=f"Nieprawidłowa data: {field}")


def _serialize(goal: GoalDB) -> dict:
    return {
        "id": goal.id, "goal_type": goal.goal_type, "title": goal.title,
        "description": goal.description, "status": goal.status,
        "start_date": goal.start_date.isoformat(),
        "target_date": goal.target_date.isoformat() if goal.target_date else None,
        "completed_at": goal.completed_at.isoformat() if goal.completed_at else None,
        "archived_at": goal.archived_at.isoformat() if goal.archived_at else None,
        "priority": goal.priority, "metric_key": goal.metric_key,
        "baseline_value": goal.baseline_value, "target_value": goal.target_value,
        "metadata": goal.metadata_dict(),
        "created_at": goal.created_at.isoformat(), "updated_at": goal.updated_at.isoformat(),
    }




def _validate_metric_values(metric: str | None, baseline: float | None, target: float | None) -> None:
    if metric is None:
        if baseline is not None or target is not None:
            raise ValueError("metric_key is required for metric values")
        return
    if target is None:
        raise ValueError("target_value is required when metric_key is set")
    if metric in {"best_weight_kg", "total_volume_kg", "sessions", "training_days", "best_reps_at_best_weight"} and target < 0:
        raise ValueError("target_value cannot be negative for this metric")
    if metric == "average_rpe" and not 1 <= target <= 10:
        raise ValueError("average_rpe target must be between 1 and 10")

def _owned_or_404(db: Session, user: UserDB, goal_id: str) -> GoalDB:
    row = get_goal_for_user(db, user, goal_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Cel nie istnieje")
    return row


@router.get("/metrics")
def get_goal_metrics(user: UserDB = Depends(get_current_user)):
    return {"metrics": [{"key": key, **value} for key, value in sorted(SUPPORTED_METRICS.items())]}


@router.post("")
def create_goal_api(
    payload: GoalCreateRequest,
    user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    try:
        start = _parse_date(payload.start_date, "start_date") or date.today()
        target_date = _parse_date(payload.target_date, "target_date")
        metric = validate_metric_key(payload.metric_key)
        _validate_metric_values(metric, payload.baseline_value, payload.target_value)
        duplicate = db.exec(select(GoalDB).where(GoalDB.user_id == user.id).where(GoalDB.goal_type == payload.goal_type.strip().lower()).where(GoalDB.title == payload.title.strip()).where(GoalDB.status == "active")).first()
        if duplicate:
            raise HTTPException(status_code=409, detail="Aktywny cel o tej nazwie i typie już istnieje")
        goal = create_goal(db, user, goal_type=payload.goal_type, title=payload.title,
                           description=payload.description, start_date=start,
                           target_date=target_date, priority=payload.priority,
                           metadata=payload.metadata)
        goal.metric_key, goal.baseline_value, goal.target_value = metric, payload.baseline_value, payload.target_value
        goal.updated_at = datetime.now()
        db.add(goal); db.commit(); db.refresh(goal)
        return _serialize(goal)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("")
def list_goals_api(
    status: str | None = None,
    user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    try:
        rows = list_goals_for_user(db, user, status=status)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"count": len(rows), "goals": [_serialize(row) for row in rows]}


@router.get("/{goal_id}")
def get_goal_api(goal_id: str, user: UserDB = Depends(get_current_user), db: Session = Depends(get_session)):
    return _serialize(_owned_or_404(db, user, goal_id))


@router.patch("/{goal_id}")
def update_goal_api(
    goal_id: str, payload: GoalUpdateRequest,
    user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    goal = _owned_or_404(db, user, goal_id)
    data = payload.model_dump(exclude_unset=True)
    try:
        if "goal_type" in data: goal.goal_type = validate_goal_type(data["goal_type"])
        if "title" in data: goal.title = str(data["title"]).strip()
        if not goal.title or len(goal.title) > 200: raise ValueError("Goal title must contain 1-200 characters")
        if "description" in data: goal.description = data["description"] or ""
        if "start_date" in data: goal.start_date = _parse_date(data["start_date"], "start_date") or goal.start_date
        if "target_date" in data: goal.target_date = _parse_date(data["target_date"], "target_date")
        if goal.target_date and goal.target_date < goal.start_date: raise ValueError("Goal target_date cannot precede start_date")
        if "priority" in data: goal.priority = data["priority"]
        if "metric_key" in data: goal.metric_key = validate_metric_key(data["metric_key"])
        if "baseline_value" in data: goal.baseline_value = data["baseline_value"]
        if "target_value" in data: goal.target_value = data["target_value"]
        _validate_metric_values(goal.metric_key, goal.baseline_value, goal.target_value)
        if "metadata" in data: 
            import json
            goal.metadata_json = json.dumps(data["metadata"] or {}, ensure_ascii=False, sort_keys=True)
        if "status" in data: goal = transition_goal(db, user, goal.id, data["status"])
        goal.updated_at = datetime.now()
        db.add(goal); db.commit(); db.refresh(goal)
        return _serialize(goal)
    except (ValueError, LookupError) as exc:
        db.rollback()
        raise HTTPException(status_code=422 if isinstance(exc, ValueError) else 404, detail=str(exc))


@router.delete("/{goal_id}")
def delete_goal_api(goal_id: str, user: UserDB = Depends(get_current_user), db: Session = Depends(get_session)):
    goal = _owned_or_404(db, user, goal_id)
    try:
        goal = transition_goal(db, user, goal.id, "archived")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return {"archived": True, "goal": _serialize(goal)}


def _metric_snapshots(db: Session, user: UserDB, goal: GoalDB) -> list[dict[str, Any]]:
    """Build cumulative goal metric snapshots from the same completed execution source as Progress."""
    metric = goal.metric_key
    if not metric:
        return []
    sessions = list(db.exec(
        select(TrainingSessionDB)
        .where(TrainingSessionDB.user_id == user.id)
        .where(TrainingSessionDB.status == "completed")
        .where(TrainingSessionDB.session_date >= goal.start_date)
        .order_by(TrainingSessionDB.session_date.asc(), TrainingSessionDB.completed_at.asc())
    ).all())
    exercise_key = goal.metadata_dict().get("exercise_key")
    snapshots: list[dict[str, Any]] = []
    cumulative_volume = 0.0
    cumulative_sets = 0
    cumulative_rpes: list[float] = []
    best_weight = 0.0
    best_reps_at_best_weight = 0
    training_days: set[str] = set()

    for training in sessions:
        sets = list(db.exec(
            select(TrainingSetResultDB)
            .where(TrainingSetResultDB.session_id == training.id)
            .where(TrainingSetResultDB.user_id == user.id)
            .where(TrainingSetResultDB.completed == True)
        ).all())
        if exercise_key:
            sets = [row for row in sets if row.exercise_key == exercise_key]
        if not sets and (exercise_key or metric not in {"sessions", "training_days"}):
            continue

        if sets:
            cumulative_sets += len(sets)
            cumulative_volume += sum(float(row.actual_weight_kg or 0) * int(row.actual_reps or 0) for row in sets)
            for row in sets:
                weight = float(row.actual_weight_kg or 0)
                reps = int(row.actual_reps or 0)
                if weight > best_weight:
                    best_weight = weight
                    best_reps_at_best_weight = reps
                elif weight == best_weight:
                    best_reps_at_best_weight = max(best_reps_at_best_weight, reps)
                if row.actual_rpe is not None:
                    cumulative_rpes.append(float(row.actual_rpe))

        training_days.add(training.session_date.isoformat())
        if metric == "sessions":
            value = float(len([item for item in snapshots]) + 1)
        elif metric == "training_days":
            value = float(len(training_days))
        elif metric == "total_volume_kg":
            value = cumulative_volume
        elif metric == "best_weight_kg":
            value = best_weight
        elif metric == "best_reps_at_best_weight":
            value = best_reps_at_best_weight
        elif metric == "average_rpe":
            if not cumulative_rpes:
                continue
            value = sum(cumulative_rpes) / len(cumulative_rpes)
        else:
            continue
        snapshots.append({
            "date": training.session_date.isoformat(),
            "value": round(value, 2),
            "session_id": training.id,
        })
    return snapshots


@router.get("/{goal_id}/progress")
def get_goal_progress(goal_id: str, user: UserDB = Depends(get_current_user), db: Session = Depends(get_session)):
    goal = _owned_or_404(db, user, goal_id)
    metric = validate_metric_key(goal.metric_key)
    if not metric:
        return {"goal": _serialize(goal), "metric": None, "current_value": None, "target_value": goal.target_value,
                "remaining": None, "progress_pct": None, "trend": None, "on_track": None, "last_updated": None, "history": []}
    history = _metric_snapshots(db, user, goal)
    current = history[-1]["value"] if history else None
    definition = SUPPORTED_METRICS[metric]
    calc = calculate_progress(current, goal.baseline_value, goal.target_value, definition["direction"])
    on_track = calc["on_track"]
    if on_track is not True and goal.target_date and goal.baseline_value is not None and goal.target_value is not None and goal.target_date > goal.start_date:
        total_days = (goal.target_date - goal.start_date).days
        elapsed_days = max(0, min(total_days, (date.today() - goal.start_date).days))
        expected_pct = (elapsed_days / total_days) * 100
        on_track = calc["percent"] is not None and calc["percent"] >= round(expected_pct, 1)
    trend = None
    if len(history) >= 2:
        delta = history[-1]["value"] - history[-2]["value"]
        trend = "up" if delta > 0 else "down" if delta < 0 else "stable"
    return {
        "goal": _serialize(goal), "metric": {"key": metric, **definition},
        "current_value": current, "target_value": goal.target_value,
        "remaining": calc["remaining"], "progress_pct": calc["percent"],
        "trend": trend, "on_track": on_track,
        "last_updated": history[-1]["date"] if history else None,
        "deadline": goal.target_date.isoformat() if goal.target_date else None,
        "history": history,
    }
