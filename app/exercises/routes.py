"""Exercise detail API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.dependencies import get_current_user
from app.database import get_session
from app.exercises.data import get_exercise, list_exercises
from app.models import UserDB

router = APIRouter(prefix="/app", tags=["exercises"])

_CONTRAINDICATION_LABELS_PL = {
    "low_back": "dolny odcinek pleców",
    "shoulder": "bark",
    "knee": "kolano",
    "wrist": "nadgarstek",
    "elbow": "łokieć",
    "neck": "szyja",
}

_EQUIPMENT_LABELS_PL = {
    "barbell": "sztanga",
    "dumbbell": "hantle",
    "bench": "ławka",
    "machine": "maszyna",
    "cable": "wyciąg",
    "bodyweight": "masa własna",
    "box": "skrzynia",
    "jump_rope": "skakanka",
    "kettlebell": "kettlebell",
    "pullup_bar": "drążek",
    "dip_station": "poręcze",
    "ab_wheel": "koło ab wheel",
    "weight_plate": "talerz",
    "bands": "gumy oporowe",
    "table_or_low_bar": "stół lub niska poręcz",
}


def _contraindications_pl(contraindications: list[str]) -> list[str]:
    return [_CONTRAINDICATION_LABELS_PL.get(c, c) for c in contraindications]


def _equipment_labels_pl(equipment: list[str]) -> list[str]:
    return [_EQUIPMENT_LABELS_PL.get(e, e) for e in equipment]


def _exercise_response(ex) -> dict:
    desc = ex.description.model_dump() if ex.description is not None else {}
    summary = desc.get("summary") or ""
    if not summary:
        summary = ex.name_pl
    return {
        "id": ex.id,
        "name_pl": ex.name_pl,
        "summary": summary,
        "setup": desc.get("setup", ""),
        "execution": desc.get("execution", []),
        "cues": desc.get("cues", []),
        "common_mistakes": desc.get("common_mistakes", []),
        "easier_note": desc.get("easier_note", ""),
        "harder_note": desc.get("harder_note", ""),
        "breathing": desc.get("breathing", ""),
        "contraindications": _contraindications_pl(ex.contraindications or []),
        "equipment": _equipment_labels_pl(ex.equipment or []),
        "level": ex.level,
        "description_status": ex.description_status,
    }


@router.get("/exercises/by-name")
def get_exercise_by_name(
    name: str = Query(..., description="name_pl lub alias ćwiczenia"),
    user: UserDB = Depends(get_current_user),
    session=Depends(get_session),
):
    key = name.strip().lower()
    for ex in list_exercises():
        if ex.name_pl.strip().lower() == key:
            return _exercise_response(ex)
        for alias in ex.aliases or []:
            if alias.strip().lower() == key:
                return _exercise_response(ex)
    raise HTTPException(status_code=404, detail="Ćwiczenie nie znalezione")


@router.get("/exercises/{exercise_id}")
def get_exercise_by_id(
    exercise_id: str,
    user: UserDB = Depends(get_current_user),
    session=Depends(get_session),
):
    ex = get_exercise(exercise_id)
    if ex is None:
        raise HTTPException(status_code=404, detail="Ćwiczenie nie znalezione")
    return _exercise_response(ex)
