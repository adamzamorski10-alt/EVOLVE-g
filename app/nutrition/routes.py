"""Structured nutrition intake API — deterministic, authenticated and user-scoped."""

from datetime import date, datetime, time, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field as PydanticField
from sqlmodel import Session, select
from sqlalchemy import update

from app.auth.dependencies import get_current_user
from app.database import engine
from app.fitness.calculations import calc_calories, calc_protein
from app.models import NutritionAdaptationDB, NutritionEntryDB, TrainingSessionDB, UserDB

router = APIRouter(prefix="/app/nutrition", tags=["nutrition"])


class NutritionEntryRequest(BaseModel):
    name: str = PydanticField(min_length=1, max_length=160)
    meal_type: str = PydanticField(default="other", min_length=1, max_length=40)
    consumed_at: Optional[datetime] = None
    calories_kcal: float = PydanticField(default=0, ge=0, le=10000)
    protein_g: float = PydanticField(default=0, ge=0, le=500)
    carbs_g: float = PydanticField(default=0, ge=0, le=1000)
    fat_g: float = PydanticField(default=0, ge=0, le=500)
    fiber_g: float = PydanticField(default=0, ge=0, le=300)
    water_liters: float = PydanticField(default=0, ge=0, le=20)
    notes: str = PydanticField(default="", max_length=1000)


def _owned_user(session: Session, principal) -> UserDB:
    user = session.exec(select(UserDB).where(UserDB.id == principal.id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def _date_bounds(day: date) -> tuple[datetime, datetime]:
    return datetime.combine(day, time.min), datetime.combine(day + timedelta(days=1), time.min)


def _summary(entries: list[NutritionEntryDB], user: UserDB, day: date) -> dict:
    calories = round(sum(e.calories_kcal for e in entries), 1)
    protein = round(sum(e.protein_g for e in entries), 1)
    carbs = round(sum(e.carbs_g for e in entries), 1)
    fat = round(sum(e.fat_g for e in entries), 1)
    fiber = round(sum(e.fiber_g for e in entries), 1)
    water = round(sum(e.water_liters for e in entries), 2)
    calorie_target = float(user.calories_target or calc_calories(user))
    protein_target = float(user.protein_target or calc_protein(user))
    return {
        "date": day.isoformat(),
        "entries": [e.to_dict() for e in entries],
        "totals": {
            "calories_kcal": calories,
            "protein_g": protein,
            "carbs_g": carbs,
            "fat_g": fat,
            "fiber_g": fiber,
            "water_liters": water,
        },
        "targets": {
            "calories_kcal": calorie_target,
            "protein_g": protein_target,
        },
        "remaining": {
            "calories_kcal": round(max(0, calorie_target - calories), 1),
            "protein_g": round(max(0, protein_target - protein), 1),
        },
    }


@router.post("/entries", status_code=201)
def create_nutrition_entry(
    payload: NutritionEntryRequest,
    current_user=Depends(get_current_user),
):
    with Session(engine) as session:
        user = _owned_user(session, current_user)
        entry = NutritionEntryDB(
            user_id=user.id,
            consumed_at=payload.consumed_at or datetime.now(),
            meal_type=payload.meal_type.strip(),
            name=payload.name.strip(),
            calories_kcal=payload.calories_kcal,
            protein_g=payload.protein_g,
            carbs_g=payload.carbs_g,
            fat_g=payload.fat_g,
            fiber_g=payload.fiber_g,
            water_liters=payload.water_liters,
            notes=payload.notes.strip(),
        )
        session.add(entry)
        session.commit()
        session.refresh(entry)
        return entry.to_dict()


@router.get("/entries")
def list_nutrition_entries(
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    current_user=Depends(get_current_user),
):
    start = start_date or date.today()
    end = end_date or start
    if end < start:
        raise HTTPException(status_code=422, detail="end_date must be on or after start_date")
    if (end - start).days > 31:
        raise HTTPException(status_code=422, detail="Date range cannot exceed 31 days")
    start_dt, _ = _date_bounds(start)
    _, end_dt = _date_bounds(end)
    with Session(engine) as session:
        user = _owned_user(session, current_user)
        entries = session.exec(
            select(NutritionEntryDB)
            .where(NutritionEntryDB.user_id == user.id)
            .where(NutritionEntryDB.consumed_at >= start_dt)
            .where(NutritionEntryDB.consumed_at < end_dt)
            .order_by(NutritionEntryDB.consumed_at.asc(), NutritionEntryDB.id.asc())
        ).all()
        return {"start_date": start.isoformat(), "end_date": end.isoformat(), "entries": [e.to_dict() for e in entries]}


@router.get("/today")
def nutrition_today(current_user=Depends(get_current_user)):
    day = date.today()
    start_dt, end_dt = _date_bounds(day)
    with Session(engine) as session:
        user = _owned_user(session, current_user)
        entries = session.exec(
            select(NutritionEntryDB)
            .where(NutritionEntryDB.user_id == user.id)
            .where(NutritionEntryDB.consumed_at >= start_dt)
            .where(NutritionEntryDB.consumed_at < end_dt)
            .order_by(NutritionEntryDB.consumed_at.asc(), NutritionEntryDB.id.asc())
        ).all()
        return _summary(entries, user, day)


@router.delete("/entries/{entry_id}")
def delete_nutrition_entry(entry_id: str, current_user=Depends(get_current_user)):
    with Session(engine) as session:
        user = _owned_user(session, current_user)
        entry = session.exec(
            select(NutritionEntryDB)
            .where(NutritionEntryDB.id == entry_id)
            .where(NutritionEntryDB.user_id == user.id)
        ).first()
        if not entry:
            raise HTTPException(status_code=404, detail="Nutrition entry not found")
        session.delete(entry)
        session.commit()
        return {"deleted": True, "id": entry_id}


@router.get("/adherence")
def nutrition_adherence(
    days: int = Query(default=7, ge=1, le=28),
    current_user=Depends(get_current_user),
):
    """Return deterministic adherence over logged nutrition days.

    Missing days are excluded from adherence denominators; the endpoint never
    treats a day with no intake record as a failed nutrition day.
    """
    end_day = date.today()
    start_day = end_day - timedelta(days=days - 1)
    start_dt, _ = _date_bounds(start_day)
    _, end_dt = _date_bounds(end_day)

    with Session(engine) as session:
        user = _owned_user(session, current_user)
        entries = session.exec(
            select(NutritionEntryDB)
            .where(NutritionEntryDB.user_id == user.id)
            .where(NutritionEntryDB.consumed_at >= start_dt)
            .where(NutritionEntryDB.consumed_at < end_dt)
            .order_by(NutritionEntryDB.consumed_at.asc(), NutritionEntryDB.id.asc())
        ).all()

        calorie_target = float(user.calories_target or calc_calories(user))
        protein_target = float(user.protein_target or calc_protein(user))
        by_day: dict[date, list[NutritionEntryDB]] = {}
        for entry in entries:
            entry_day = entry.consumed_at.date()
            by_day.setdefault(entry_day, []).append(entry)

        daily = []
        for entry_day in sorted(by_day):
            day_entries = by_day[entry_day]
            kcal = round(sum(e.calories_kcal for e in day_entries), 1)
            protein = round(sum(e.protein_g for e in day_entries), 1)
            kcal_ratio = kcal / calorie_target if calorie_target else 0
            protein_ratio = protein / protein_target if protein_target else 0
            daily.append({
                "date": entry_day.isoformat(),
                "calories_kcal": kcal,
                "protein_g": protein,
                "calorie_ratio": round(kcal_ratio, 3),
                "protein_ratio": round(protein_ratio, 3),
                "calorie_target_met": 0.9 <= kcal_ratio <= 1.1 if calorie_target else False,
                "protein_target_met": protein_ratio >= 0.9 if protein_target else False,
            })

        logged_days = len(daily)
        calorie_met_days = sum(1 for item in daily if item["calorie_target_met"])
        protein_met_days = sum(1 for item in daily if item["protein_target_met"])
        avg_kcal = round(sum(item["calories_kcal"] for item in daily) / logged_days, 1) if logged_days else 0
        avg_protein = round(sum(item["protein_g"] for item in daily) / logged_days, 1) if logged_days else 0

        return {
            "start_date": start_day.isoformat(),
            "end_date": end_day.isoformat(),
            "window_days": days,
            "logged_days": logged_days,
            "targets": {
                "calories_kcal": calorie_target,
                "protein_g": protein_target,
            },
            "adherence": {
                "calorie_pct": round((calorie_met_days / logged_days) * 100, 1) if logged_days else 0,
                "protein_pct": round((protein_met_days / logged_days) * 100, 1) if logged_days else 0,
            },
            "averages": {
                "calories_kcal": avg_kcal,
                "protein_g": avg_protein,
            },
            "daily": daily,
        }


@router.get("/response")
def nutrition_response(
    days: int = Query(default=7, ge=3, le=28),
    current_user=Depends(get_current_user),
):
    """Explain nutrition adherence deterministically without mutating targets.

    A response requires at least 3 logged days. It is intentionally advisory:
    it does not change profile targets or training plans.
    """
    end_day = date.today()
    start_day = end_day - timedelta(days=days - 1)
    start_dt, _ = _date_bounds(start_day)
    _, end_dt = _date_bounds(end_day)

    with Session(engine) as session:
        user = _owned_user(session, current_user)
        entries = session.exec(
            select(NutritionEntryDB)
            .where(NutritionEntryDB.user_id == user.id)
            .where(NutritionEntryDB.consumed_at >= start_dt)
            .where(NutritionEntryDB.consumed_at < end_dt)
            .order_by(NutritionEntryDB.consumed_at.asc(), NutritionEntryDB.id.asc())
        ).all()

        calorie_target = float(user.calories_target or calc_calories(user))
        protein_target = float(user.protein_target or calc_protein(user))
        by_day: dict[date, list[NutritionEntryDB]] = {}
        for entry in entries:
            by_day.setdefault(entry.consumed_at.date(), []).append(entry)

        daily = []
        for entry_day, day_entries in sorted(by_day.items()):
            kcal = sum(e.calories_kcal for e in day_entries)
            protein = sum(e.protein_g for e in day_entries)
            daily.append((entry_day, kcal, protein))

        logged_days = len(daily)
        if logged_days < 3:
            return {
                "status": "insufficient_data",
                "days_requested": days,
                "logged_days": logged_days,
                "minimum_logged_days": 3,
                "signal": "collect_more_data",
                "message": "Potrzeba co najmniej 3 zalogowanych dni, aby wyznaczyć reakcję żywieniową.",
                "target_change": None,
            }

        avg_kcal = sum(row[1] for row in daily) / logged_days
        avg_protein = sum(row[2] for row in daily) / logged_days
        kcal_ratio = avg_kcal / calorie_target if calorie_target else 0
        protein_ratio = avg_protein / protein_target if protein_target else 0

        if kcal_ratio < 0.85:
            signal = "consistently_under_target"
            message = "Średnia podaż energii jest wyraźnie poniżej celu."
        elif kcal_ratio > 1.15:
            signal = "consistently_over_target"
            message = "Średnia podaż energii jest wyraźnie powyżej celu."
        else:
            signal = "calories_near_target"
            message = "Średnia podaż energii znajduje się blisko celu."

        if protein_ratio < 0.90:
            protein_signal = "protein_below_target"
        elif protein_ratio > 1.20:
            protein_signal = "protein_above_target"
        else:
            protein_signal = "protein_near_target"

        return {
            "status": "ready",
            "days_requested": days,
            "logged_days": logged_days,
            "targets": {"calories_kcal": calorie_target, "protein_g": protein_target},
            "averages": {
                "calories_kcal": round(avg_kcal, 1),
                "protein_g": round(avg_protein, 1),
                "calorie_ratio": round(kcal_ratio, 3),
                "protein_ratio": round(protein_ratio, 3),
            },
            "signal": signal,
            "protein_signal": protein_signal,
            "message": message,
            "target_change": None,
            "adaptation_allowed": False,
        }


def _adaptation_evidence(session: Session, user: UserDB, days: int) -> dict:
    end_day = date.today()
    start_day = end_day - timedelta(days=days - 1)
    start_dt, _ = _date_bounds(start_day)
    _, end_dt = _date_bounds(end_day)
    entries = session.exec(
        select(NutritionEntryDB)
        .where(NutritionEntryDB.user_id == user.id)
        .where(NutritionEntryDB.consumed_at >= start_dt)
        .where(NutritionEntryDB.consumed_at < end_dt)
    ).all()
    by_day: dict[date, list[NutritionEntryDB]] = {}
    for entry in entries:
        by_day.setdefault(entry.consumed_at.date(), []).append(entry)
    calorie_target = int(user.calories_target or calc_calories(user))
    protein_target = int(user.protein_target or calc_protein(user))
    daily = []
    for entry_day, day_entries in sorted(by_day.items()):
        daily.append((
            entry_day,
            sum(e.calories_kcal for e in day_entries),
            sum(e.protein_g for e in day_entries),
        ))
    training_sessions = session.exec(
        select(TrainingSessionDB)
        .where(TrainingSessionDB.user_id == user.id)
        .where(TrainingSessionDB.session_date >= start_day)
        .where(TrainingSessionDB.session_date <= end_day)
        .where(TrainingSessionDB.status == "completed")
    ).all()
    return {
        "start_date": start_day,
        "end_date": end_day,
        "daily": daily,
        "logged_days": len(daily),
        "training_sessions": len(training_sessions),
        "calorie_target": calorie_target,
        "protein_target": protein_target,
    }


@router.get("/adaptation")
def nutrition_adaptation_preview(
    days: int = Query(default=14, ge=7, le=28),
    current_user=Depends(get_current_user),
):
    """Return a bounded adaptation proposal; never mutates the user."""
    with Session(engine) as session:
        user = _owned_user(session, current_user)
        evidence = _adaptation_evidence(session, user, days)
        logged = evidence["logged_days"]
        sessions = evidence["training_sessions"]
        base = evidence["calorie_target"]
        protein = evidence["protein_target"]

        if logged < 7:
            return {
                "status": "insufficient_data",
                "logged_days": logged,
                "training_sessions": sessions,
                "minimum_logged_days": 7,
                "minimum_training_sessions": 2,
                "adaptation_allowed": False,
                "proposed_calories_kcal": base,
                "proposed_protein_g": protein,
                "change_kcal": 0,
                "reason": "Potrzeba co najmniej 7 dni danych żywieniowych.",
            }
        if sessions < 2:
            return {
                "status": "insufficient_training_context",
                "logged_days": logged,
                "training_sessions": sessions,
                "minimum_logged_days": 7,
                "minimum_training_sessions": 2,
                "adaptation_allowed": False,
                "proposed_calories_kcal": base,
                "proposed_protein_g": protein,
                "change_kcal": 0,
                "reason": "Potrzeba co najmniej 2 ukończonych sesji treningowych w tym samym oknie.",
            }

        avg_kcal = sum(row[1] for row in evidence["daily"]) / logged
        avg_protein = sum(row[2] for row in evidence["daily"]) / logged
        ratio = avg_kcal / base if base else 1
        protein_ratio = avg_protein / protein if protein else 1

        if ratio < 0.85:
            change = 100
            direction = "increase"
            reason = "Średnia podaż energii jest trwale poniżej celu przy wystarczającym kontekście treningowym."
        elif ratio > 1.15:
            change = -100
            direction = "decrease"
            reason = "Średnia podaż energii jest trwale powyżej celu przy wystarczającym kontekście treningowym."
        else:
            change = 0
            direction = "hold"
            reason = "Średnia podaż energii pozostaje w kontrolowanym zakresie; brak podstaw do zmiany."

        proposed = max(1200, min(5000, base + change))
        return {
            "status": "ready",
            "logged_days": logged,
            "training_sessions": sessions,
            "average_calories_kcal": round(avg_kcal, 1),
            "average_protein_g": round(avg_protein, 1),
            "calorie_ratio": round(ratio, 3),
            "protein_ratio": round(protein_ratio, 3),
            "base_calories_kcal": base,
            "base_protein_g": protein,
            "proposed_calories_kcal": proposed,
            "proposed_protein_g": protein,
            "change_kcal": proposed - base,
            "direction": direction,
            "reason": reason,
            "adaptation_allowed": change != 0,
            "max_change_kcal": 100,
        }


@router.post("/adaptation/apply")
def apply_nutrition_adaptation(
    days: int = Query(default=14, ge=7, le=28),
    current_user=Depends(get_current_user),
):
    """Apply one bounded calorie adaptation with optimistic concurrency."""
    with Session(engine) as session:
        user = _owned_user(session, current_user)
        evidence = _adaptation_evidence(session, user, days)
        logged = evidence["logged_days"]
        sessions = evidence["training_sessions"]
        base = evidence["calorie_target"]
        protein = evidence["protein_target"]

        if logged < 7 or sessions < 2:
            raise HTTPException(status_code=422, detail="Insufficient evidence for nutrition adaptation")

        avg_kcal = sum(row[1] for row in evidence["daily"]) / logged
        ratio = avg_kcal / base if base else 1
        if ratio < 0.85:
            change, direction = 100, "increase"
            reason = "Średnia podaż energii jest trwale poniżej celu."
        elif ratio > 1.15:
            change, direction = -100, "decrease"
            reason = "Średnia podaż energii jest trwale powyżej celu."
        else:
            return {
                "status": "no_change",
                "calories_target": base,
                "protein_target": protein,
                "change_kcal": 0,
                "adaptation_allowed": False,
            }

        proposed = max(1200, min(5000, base + change))
        result = session.exec(
            update(UserDB)
            .where(UserDB.id == user.id)
            .where(UserDB.calories_target == base)
            .values(calories_target=proposed, updated_at=datetime.now())
        )
        if result.rowcount != 1:
            session.rollback()
            raise HTTPException(status_code=409, detail="Nutrition target changed concurrently; retry preview")

        audit = NutritionAdaptationDB(
            user_id=user.id,
            evidence_days=logged,
            training_sessions=sessions,
            base_calories_kcal=base,
            proposed_calories_kcal=proposed,
            base_protein_g=protein,
            proposed_protein_g=protein,
            direction=direction,
            reason=reason,
            status="applied",
        )
        session.add(audit)
        session.commit()
        return {
            "status": "applied",
            "adaptation_id": audit.id,
            "calories_target": proposed,
            "protein_target": protein,
            "change_kcal": change,
            "direction": direction,
            "max_change_kcal": 100,
        }
