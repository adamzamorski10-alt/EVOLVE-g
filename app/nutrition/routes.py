"""Structured nutrition intake API — deterministic, authenticated and user-scoped."""

from datetime import date, datetime, time, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field as PydanticField
from sqlmodel import Session, select

from app.auth.dependencies import get_current_user
from app.database import engine
from app.fitness.calculations import calc_calories, calc_protein
from app.models import NutritionEntryDB, UserDB

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
