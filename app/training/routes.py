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
