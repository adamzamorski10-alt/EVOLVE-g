"""
Training Execution — deterministic session lifecycle for planned workouts.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmodel import Session, select

from app.auth.dependencies import get_current_user
from app.database import get_session
from app.models import AdaptivePlanRevisionDB, ExerciseResultDB, TrainingSessionDB, TrainingSetResultDB, UserDB
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


def _load_base_plan(user: UserDB) -> dict:
    try:
        value = json.loads(user.weekly_plan_json or "{}")
        return value if isinstance(value, dict) else {}
    except (TypeError, json.JSONDecodeError):
        return {}


def _latest_adaptive_revision(user_id: str, session: Session) -> AdaptivePlanRevisionDB | None:
    return session.exec(
        select(AdaptivePlanRevisionDB)
        .where(AdaptivePlanRevisionDB.user_id == user_id)
        .order_by(AdaptivePlanRevisionDB.version.desc(), AdaptivePlanRevisionDB.created_at.desc())
    ).first()


def _plan_fingerprint(plan: dict) -> str:
    canonical = json.dumps(plan, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _effective_plan(user: UserDB, session: Session) -> tuple[dict, dict]:
    """Resolve only an adaptive revision derived from the current base plan."""
    base = _load_base_plan(user)
    revision = _latest_adaptive_revision(user.id, session)
    if revision and isinstance(base, dict) and base:
        try:
            adapted = json.loads(revision.applied_plan_json or "{}")
        except (TypeError, json.JSONDecodeError):
            adapted = {}
        metadata = adapted.get("_evolve_adaptation") if isinstance(adapted, dict) else None
        if (
            isinstance(adapted, dict)
            and isinstance(adapted.get("days"), list)
            and isinstance(metadata, dict)
            and metadata.get("base_plan_fingerprint") == _plan_fingerprint(base)
        ):
            return adapted, {
                "source": "adaptive",
                "version": revision.version,
                "created_at": revision.created_at.isoformat(),
                "source_session_ids": revision.source_session_ids(),
                "algorithm": metadata.get("algorithm", "deterministic-v1"),
            }
    return base, {
        "source": "base",
        "version": 0,
        "created_at": None,
        "source_session_ids": [],
        "algorithm": None,
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


@router.get("/sessions/history")
def get_training_history(
    limit: int = 20,
    user: UserDB = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Return the authenticated user's completed training history with compact results."""
    limit = max(1, min(limit, 100))
    rows = list(
        session.exec(
            select(TrainingSessionDB)
            .where(TrainingSessionDB.user_id == user.id)
            .where(TrainingSessionDB.status == "completed")
            .order_by(TrainingSessionDB.session_date.desc(), TrainingSessionDB.completed_at.desc())
            .limit(limit)
        ).all()
    )
    result = []
    for row in rows:
        sets = list(
            session.exec(
                select(TrainingSetResultDB)
                .where(TrainingSetResultDB.session_id == row.id)
                .where(TrainingSetResultDB.user_id == user.id)
                .where(TrainingSetResultDB.completed == True)
            ).all()
        )
        planned = row.planned_snapshot()
        planned_sets = sum(max(0, int(item.get("sets") or 0)) for item in planned.get("exercises", []) if isinstance(item, dict))
        exercise_names = sorted({item.exercise_name for item in sets})
        result.append({
            "session_id": row.id,
            "session_date": row.session_date.isoformat(),
            "completed_at": row.completed_at.isoformat() if row.completed_at else None,
            "final_rpe": row.final_rpe,
            "planned_sets": planned_sets,
            "completed_sets": len(sets),
            "completion_pct": round((len(sets) / planned_sets) * 100, 1) if planned_sets else 0,
            "exercise_count": len(exercise_names),
            "exercises": exercise_names,
            "notes": row.notes,
        })
    return {"limit": limit, "count": len(result), "sessions": result}


@router.get("/exercises/{exercise_key}/history")
def get_exercise_history(
    exercise_key: str,
    limit: int = 20,
    user: UserDB = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Return chronological performance history for one exercise owned by the user."""
    limit = max(1, min(limit, 100))
    rows = list(
        session.exec(
            select(TrainingSetResultDB, TrainingSessionDB)
            .join(TrainingSessionDB, TrainingSetResultDB.session_id == TrainingSessionDB.id)
            .where(TrainingSetResultDB.user_id == user.id)
            .where(TrainingSetResultDB.exercise_key == exercise_key)
            .where(TrainingSetResultDB.completed == True)
            .order_by(TrainingSessionDB.session_date.desc(), TrainingSetResultDB.set_number.desc())
            .limit(limit)
        ).all()
    )
    return {
        "exercise_key": exercise_key,
        "count": len(rows),
        "results": [
            {
                "session_id": training.id,
                "session_date": training.session_date.isoformat(),
                "set_number": item.set_number,
                "exercise_name": item.exercise_name,
                "reps": item.actual_reps,
                "weight_kg": item.actual_weight_kg,
                "rpe": item.actual_rpe,
            }
            for item, training in rows
        ],
    }


@router.get("/today")
def get_training_today(
    user: UserDB = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Return the authenticated user's effective training plan for today."""
    target = date.today()
    plan, meta = _effective_plan(user, session)
    raw = _extract_workout(plan, target)
    exercises = [
        _normalize_plan_item(item, index)
        for index, item in enumerate(raw)
        if isinstance(item, dict)
    ]

    active = session.exec(
        select(TrainingSessionDB)
        .where(TrainingSessionDB.user_id == user.id)
        .where(TrainingSessionDB.session_date == target)
        .where(TrainingSessionDB.status == "active")
    ).first()

    active_sets = 0
    if active:
        active_sets = len(
            session.exec(
                select(TrainingSetResultDB)
                .where(TrainingSetResultDB.session_id == active.id)
                .where(TrainingSetResultDB.user_id == user.id)
                .where(TrainingSetResultDB.completed == True)
            ).all()
        )

    planned_sets = sum(
        max(0, int(item.get("sets") or 0))
        for item in exercises
    )

    return {
        "date": target.isoformat(),
        "day_label": _DAY_LABELS[target.weekday()],
        "has_workout": bool(exercises),
        "plan": meta,
        "exercises": exercises,
        "session": {
            "id": active.id if active else None,
            "status": active.status if active else None,
            "completed_sets": active_sets,
            "planned_sets": planned_sets,
            "completion_pct": (
                round((active_sets / planned_sets) * 100, 1)
                if planned_sets else 0
            ),
        },
        "message": (
            "Dzisiejszy trening pochodzi z zastosowanej adaptacji planu."
            if meta["source"] == "adaptive"
            else "Dzisiejszy trening pochodzi z bazowego planu tygodniowego."
        ),
    }


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

    plan, plan_meta = _effective_plan(user, session)

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
        "plan_source": plan_meta["source"],
        "plan_version": plan_meta["version"],
        "plan_source_session_ids": plan_meta["source_session_ids"],
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
        active = session.exec(select(TrainingSessionDB).where(TrainingSessionDB.user_id == user.id).where(TrainingSessionDB.session_date == target_date).where(TrainingSessionDB.status == "active")).first()
        if active:
            sets = list(session.exec(select(TrainingSetResultDB).where(TrainingSetResultDB.session_id == active.id).order_by(TrainingSetResultDB.exercise_key, TrainingSetResultDB.set_number)).all())
            return {"status": "resumed", "session": _serialize_session(active, sets)}
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
        .where(TrainingSetResultDB.user_id == user.id)
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
    except IntegrityError:
        session.rollback()
        existing = session.exec(
            select(TrainingSetResultDB)
            .where(TrainingSetResultDB.session_id == row.id)
            .where(TrainingSetResultDB.user_id == user.id)
            .where(TrainingSetResultDB.exercise_key == payload.exercise_key)
            .where(TrainingSetResultDB.set_number == payload.set_number)
        ).first()
        if existing is None:
            raise HTTPException(status_code=409, detail="Konflikt zapisu serii")
        existing.actual_reps = payload.actual_reps
        existing.actual_weight_kg = payload.actual_weight_kg
        existing.actual_rpe = payload.actual_rpe
        existing.completed = payload.completed
        existing.note = payload.note
        session.add(existing)
        try:
            session.commit()
            session.refresh(existing)
        except SQLAlchemyError as exc:
            session.rollback()
            raise HTTPException(status_code=500, detail="Nie udało się zapisać serii") from exc
        result = existing
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




@router.get("/adaptive/preview")
def get_adaptive_training_preview(
    user: UserDB = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Build a trend-aware, conservative read-only adaptation preview."""
    sessions = list(
        session.exec(
            select(TrainingSessionDB)
            .where(TrainingSessionDB.user_id == user.id)
            .where(TrainingSessionDB.status == "completed")
            .order_by(TrainingSessionDB.session_date.desc(), TrainingSessionDB.completed_at.desc())
            .limit(6)
        ).all()
    )
    if not sessions:
        return {
            "has_data": False,
            "sessions_analyzed": 0,
            "source_session_ids": [],
            "latest_session": None,
            "exercises": [],
            "plan_mutated": False,
        }

    source_ids = [item.id for item in sessions]
    session_sets: dict[str, list[TrainingSetResultDB]] = {}
    for training in sessions:
        session_sets[training.id] = list(
            session.exec(
                select(TrainingSetResultDB)
                .where(TrainingSetResultDB.session_id == training.id)
                .where(TrainingSetResultDB.user_id == user.id)
                .where(TrainingSetResultDB.completed == True)
                .order_by(TrainingSetResultDB.exercise_key, TrainingSetResultDB.set_number)
            ).all()
        )

    by_exercise: dict[str, list[tuple[TrainingSessionDB, TrainingSetResultDB]]] = {}
    for training in sessions:
        for item in session_sets[training.id]:
            by_exercise.setdefault(item.exercise_key, []).append((training, item))

    latest = sessions[0]
    latest_items = [
        item for item in latest.planned_snapshot().get("exercises", [])
        if isinstance(item, dict)
    ]
    preview = []
    for planned in latest_items:
        key = str(planned.get("exercise_key") or "")
        if not key:
            continue
        latest_completed = [item for item in session_sets[latest.id] if item.exercise_key == key]
        decision = _progression_decision(planned, latest_completed)
        proposed = _next_plan_exercise(planned, decision)

        history = by_exercise.get(key, [])
        grouped: list[dict[str, Any]] = []
        for training in sessions:
            sets_for_session = [item for owner, item in history if owner.id == training.id]
            if not sets_for_session:
                continue
            reps = [item.actual_reps for item in sets_for_session]
            weights = [float(item.actual_weight_kg or 0) for item in sets_for_session]
            rpes = [item.actual_rpe for item in sets_for_session if item.actual_rpe is not None]
            grouped.append({
                "session_id": training.id,
                "date": training.session_date.isoformat(),
                "average_reps": round(sum(reps) / len(reps), 2) if reps else None,
                "average_weight_kg": round(sum(weights) / len(weights), 2) if weights else None,
                "average_rpe": round(sum(rpes) / len(rpes), 2) if rpes else None,
                "completed_sets": len(sets_for_session),
            })
        recent = grouped[:3]
        trend = "insufficient_data"
        trend_delta = None
        if len(recent) >= 2:
            latest_metric = recent[0]["average_weight_kg"] or recent[0]["average_reps"] or 0
            previous_metric = recent[1]["average_weight_kg"] or recent[1]["average_reps"] or 0
            trend_delta = round(latest_metric - previous_metric, 2)
            trend = "up" if trend_delta > 0 else "down" if trend_delta < 0 else "stable"
        elif len(recent) == 1:
            trend = "new_baseline"

        if len(recent) >= 3:
            rpe_values = [x["average_rpe"] for x in recent if x["average_rpe"] is not None]
            if len(rpe_values) >= 3 and sum(rpe_values) / len(rpe_values) >= 8:
                decision = dict(decision)
                decision["decision"] = "maintain"
                decision["reason_codes"] = list(dict.fromkeys(decision["reason_codes"] + ["SUSTAINED_HIGH_RPE"]))
                proposed = _next_plan_exercise(planned, decision)

        data_sufficiency = (
            "high" if len(recent) >= 3 else
            "medium" if len(recent) == 2 else
            "low"
        )
        preview.append({
            "exercise_key": key,
            "exercise_name": str(planned.get("exercise_name") or "Ćwiczenie"),
            "decision": decision["decision"],
            "reason_codes": decision["reason_codes"],
            "data_sufficiency": data_sufficiency,
            "trend": trend,
            "trend_delta": trend_delta,
            "current": proposed["current"],
            "proposed": proposed["proposed"],
            "action": proposed["action"],
            "recent_sessions": recent,
        })

    return {
        "has_data": True,
        "sessions_analyzed": len(sessions),
        "source_session_ids": source_ids,
        "latest_session": {
            "id": latest.id,
            "date": latest.session_date.isoformat(),
            "final_rpe": latest.final_rpe,
        },
        "exercises": preview,
        "plan_mutated": False,
        "message": "Podgląd adaptacji na podstawie maksymalnie 6 ostatnich ukończonych sesji. Plan tygodniowy nie został zmieniony.",
    }



def _build_adaptive_plan(user_id: str, session: Session) -> tuple[dict, list[str], dict]:
    """Build a weekly-plan revision, changing only the latest completed day."""
    sessions = list(
        session.exec(
            select(TrainingSessionDB)
            .where(TrainingSessionDB.user_id == user_id)
            .where(TrainingSessionDB.status == "completed")
            .order_by(TrainingSessionDB.session_date.desc(), TrainingSessionDB.completed_at.desc())
            .limit(6)
        ).all()
    )
    if not sessions:
        return {}, [], {"progress": 0, "maintain": 0, "reduce": 0, "insufficient_data": 0}

    latest = sessions[0]
    source_ids = [item.id for item in sessions]
    plan = _load_base_plan(user=session.exec(select(UserDB).where(UserDB.id == user_id)).first())
    if not plan:
        plan = latest.planned_snapshot()
    latest_snapshot = latest.planned_snapshot()
    exercises = [item for item in latest_snapshot.get("exercises", []) if isinstance(item, dict)]
    if not exercises:
        return plan, source_ids, {"progress": 0, "maintain": 0, "reduce": 0, "insufficient_data": 0}

    latest_sets = list(
        session.exec(
            select(TrainingSetResultDB)
            .where(TrainingSetResultDB.session_id == latest.id)
            .where(TrainingSetResultDB.user_id == user_id)
            .where(TrainingSetResultDB.completed == True)
        ).all()
    )
    by_key: dict[str, list[TrainingSetResultDB]] = {}
    for item in latest_sets:
        by_key.setdefault(item.exercise_key, []).append(item)

    next_exercises = []
    summary = {"progress": 0, "maintain": 0, "reduce": 0, "insufficient_data": 0}
    for planned in exercises:
        key = str(planned.get("exercise_key") or "")
        decision = _progression_decision(planned, by_key.get(key, []))
        proposed = _next_plan_exercise(planned, decision)
        next_item = dict(proposed["proposed"])
        next_item["exercise_key"] = key
        next_item["exercise_name"] = planned.get("exercise_name") or "Ćwiczenie"
        next_exercises.append(next_item)
        summary[decision["decision"]] = summary.get(decision["decision"], 0) + 1

    adapted = json.loads(json.dumps(plan, ensure_ascii=False))
    target_day = latest.session_date
    replaced = False
    days = adapted.get("days") if isinstance(adapted, dict) else None
    if isinstance(days, list):
        for entry in days:
            if not isinstance(entry, dict) or not _day_matches(entry.get("day"), target_day):
                continue
            workout = entry.get("workout")
            if isinstance(workout, dict):
                existing = workout.get("exercises") or []
                by_key = {str(item.get("exercise_key") or item.get("id") or item.get("item_id") or ""): item for item in next_exercises if isinstance(item, dict)}
                updated = []
                for item in existing:
                    if not isinstance(item, dict):
                        updated.append(item)
                        continue
                    key = str(item.get("id") or item.get("item_id") or "")
                    replacement = by_key.get(key)
                    updated.append({**item, **({"sets": replacement["sets"], "reps": replacement["reps"], "weight_kg": replacement["weight_kg"]} if replacement else {})})
                    if replacement:
                        replaced = True
                workout["exercises"] = updated
            break
    if not replaced and not isinstance(days, list):
        adapted = latest.planned_snapshot()
    adapted["exercises"] = next_exercises
    adapted["_evolve_adaptation"] = {
        "base_plan_fingerprint": _plan_fingerprint(plan),
        "source_session_ids": source_ids,
        "source_day": target_day.isoformat(),
        "summary": summary,
        "algorithm": "deterministic-v1",
    }
    return adapted, source_ids, summary


@router.get("/adaptive/plan-current")
def get_adaptive_plan_current(
    user: UserDB = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    latest = _latest_adaptive_revision(user.id, session)
    if not latest:
        return {"has_adapted_plan": False, "version": 0, "plan": None}
    return {
        "has_adapted_plan": True,
        "version": latest.version,
        "plan": json.loads(latest.applied_plan_json or "{}"),
        "source_session_ids": latest.source_session_ids(),
        "created_at": latest.created_at.isoformat(),
    }


@router.post("/adaptive/apply")
def apply_adaptive_plan(
    user: UserDB = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Apply one deterministic adaptation with a revision/audit record."""
    proposed, source_ids, summary = _build_adaptive_plan(user.id, session)
    if not proposed:
        raise HTTPException(status_code=422, detail="Brak ukończonego treningu z planem do adaptacji")

    current = session.exec(
        select(AdaptivePlanRevisionDB)
        .where(AdaptivePlanRevisionDB.user_id == user.id)
        .order_by(AdaptivePlanRevisionDB.version.desc(), AdaptivePlanRevisionDB.created_at.desc())
    ).first()
    previous = json.loads(current.applied_plan_json) if current else {}
    version = (current.version + 1) if current else 1

    if current and json.dumps(previous, sort_keys=True) == json.dumps(proposed, sort_keys=True):
        return {
            "status": "unchanged",
            "version": current.version,
            "plan": previous,
            "source_session_ids": current.source_session_ids(),
            "message": "Nowa adaptacja nie różni się od ostatniej zapisanej wersji.",
        }

    revision = AdaptivePlanRevisionDB(
        user_id=user.id,
        source_session_ids_json=json.dumps(source_ids),
        previous_plan_json=json.dumps(previous, ensure_ascii=False),
        applied_plan_json=json.dumps(proposed, ensure_ascii=False),
        decision_summary_json=json.dumps(summary),
        version=version,
    )
    session.add(revision)
    try:
        session.commit()
        session.refresh(revision)
    except SQLAlchemyError as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail="Nie udało się zapisać adaptacji planu") from exc

    return {
        "status": "applied",
        "version": revision.version,
        "plan": proposed,
        "source_session_ids": source_ids,
        "decision_summary": summary,
        "created_at": revision.created_at.isoformat(),
        "message": "Adaptacja została zapisana jako nowa wersja. Poprzednia wersja pozostaje w audycie.",
    }


@router.get("/adaptive/history")
def get_adaptive_plan_history(
    limit: int = 20,
    user: UserDB = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    limit = max(1, min(limit, 100))
    rows = list(
        session.exec(
            select(AdaptivePlanRevisionDB)
            .where(AdaptivePlanRevisionDB.user_id == user.id)
            .order_by(AdaptivePlanRevisionDB.version.desc())
            .limit(limit)
        ).all()
    )
    return {
        "versions": [
            {
                "version": row.version,
                "created_at": row.created_at.isoformat(),
                "source_session_ids": row.source_session_ids(),
                "decision_summary": row.decision_summary(),
                "plan": json.loads(row.applied_plan_json or "{}"),
            }
            for row in rows
        ]
    }


@router.get("/adaptive/plan-preview")
def get_adaptive_plan_preview(
    user: UserDB = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Return a deterministic 2-week microcycle preview without persisting it."""
    sessions = list(
        session.exec(
            select(TrainingSessionDB)
            .where(TrainingSessionDB.user_id == user.id)
            .where(TrainingSessionDB.status == "completed")
            .order_by(TrainingSessionDB.session_date.desc(), TrainingSessionDB.completed_at.desc())
            .limit(6)
        ).all()
    )
    if not sessions:
        return {
            "has_data": False,
            "weeks": [],
            "source_session_ids": [],
            "plan_mutated": False,
        }

    latest = sessions[0]
    latest_exercises = [
        item for item in latest.planned_snapshot().get("exercises", [])
        if isinstance(item, dict)
    ]
    session_by_id = {item.id: item for item in sessions}
    latest_sets = list(
        session.exec(
            select(TrainingSetResultDB)
            .where(TrainingSetResultDB.session_id == latest.id)
            .where(TrainingSetResultDB.user_id == user.id)
            .where(TrainingSetResultDB.completed == True)
        ).all()
    )
    by_key: dict[str, list[TrainingSetResultDB]] = {}
    for item in latest_sets:
        by_key.setdefault(item.exercise_key, []).append(item)

    week_exercises = []
    for planned in latest_exercises:
        key = str(planned.get("exercise_key") or "")
        decision = _progression_decision(planned, by_key.get(key, []))
        proposed = _next_plan_exercise(planned, decision)
        week_exercises.append({
            "exercise_key": key,
            "exercise_name": str(planned.get("exercise_name") or "Ćwiczenie"),
            "week_1": proposed["proposed"],
            "week_2": proposed["proposed"],
            "decision": decision["decision"],
            "reason_codes": decision["reason_codes"],
        })

    return {
        "has_data": True,
        "source_session_ids": list(session_by_id),
        "source_latest_session": latest.id,
        "weeks": [
            {"week": 1, "source": "latest_completed_session", "exercises": week_exercises},
            {"week": 2, "source": "conservative_repeat_of_week_1", "exercises": week_exercises},
        ],
        "plan_mutated": False,
        "message": "To jest 2-tygodniowy preview. Żaden zapisany plan nie został zmieniony.",
    }


@router.get("/today-ui", response_class=HTMLResponse)
def training_today_ui():
    """Focused Mój Dzień training view backed by the effective plan resolver."""
    return HTMLResponse("""<!doctype html>
<html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>EVOLVE · Mój dzień</title>
<style>:root{color-scheme:dark;--bg:#090b12;--panel:#121722;--line:#252c3b;--text:#f4f6fb;--muted:#9aa4b5;--accent:#8b5cf6;--good:#34d399}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 15% 0%,#21183a,#090b12 48%);font:15px system-ui;color:var(--text)}main{max-width:900px;margin:auto;padding:34px 18px 60px}.top{display:flex;justify-content:space-between;align-items:center;gap:15px}.top h1{margin:0;font-size:32px}.back,.btn{color:#fff;text-decoration:none;border:1px solid var(--line);background:#171d29;padding:10px 13px;border-radius:10px;font-weight:700}.hero{margin-top:18px;padding:22px;border:1px solid var(--line);background:rgba(18,23,34,.94);border-radius:18px}.eyebrow{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.08em}.status{margin-top:8px;font-size:22px;font-weight:800}.muted{color:var(--muted)}.badge{display:inline-block;margin-top:12px;padding:6px 10px;border-radius:999px;background:#2d2148;color:#c4b5fd;font-weight:750;font-size:12px}.grid{display:grid;gap:12px;margin-top:14px}.exercise{padding:17px;background:rgba(18,23,34,.94);border:1px solid var(--line);border-radius:15px}.name{font-size:18px;font-weight:800}.target{margin-top:6px;color:var(--muted)}.empty{text-align:center;padding:35px}.actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}.primary{background:var(--accent);border-color:transparent}.reason{margin-top:12px;padding:11px 13px;border-radius:11px;background:#0d111a;color:var(--muted);font-size:13px}@media(max-width:600px){.top{align-items:flex-start;flex-direction:column}}
</style></head><body><main><div class="top"><h1>Mój dzień</h1><a class="back" href="/app#my-day">← Panel</a></div><div id="app" class="hero">Ładowanie dzisiejszego planu…</div></main>
<script>const token=localStorage.getItem('fitai_token');const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));async function load(){if(!token){app.innerHTML='<div class="empty"><b>Zaloguj się w EVOLVE</b><p class="muted">Po zalogowaniu zobaczysz swój aktualny trening.</p></div>';return}try{const r=await fetch('/app/training/today',{headers:{Authorization:'Bearer '+token}}),d=await r.json();if(!r.ok){app.innerHTML='<div class="empty">'+esc(d.detail||'Nie udało się pobrać planu.')+'</div>';return}const p=d.plan||{};const label=p.source==='adaptive'?'Plan v'+p.version+' · dostosowany na podstawie ostatnich treningów':'Bazowy plan tygodniowy';app.innerHTML='<div class="eyebrow">'+esc(d.day_label)+' · '+esc(d.date)+'</div><div class="status">'+(d.has_workout?'Dzisiejszy trening jest gotowy':'Dzień bez zaplanowanego treningu')+'</div><span class="badge">'+esc(label)+'</span>'+(d.has_workout?'<div class="grid">'+d.exercises.map(e=>'<div class="exercise"><div class="name">'+esc(e.exercise_name)+'</div><div class="target">'+e.sets+' × '+e.reps+(e.weight_kg?' · '+e.weight_kg+' kg':'')+(e.rpe?' · RPE '+e.rpe:'')+'</div></div>').join('')+'</div>':'<p class="muted">Na dziś nie ma ćwiczeń w aktywnym planie.</p>')+(p.source==='adaptive'?'<div class="reason">Dzisiejszy plan został pobrany z zastosowanej wersji adaptacyjnej. Źródłowe sesje: '+esc((p.source_session_ids||[]).join(', '))+'</div>':'<div class="reason">Nie zastosowano jeszcze adaptacji. Po ukończeniu treningu możesz przejść do Postępów i zapisać kolejną wersję planu.</div>')+'<div class="actions">'+(d.has_workout?'<a class="btn primary" href="/app/training/session-ui">▶ Rozpocznij trening</a>':'')+'<a class="btn" href="/app/training/dashboard">📈 Postępy</a><a class="btn" href="/">Wróć do aplikacji</a></div>'}catch(e){app.innerHTML='<div class="empty">Nie udało się połączyć z serwerem.</div>'}}load();</script></body></html>""")


@router.get("/session-ui", response_class=HTMLResponse)
def training_session_ui():
    """Browser UI for the deterministic PLAN -> START -> LOG -> COMPLETE loop."""
    return HTMLResponse("""<!doctype html>
<html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>EVOLVE · Trening</title>
<style>
:root{color-scheme:dark;--bg:#090b12;--panel:#121722;--line:#242b3a;--text:#f4f6fb;--muted:#9aa4b5;--accent:#8b5cf6;--good:#34d399}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 20% 0%,#1b1530 0,#090b12 48%);font:15px Inter,system-ui,sans-serif;color:var(--text)}
.wrap{max-width:900px;margin:auto;padding:30px 18px 60px}.top{display:flex;justify-content:space-between;gap:12px;align-items:center}.top h1{margin:0;font-size:30px}.back{color:#fff;text-decoration:none;border:1px solid var(--line);padding:9px 12px;border-radius:10px}
.notice{color:var(--muted);margin:12px 0 18px}.card{background:rgba(18,23,34,.94);border:1px solid var(--line);border-radius:16px;padding:18px;margin-top:14px}.exercise{border-top:1px solid var(--line);padding:16px 0}.exercise:first-child{border-top:0}.title{font-size:18px;font-weight:750}.target{color:var(--muted);margin:5px 0 12px}.sets{display:grid;gap:8px}.set{display:grid;grid-template-columns:55px 1fr 1fr 1fr auto;gap:8px;align-items:center}.set input{width:100%;padding:9px;background:#0d111a;border:1px solid var(--line);color:#fff;border-radius:8px}.set button,.primary{border:0;background:var(--accent);color:#fff;padding:9px 12px;border-radius:9px;font-weight:700;cursor:pointer}.set button.done{background:#173d30}.primary{margin-top:16px}.hidden{display:none}.success{color:var(--good)}@media(max-width:650px){.set{grid-template-columns:1fr 1fr 1fr}.set button{grid-column:1/-1}.set b{grid-column:1/-1}}
</style></head><body><main class="wrap">
<div class="top"><h1>Dzisiejszy trening</h1><a class="back" href="/">← EVOLVE</a></div>
<div id="status" class="notice">Ładowanie…</div>
<div id="workout"></div>
<button id="complete" class="primary hidden">Zakończ trening</button>
</main>
<script>
const token=localStorage.getItem('fitai_token'), headers=token?{'Authorization':'Bearer '+token,'Content-Type':'application/json'}:{};
let current=null;
const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
function setStatus(t,ok=false){status.textContent=t;status.className=ok?'notice success':'notice'}
async function api(url,opts={}){return fetch(url,{...opts,headers:{...headers,...(opts.headers||{})}})}
async function start(){
 if(!token){setStatus('Zaloguj się w EVOLVE, aby rozpocząć trening.');return}
 try{
  const r=await api('/app/training/sessions/start',{method:'POST'}), d=await r.json();
  if(!r.ok){setStatus(d.detail||'Nie udało się rozpocząć treningu.');return}
  current=d.session; render();
 }catch(e){setStatus('Nie udało się połączyć z serwerem.')}
}
function render(){
 setStatus(current.status==='completed'?'Trening ukończony.':'Trening aktywny — zapisuj każdą serię po wykonaniu.',current.status==='completed');
 workout.innerHTML='<div class="card">'+(current.planned.exercises||[]).map(ex=>{
  const logged=(current.sets||[]).filter(s=>s.exercise_key===ex.exercise_key);
  return '<div class="exercise"><div class="title">'+esc(ex.exercise_name)+'</div><div class="target">Plan: '+ex.sets+' × '+ex.reps+(ex.weight_kg?' · '+ex.weight_kg+' kg':'')+'</div><div class="sets">'+Array.from({length:ex.sets||1},(_,i)=>{
   const n=i+1, old=logged.find(s=>s.set_number===n);
   return '<div class="set"><b>Seria '+n+'</b><input id="r-'+ex.exercise_key+'-'+n+'" type="number" min="0" placeholder="powt." value="'+(old?.actual_reps??ex.reps)+'"><input id="w-'+ex.exercise_key+'-'+n+'" type="number" min="0" step="0.5" placeholder="kg" value="'+(old?.actual_weight_kg??ex.weight_kg)+'"><input id="p-'+ex.exercise_key+'-'+n+'" type="number" min="1" max="10" placeholder="RPE" value="'+(old?.actual_rpe??'')+'"><button '+(old?.completed?'class="done"':'')+' onclick="logSet(\''+esc(ex.exercise_key)+'\','+n+')">'+(old?.completed?'Zapisano':'Zapisz')+'</button></div>'
  }).join('')+'</div></div>'
 }).join('')+'</div>';
 complete.classList.toggle('hidden',current.status!=='active');
}
async function logSet(key,n){
 const ex=current.planned.exercises.find(x=>x.exercise_key===key);
 const reps=Number(document.getElementById('r-'+key+'-'+n).value||0), weight=Number(document.getElementById('w-'+key+'-'+n).value||0);
 const rpeRaw=document.getElementById('p-'+key+'-'+n).value; const rpe=rpeRaw?Number(rpeRaw):null;
 const r=await api('/app/training/sessions/'+current.id+'/sets',{method:'POST',body:JSON.stringify({exercise_key:key,set_number:n,actual_reps:reps,actual_weight_kg:weight,actual_rpe:rpe,completed:true})});
 const d=await r.json(); if(!r.ok){setStatus(d.detail||'Nie udało się zapisać serii.');return}
 const existing=current.sets.findIndex(x=>x.exercise_key===key&&x.set_number===n); if(existing>=0) current.sets[existing]=d.set; else current.sets.push(d.set); render();
}
complete.onclick=async()=>{
 const rpe=Number(prompt('Końcowe RPE treningu (1–10):')||0); if(!rpe)return;
 const r=await api('/app/training/sessions/'+current.id+'/complete',{method:'POST',body:JSON.stringify({final_rpe:rpe})});
 const d=await r.json(); if(!r.ok){setStatus(d.detail||'Nie udało się zakończyć treningu.');return}
 current=d.session; render(); complete.outerHTML='<a class="primary" href="/app/training/dashboard" style="display:inline-block;text-decoration:none">Zobacz analizę i progres →</a>';
};
start();
</script></body></html>""")

@router.get("/dashboard", response_class=HTMLResponse)
def training_dashboard():
    """Premium progress dashboard with trend cards and recent session history."""
    return HTMLResponse("""<!doctype html>
<html lang="pl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>EVOLVE · Postępy treningowe</title>
<style>
:root{color-scheme:dark;--bg:#090b12;--panel:#121722;--line:#242b3a;--text:#f4f6fb;--muted:#9aa4b5;--accent:#8b5cf6;--good:#34d399;--warn:#fbbf24;--bad:#fb7185}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 20% 0%,#1b1530 0,#090b12 45%);font:15px Inter,system-ui,sans-serif;color:var(--text)}
.wrap{max-width:1160px;margin:auto;padding:34px 20px 60px}.top{display:flex;justify-content:space-between;gap:20px;align-items:end;margin-bottom:24px}
h1{margin:0;font-size:32px}.sub{color:var(--muted);margin-top:7px}.back{color:#fff;text-decoration:none;border:1px solid var(--line);padding:10px 14px;border-radius:10px}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:18px}.card{background:rgba(18,23,34,.92);border:1px solid var(--line);border-radius:16px;padding:18px;box-shadow:0 12px 30px #0004}.label{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.08em}.value{font-size:24px;font-weight:750;margin-top:8px}
.list{display:grid;gap:10px}.row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:15px;align-items:center;border-top:1px solid var(--line);padding:13px 0}.row:first-child{border-top:0}.name{font-weight:700}.meta{color:var(--muted);font-size:13px;margin-top:4px}.pill{padding:6px 9px;border-radius:999px;font-size:12px;font-weight:700}.progress{background:#123d2d;color:var(--good)}.maintain{background:#3b3010;color:var(--warn)}.reduce{background:#3b1717;color:var(--bad)}.insufficient_data{background:#252b36;color:var(--muted)}
.trend{font-weight:700;font-size:12px}.up{color:var(--good)}.down{color:var(--bad)}.stable,.new_baseline{color:var(--muted)}.bar{height:6px;background:#202633;border-radius:99px;overflow:hidden;margin-top:9px}.bar>i{display:block;height:100%;background:var(--accent);border-radius:99px}.section{margin-top:18px}.history{width:100%;border-collapse:collapse}.history th,.history td{text-align:left;padding:11px 8px;border-bottom:1px solid var(--line);font-size:13px}.history th{color:var(--muted);font-weight:600}.cta{display:flex;gap:10px;margin-top:16px;flex-wrap:wrap}.btn{border:1px solid var(--line);background:#171d29;color:#fff;text-decoration:none;padding:9px 12px;border-radius:10px;font-weight:650}
.notice{margin-bottom:18px;color:var(--muted)}@media(max-width:900px){.grid{grid-template-columns:repeat(2,1fr)}}@media(max-width:620px){.grid{grid-template-columns:1fr}.top{align-items:start;flex-direction:column}.history{font-size:12px}}
</style></head>
<body><main class="wrap">
<div class="top"><div><h1>Postępy treningowe</h1><div class="sub">Historia wykonania · trendy · bezpieczna adaptacja kolejnego kroku</div></div><a class="back" href="/">← Wróć do EVOLVE</a></div>
<div id="status" class="notice">Ładowanie danych…</div>
<section class="grid" id="summary"></section>
<section class="card"><div class="label">Adaptacja ćwiczeń</div><div id="recommendations" class="list"></div></section>
<section class="card section"><div class="label">Ostatnie sesje</div><div id="history"></div></section>
<div class="cta"><button class="btn" id="apply" type="button">Zastosuj adaptację jako nową wersję planu</button><a class="btn" href="/app/training/adaptive/plan-preview">Podgląd planu 2-tygodniowego (API)</a><a class="btn" href="/">Wróć do aplikacji</a></div><div id="applyStatus" class="notice"></div>
</main>
<script>
const token=localStorage.getItem('fitai_token');
const headers=token?{Authorization:'Bearer '+token}:{};
const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
const decisionLabel=d=>({progress:'progres',maintain:'utrzymaj',reduce:'zmniejsz',insufficient_data:'brak danych'}[d]||d);
const trendLabel=d=>({up:'↗ trend wzrostowy',down:'↘ trend spadkowy',stable:'→ stabilnie',new_baseline:'nowa baza',insufficient_data:'za mało danych'}[d]||d);
async function load(){
 if(!token){status.textContent='Zaloguj się w głównym EVOLVE, aby zobaczyć swoje dane.';return}
 try{
  const [a,h]=await Promise.all([
   fetch('/app/training/adaptive/preview',{headers}),
   fetch('/app/training/sessions/history?limit=8',{headers})
  ]);
  if([a,h].some(r=>r.status===401||r.status===403)){status.textContent='Sesja logowania wygasła. Wróć do EVOLVE i zaloguj się ponownie.';return}
  const d=await a.json(), hist=await h.json();
  if(!d.has_data){status.textContent='Brak ukończonych treningów. Ukończ pierwszy trening, aby uruchomić analizę.';return}
  status.textContent=d.message;
  const progress=d.exercises.filter(e=>e.decision==='progress').length;
  const reduce=d.exercises.filter(e=>e.decision==='reduce').length;
  summary.innerHTML='<div class="card"><div class="label">Sesje analizowane</div><div class="value">'+d.sessions_analyzed+'</div></div>'+
   '<div class="card"><div class="label">Ćwiczenia</div><div class="value">'+d.exercises.length+'</div></div>'+
   '<div class="card"><div class="label">Progres</div><div class="value">'+progress+'</div></div>'+
   '<div class="card"><div class="label">Redukcja</div><div class="value">'+reduce+'</div></div>';
  recommendations.innerHTML=d.exercises.map(e=>{
   const p=e.proposed||{},c=e.current||{},s=e.recent_sessions||[];
   const completion=s.length?Math.min(100,s[0].completed_sets*20):0;
   return '<div class="row"><div><div class="name">'+esc(e.exercise_name)+' <span class="trend '+esc(e.trend)+'">'+esc(trendLabel(e.trend))+'</span></div>'+
    '<div class="meta">Teraz: '+c.sets+'×'+c.reps+(c.weight_kg?' · '+c.weight_kg+' kg':'')+' → '+p.sets+'×'+p.reps+(p.weight_kg?' · '+p.weight_kg+' kg':'')+
    ' · dane: '+esc(e.data_sufficiency)+'</div><div class="bar"><i style="width:'+completion+'%"></i></div></div>'+
    '<span class="pill '+esc(e.decision)+'">'+esc(decisionLabel(e.decision))+'</span></div>'
  }).join('')||'<div class="notice">Brak ćwiczeń w ostatnim treningu.</div>';
  history.innerHTML='<table class="history"><thead><tr><th>Data</th><th>RPE</th><th>Serie</th><th>Ukończenie</th><th>Ćwiczenia</th></tr></thead><tbody>'+
   (hist.sessions||[]).map(x=>'<tr><td>'+esc(x.session_date)+'</td><td>'+(x.final_rpe??'—')+'</td><td>'+x.completed_sets+'/'+x.planned_sets+'</td><td>'+x.completion_pct+'%</td><td>'+esc((x.exercises||[]).join(', '))+'</td></tr>').join('')+
   '</tbody></table>';
 }catch(e){status.textContent='Nie udało się pobrać danych treningowych.'}
}
document.getElementById('apply').onclick=async()=>{
 if(!token){applyStatus.textContent='Zaloguj się ponownie.';return}
 if(!confirm('Zastosować obecną adaptację jako nową wersję planu? Poprzednia wersja zostanie zachowana w historii.'))return;
 applyStatus.textContent='Zapisywanie nowej wersji planu…';
 try{
  const r=await fetch('/app/training/adaptive/apply',{method:'POST',headers:{...headers,'Content-Type':'application/json'}});
  const d=await r.json();
  if(!r.ok){applyStatus.textContent=d.detail||'Nie udało się zapisać adaptacji.';return}
  applyStatus.textContent=d.status==='unchanged'?'Plan już zawiera tę samą adaptację.':'Zapisano wersję planu v'+d.version+'. Poprzednia wersja została zachowana w historii.';
 }catch(e){applyStatus.textContent='Nie udało się zapisać adaptacji.'}
};
load();
</script></body></html>""")

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
