"""
Training Execution — deterministic session lifecycle for planned workouts.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select

from app.auth.dependencies import get_current_user
from app.database import get_session
from app.models import ExerciseResultDB, TrainingSessionDB, TrainingSetResultDB, UserDB
from app.schemas import TrainingCompleteRequest, TrainingSetResultRequest

router = APIRouter(prefix="/app/training", tags=["training-execution"])


_DAY_LABELS = {0: "Pon", 1: "Wt", 2: "Śr", 3: "Czw", 4: "Pt", 5: "Sob", 6: "Niedz"}
_DAY_FULL = {
    0: "Poniedziałek", 1: "Wtorek", 2: "Środa", 3: "Czwartek",
    4: "Piątek", 5: "Sobota", 6: "Niedziela",
}


def _day_matches(value: Any, target: date) -> bool:
    value = str(value or "").strip().lower().rstrip(".")
    aliases = {
        "pon": 0, "poniedzialek": 0, "poniedziałek": 0,
        "wt": 1, "wto": 1, "wtorek": 1,
        "sr": 2, "śr": 2, "sroda": 2, "środa": 2,
        "czw": 3, "czwartek": 3,
        "pt": 4, "piatek": 4, "piątek": 4,
        "sob": 5, "sobota": 5,
        "niedz": 6, "nd": 6, "niedziela": 6,
    }
    return value == target.isoformat() or aliases.get(value) == target.weekday()


def _extract_workout(plan: dict, target: date) -> list[dict[str, Any]]:
    if not isinstance(plan, dict):
        return []

    day_label = _DAY_LABELS[target.weekday()]
    day_full = _DAY_FULL[target.weekday()]

    days = plan.get("days")
    if isinstance(days, list):
        for entry in days:
            if isinstance(entry, dict) and _day_matches(entry.get("day"), target):
                workout = entry.get("workout") or {}
                if isinstance(workout, dict):
                    return list(workout.get("exercises") or [])
                if isinstance(workout, list):
                    return list(workout)

    training = plan.get("training")
    if isinstance(training, dict):
        raw = (
            training.get(day_label)
            or training.get(day_full)
            or next(
                (items for key, items in training.items() if _day_matches(key, target)),
                [],
            )
        )
        if isinstance(raw, dict):
            return list(raw.get("exercises") or [])
        if isinstance(raw, list):
            return list(raw)

    return []


def _normalize_plan_item(item: dict[str, Any], index: int) -> dict[str, Any]:
    name = str(item.get("name") or item.get("exercise_name") or "Ćwiczenie").strip()
    key = str(item.get("id") or item.get("item_id") or f"exercise-{index + 1}")
    weight = item.get("weight_kg", item.get("weight", 0))
    try:
        weight = float(weight or 0)
    except (TypeError, ValueError):
        weight = 0.0

    return {
        "exercise_key": key,
        "exercise_name": name,
        "sets": max(0, int(item.get("sets") or 0)),
        "reps": max(0, int(item.get("reps") or 0)),
        "weight_kg": max(0.0, weight),
        "rpe": int(item["rpe"]) if item.get("rpe") is not None else None,
        "notes": str(item.get("notes") or ""),
    }


def _serialize_session(session: TrainingSessionDB, sets: list[TrainingSetResultDB]) -> dict:
    return {
        "id": session.id,
        "session_date": session.session_date.isoformat(),
        "status": session.status,
        "started_at": session.started_at.isoformat(),
        "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        "final_rpe": session.final_rpe,
        "notes": session.notes,
        "planned": session.planned_snapshot(),
        "sets": [
            {
                "id": item.id,
                "exercise_key": item.exercise_key,
                "exercise_name": item.exercise_name,
                "set_number": item.set_number,
                "planned_reps": item.planned_reps,
                "planned_weight_kg": item.planned_weight_kg,
                "actual_reps": item.actual_reps,
                "actual_weight_kg": item.actual_weight_kg,
                "actual_rpe": item.actual_rpe,
                "completed": item.completed,
                "note": item.note,
                "logged_at": item.logged_at.isoformat(),
            }
            for item in sets
        ],
    }


def _owned_session(session: Session, user: UserDB, session_id: str) -> TrainingSessionDB:
    row = session.exec(
        select(TrainingSessionDB)
        .where(TrainingSessionDB.id == session_id)
        .where(TrainingSessionDB.user_id == user.id)
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Sesja treningowa nie istnieje")
    return row


@router.post("/sessions/start")
def start_training_session(
    user: UserDB = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    target_date = date.today()

    active = session.exec(
        select(TrainingSessionDB)
        .where(TrainingSessionDB.user_id == user.id)
        .where(TrainingSessionDB.session_date == target_date)
        .where(TrainingSessionDB.status == "active")
    ).first()
    if active:
        sets = list(
            session.exec(
                select(TrainingSetResultDB)
                .where(TrainingSetResultDB.session_id == active.id)
                .order_by(TrainingSetResultDB.exercise_key, TrainingSetResultDB.set_number)
            ).all()
        )
        return {"status": "resumed", "session": _serialize_session(active, sets)}

    try:
        plan = json.loads(user.weekly_plan_json or "{}")
    except json.JSONDecodeError:
        plan = {}

    exercises = [
        _normalize_plan_item(item, index)
        for index, item in enumerate(_extract_workout(plan, target_date))
        if isinstance(item, dict)
    ]
    if not exercises:
        raise HTTPException(status_code=404, detail="Brak zaplanowanego treningu na dziś")

    snapshot = {
        "session_date": target_date.isoformat(),
        "day_label": _DAY_LABELS[target_date.weekday()],
        "exercises": exercises,
    }
    new_session = TrainingSessionDB(
        user_id=user.id,
        session_date=target_date,
        status="active",
        planned_snapshot_json=json.dumps(snapshot, ensure_ascii=False),
    )
    session.add(new_session)
    try:
        session.commit()
        session.refresh(new_session)
    except SQLAlchemyError as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail="Nie udało się rozpocząć sesji") from exc

    return {"status": "started", "session": _serialize_session(new_session, [])}


@router.get("/sessions/{session_id}")
def get_training_session(
    session_id: str,
    user: UserDB = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    row = _owned_session(session, user, session_id)
    sets = list(
        session.exec(
            select(TrainingSetResultDB)
            .where(TrainingSetResultDB.session_id == row.id)
            .where(TrainingSetResultDB.user_id == user.id)
            .order_by(TrainingSetResultDB.exercise_key, TrainingSetResultDB.set_number)
        ).all()
    )
    return {"session": _serialize_session(row, sets)}


@router.post("/sessions/{session_id}/sets")
def log_training_set(
    session_id: str,
    payload: TrainingSetResultRequest,
    user: UserDB = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    row = _owned_session(session, user, session_id)
    if row.status != "active":
        raise HTTPException(status_code=409, detail="Zakończona sesja nie może być edytowana")

    planned = next(
        (
            item for item in row.planned_snapshot().get("exercises", [])
            if str(item.get("exercise_key")) == payload.exercise_key
        ),
        None,
    )
    if planned is None:
        raise HTTPException(status_code=422, detail="Ćwiczenie nie należy do snapshotu sesji")

    planned_sets = max(0, int(planned.get("sets") or 0))
    if planned_sets and payload.set_number > planned_sets:
        raise HTTPException(status_code=422, detail="Numer serii wykracza poza zaplanowaną liczbę serii")

    existing = session.exec(
        select(TrainingSetResultDB)
        .where(TrainingSetResultDB.session_id == row.id)
        .where(TrainingSetResultDB.exercise_key == payload.exercise_key)
        .where(TrainingSetResultDB.set_number == payload.set_number)
    ).first()

    if existing:
        existing.actual_reps = payload.actual_reps
        existing.actual_weight_kg = payload.actual_weight_kg
        existing.actual_rpe = payload.actual_rpe
        existing.completed = payload.completed
        existing.note = payload.note
        result = existing
    else:
        result = TrainingSetResultDB(
            session_id=row.id,
            user_id=user.id,
            exercise_key=payload.exercise_key,
            exercise_name=str(planned.get("exercise_name") or "Ćwiczenie"),
            set_number=payload.set_number,
            planned_reps=planned.get("reps"),
            planned_weight_kg=planned.get("weight_kg"),
            actual_reps=payload.actual_reps,
            actual_weight_kg=payload.actual_weight_kg,
            actual_rpe=payload.actual_rpe,
            completed=payload.completed,
            note=payload.note,
        )
    session.add(result)
    row.updated_at = datetime.now()
    session.add(row)
    try:
        session.commit()
        session.refresh(result)
    except SQLAlchemyError as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail="Nie udało się zapisać serii") from exc

    return {
        "status": "updated" if existing else "created",
        "set": {
            "id": result.id,
            "exercise_key": result.exercise_key,
            "exercise_name": result.exercise_name,
            "set_number": result.set_number,
            "planned_reps": result.planned_reps,
            "planned_weight_kg": result.planned_weight_kg,
            "actual_reps": result.actual_reps,
            "actual_weight_kg": result.actual_weight_kg,
            "actual_rpe": result.actual_rpe,
            "completed": result.completed,
            "note": result.note,
        },
    }



@router.get("/sessions/{session_id}/analysis")
def analyze_training_session(
    session_id: str,
    user: UserDB = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Return deterministic post-session facts without changing the plan."""
    row = _owned_session(session, user, session_id)
    sets = list(
        session.exec(
            select(TrainingSetResultDB)
            .where(TrainingSetResultDB.session_id == row.id)
            .where(TrainingSetResultDB.user_id == user.id)
            .order_by(TrainingSetResultDB.exercise_key, TrainingSetResultDB.set_number)
        ).all()
    )

    planned_items = {
        str(item.get("exercise_key")): item
        for item in row.planned_snapshot().get("exercises", [])
        if isinstance(item, dict)
    }
    by_exercise: dict[str, list[TrainingSetResultDB]] = {}
    for item in sets:
        by_exercise.setdefault(item.exercise_key, []).append(item)

    exercises = []
    for key, planned in planned_items.items():
        actual = by_exercise.get(key, [])
        planned_sets = max(0, int(planned.get("sets") or 0))
        completed = [item for item in actual if item.completed]
        target_reps = int(planned.get("reps") or 0)
        target_weight = float(planned.get("weight_kg") or 0)
        avg_reps = round(sum(item.actual_reps for item in completed) / len(completed), 2) if completed else 0
        avg_weight = round(sum(float(item.actual_weight_kg or 0) for item in completed) / len(completed), 2) if completed else 0
        rpes = [item.actual_rpe for item in completed if item.actual_rpe is not None]
        avg_rpe = round(sum(rpes) / len(rpes), 2) if rpes else None
        exercises.append({
            "exercise_key": key,
            "exercise_name": str(planned.get("exercise_name") or "Ćwiczenie"),
            "planned_sets": planned_sets,
            "completed_sets": len(completed),
            "set_completion_pct": round((len(completed) / planned_sets) * 100, 1) if planned_sets else 0,
            "planned_reps": target_reps,
            "average_actual_reps": avg_reps,
            "reps_delta": round(avg_reps - target_reps, 2) if completed else None,
            "planned_weight_kg": target_weight,
            "average_actual_weight_kg": avg_weight,
            "weight_delta_kg": round(avg_weight - target_weight, 2) if completed else None,
            "average_rpe": avg_rpe,
        })

    total_planned_sets = sum(item["planned_sets"] for item in exercises)
    total_completed_sets = sum(item["completed_sets"] for item in exercises)
    return {
        "session_id": row.id,
        "session_date": row.session_date.isoformat(),
        "status": row.status,
        "final_rpe": row.final_rpe,
        "planned_sets": total_planned_sets,
        "completed_sets": total_completed_sets,
        "completion_pct": round((total_completed_sets / total_planned_sets) * 100, 1) if total_planned_sets else 0,
        "exercises": exercises,
    }


_PROGRESSION_HIGH_RPE = 8
_PROGRESSION_LOW_COMPLETION_PCT = 80


def _progression_decision(planned: dict[str, Any], completed_sets: list[TrainingSetResultDB]) -> dict[str, Any]:
    planned_sets = max(0, int(planned.get("sets") or 0))
    target_reps = max(0, int(planned.get("reps") or 0))
    target_weight = max(0.0, float(planned.get("weight_kg") or 0))
    completed_count = len(completed_sets)
    completion_pct = round((completed_count / planned_sets) * 100, 1) if planned_sets else 0.0
    rpes = [item.actual_rpe for item in completed_sets if item.actual_rpe is not None]
    avg_rpe = round(sum(rpes) / len(rpes), 2) if rpes else None
    reps = [item.actual_reps for item in completed_sets]
    avg_reps = round(sum(reps) / len(reps), 2) if reps else None
    weights = [float(item.actual_weight_kg or 0) for item in completed_sets]
    avg_weight = round(sum(weights) / len(weights), 2) if weights else None

    if completed_count == 0:
        decision = "insufficient_data"
        reason_codes = ["NO_COMPLETED_SETS"]
    elif planned_sets == 0:
        decision = "insufficient_data"
        reason_codes = ["NO_PLANNED_SETS"]
    elif completion_pct < _PROGRESSION_LOW_COMPLETION_PCT:
        decision = "reduce"
        reason_codes = ["LOW_SET_COMPLETION"]
    elif avg_rpe is not None and avg_rpe > _PROGRESSION_HIGH_RPE:
        decision = "maintain"
        reason_codes = ["HIGH_RPE"]
    elif target_reps > 0 and avg_reps is not None and avg_reps < target_reps:
        decision = "maintain"
        reason_codes = ["REPS_BELOW_TARGET"]
    else:
        decision = "progress"
        reason_codes = ["TARGET_COMPLETED"]

    return {
        "decision": decision,
        "reason_codes": reason_codes,
        "planned_sets": planned_sets,
        "completed_sets": completed_count,
        "completion_pct": completion_pct,
        "planned_reps": target_reps,
        "average_actual_reps": avg_reps,
        "planned_weight_kg": target_weight,
        "average_actual_weight_kg": avg_weight,
        "average_rpe": avg_rpe,
    }


@router.get("/sessions/{session_id}/progression")
def get_training_progression(
    session_id: str,
    user: UserDB = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Return conservative deterministic next-step decisions without mutating a plan."""
    row = _owned_session(session, user, session_id)
    sets = list(
        session.exec(
            select(TrainingSetResultDB)
            .where(TrainingSetResultDB.session_id == row.id)
            .where(TrainingSetResultDB.user_id == user.id)
            .order_by(TrainingSetResultDB.exercise_key, TrainingSetResultDB.set_number)
        ).all()
    )

    planned_items = {
        str(item.get("exercise_key")): item
        for item in row.planned_snapshot().get("exercises", [])
        if isinstance(item, dict)
    }
    by_exercise: dict[str, list[TrainingSetResultDB]] = {}
    for item in sets:
        if item.completed:
            by_exercise.setdefault(item.exercise_key, []).append(item)

    exercises = []
    for key, planned in planned_items.items():
        result = _progression_decision(planned, by_exercise.get(key, []))
        result["exercise_key"] = key
        result["exercise_name"] = str(planned.get("exercise_name") or "Ćwiczenie")
        exercises.append(result)

    counts = {"progress": 0, "maintain": 0, "reduce": 0, "insufficient_data": 0}
    for item in exercises:
        counts[item["decision"]] += 1

    return {
        "session_id": row.id,
        "session_date": row.session_date.isoformat(),
        "status": row.status,
        "rules": {
            "high_rpe_threshold": _PROGRESSION_HIGH_RPE,
            "low_completion_pct": _PROGRESSION_LOW_COMPLETION_PCT,
            "mutates_plan": False,
        },
        "summary": counts,
        "exercises": exercises,
    }


def _round_load(value: float) -> float:
    return round(value / 2.5) * 2.5


def _next_plan_exercise(planned: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    current_reps = max(0, int(planned.get("reps") or 0))
    current_weight = max(0.0, float(planned.get("weight_kg") or 0))
    next_reps = current_reps
    next_weight = current_weight
    action = "unchanged"

    if decision["decision"] == "progress":
        action = "progress_load" if current_weight > 0 else "progress_reps"
        if current_weight > 0:
            next_weight = _round_load(current_weight * 1.025)
        else:
            next_reps = current_reps + 1
    elif decision["decision"] == "reduce":
        action = "reduce_load" if current_weight > 0 else "reduce_reps"
        if current_weight > 0:
            next_weight = max(0.0, _round_load(current_weight * 0.95))
        elif current_reps > 1:
            next_reps = current_reps - 1

    return {
        "exercise_key": str(planned.get("exercise_key") or ""),
        "exercise_name": str(planned.get("exercise_name") or "Ćwiczenie"),
        "decision": decision["decision"],
        "action": action,
        "current": {
            "sets": max(0, int(planned.get("sets") or 0)),
            "reps": current_reps,
            "weight_kg": current_weight,
        },
        "proposed": {
            "sets": max(0, int(planned.get("sets") or 0)),
            "reps": next_reps,
            "weight_kg": next_weight,
        },
        "reason_codes": decision["reason_codes"],
    }


@router.get("/sessions/{session_id}/next-plan-preview")
def preview_next_training_plan(
    session_id: str,
    user: UserDB = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Preview the next training adjustments; never writes to weekly_plan_json."""
    row = _owned_session(session, user, session_id)
    sets = list(
        session.exec(
            select(TrainingSetResultDB)
            .where(TrainingSetResultDB.session_id == row.id)
            .where(TrainingSetResultDB.user_id == user.id)
            .order_by(TrainingSetResultDB.exercise_key, TrainingSetResultDB.set_number)
        ).all()
    )

    planned_items = [
        item for item in row.planned_snapshot().get("exercises", [])
        if isinstance(item, dict)
    ]
    by_exercise: dict[str, list[TrainingSetResultDB]] = {}
    for item in sets:
        if item.completed:
            by_exercise.setdefault(item.exercise_key, []).append(item)

    exercises = []
    for planned in planned_items:
        key = str(planned.get("exercise_key") or "")
        decision = _progression_decision(planned, by_exercise.get(key, []))
        exercises.append(_next_plan_exercise(planned, decision))

    return {
        "session_id": row.id,
        "session_date": row.session_date.isoformat(),
        "source": "deterministic_session_result",
        "plan_mutated": False,
        "exercises": exercises,
    }


@router.post("/sessions/{session_id}/complete")
def complete_training_session(
    session_id: str,
    payload: TrainingCompleteRequest,
    user: UserDB = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    row = _owned_session(session, user, session_id)
    if row.status == "completed":
        sets = list(session.exec(select(TrainingSetResultDB).where(TrainingSetResultDB.session_id == row.id)).all())
        return {"status": "already_completed", "session": _serialize_session(row, sets)}
    if row.status != "active":
        raise HTTPException(status_code=409, detail="Sesja nie jest aktywna")

    sets = list(
        session.exec(
            select(TrainingSetResultDB)
            .where(TrainingSetResultDB.session_id == row.id)
            .where(TrainingSetResultDB.user_id == user.id)
            .where(TrainingSetResultDB.completed == True)
        ).all()
    )
    if not sets:
        raise HTTPException(status_code=422, detail="Nie można zakończyć pustej sesji")

    row.status = "completed"
    row.completed_at = datetime.now()
    row.final_rpe = payload.final_rpe
    row.notes = payload.notes
    row.updated_at = datetime.now()
    session.add(row)

    by_exercise: dict[str, list[TrainingSetResultDB]] = {}
    for item in sets:
        by_exercise.setdefault(item.exercise_key, []).append(item)

    existing_results = list(
        session.exec(
            select(ExerciseResultDB).where(ExerciseResultDB.user_id == user.id)
        ).all()
    )
    existing_keys = {
        (
            item.exercise_name,
            item.session_date,
            item.sets,
            item.reps,
            round(float(item.weight_kg or 0), 3),
        )
        for item in existing_results
    }

    for exercise_sets in by_exercise.values():
        reps = round(sum(item.actual_reps for item in exercise_sets) / len(exercise_sets))
        weight = round(sum(float(item.actual_weight_kg or 0) for item in exercise_sets) / len(exercise_sets), 3)
        rpes = [item.actual_rpe for item in exercise_sets if item.actual_rpe is not None]
        rpe = round(sum(rpes) / len(rpes)) if rpes else (payload.final_rpe or 1)
        name = exercise_sets[0].exercise_name
        key = (name, row.session_date, len(exercise_sets), reps, weight)
        if key in existing_keys:
            continue
        session.add(
            ExerciseResultDB(
                user_id=user.id,
                exercise_name=name,
                session_date=row.session_date,
                sets=len(exercise_sets),
                reps=reps,
                weight_kg=weight,
                rpe=max(1, min(10, rpe)),
                notes=payload.notes,
            )
        )

    try:
        session.commit()
        session.refresh(row)
    except SQLAlchemyError as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail="Nie udało się zakończyć sesji") from exc

    final_sets = list(
        session.exec(
            select(TrainingSetResultDB)
            .where(TrainingSetResultDB.session_id == row.id)
            .order_by(TrainingSetResultDB.exercise_key, TrainingSetResultDB.set_number)
        ).all()
    )
    return {"status": "completed", "session": _serialize_session(row, final_sets)}
