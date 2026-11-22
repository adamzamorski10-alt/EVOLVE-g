"""Ukierunkowane testy dla endpointów planu (GET/PUT /app/plan/current).

Weryfikują契约, na którym opiera się frontend (modal edycji, spójność harmonogramu).
"""
from __future__ import annotations

import uuid
from datetime import date

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.auth.jwt_utils import create_access_token
from app.database import engine
from app.models import UserDB
from main import app

client = TestClient(app)

_DAY_LABELS_PL = {0: "Pon", 1: "Wt", 2: "Śr", 3: "Czw", 4: "Pt", 5: "Sob", 6: "Niedz"}


def _seed_user(suffix: str | None = None) -> tuple[UserDB, str]:
    suffix = suffix or uuid.uuid4().hex[:10]
    user = UserDB(
        user_key=f"test-plan-curr:{suffix}",
        email=f"plan-curr-{suffix}@example.com",
        nickname=f"plan_curr_{suffix}",
        name="Plan Current Test",
        age=30,
        height=180.0,
        weight=82.0,
        start_weight=82.0,
        target_weight=78.0,
        gender="mężczyzna",
        goal="Budowa masy mięśniowej",
        frequency="3-4",
        diet="zbilansowana",
    )
    with Session(engine) as session:
        session.add(user)
        session.commit()
        session.refresh(user)
        token = create_access_token(user.id, user.email or "", user.role)
        return user, token


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _weekly_plan(today_label: str, with_exercises: bool = True) -> dict:
    workout = {
        "title": "Trening siłowy",
        "focus": "klatka",
        "exercises": [],
        "day_type": "strength",
    }
    if with_exercises:
        workout["exercises"] = [
            {
                "name": "Wyciskanie hantlami leżąc",
                "sets": 3,
                "reps": 10,
                "weight": 20,
                "muscle_group": "klatka",
            },
            {
                "name": "Wiosłowanie hantlem jednorącz",
                "sets": 3,
                "reps": 10,
                "weight": 15,
                "muscle_group": "plecy",
            },
        ]
    return {
        "days": [
            {
                "day": today_label,
                "day_type": "strength",
                "workout": workout,
                "meals": [],
                "is_sport_session": False,
                "macros": {},
            },
            {
                "day": "Wt",
                "day_type": "rest",
                "workout": {"title": "", "focus": "", "exercises": [], "day_type": "rest"},
                "meals": [],
                "is_sport_session": False,
                "macros": {},
            },
        ],
        "diet": {today_label: []},
        "training": {
            today_label: workout.get("exercises", []),
            "Wt": [],
        },
    }


def test_get_plan_current_returns_empty_when_no_plan_saved():
    """GET /app/plan/current zwraca pustą strukturę gdy brak zapis planu."""
    user, token = _seed_user()
    resp = client.get("/app/plan/current", headers=_auth_headers(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["source"] == "empty"
    assert data["days"] == []
    # Pusta struktura zwraca diet="" i training="" (stringi), nie {} — patrz backend _EMPTY
    assert data["diet"] == ""
    assert data["training"] == ""


def test_put_then_get_plan_current_roundtrip():
    """PUT /app/plan/current zapisuje plan, GET go zwraca z day_type i ćwiczeniami."""
    user, token = _seed_user()
    today = _DAY_LABELS_PL[date.today().weekday()]
    plan = _weekly_plan(today, with_exercises=True)

    save_resp = client.put(
        "/app/plan/current",
        json={"plan": plan},
        headers=_auth_headers(token),
    )
    assert save_resp.status_code == 200, save_resp.text

    get_resp = client.get("/app/plan/current", headers=_auth_headers(token))
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["source"] == "database"
    assert len(data["days"]) == 2

    today_entry = next(d for d in data["days"] if d["day"] == today)
    assert today_entry["day_type"] == "strength"
    assert len(today_entry["workout"]["exercises"]) == 2
    assert today_entry["workout"]["exercises"][0]["name"] == "Wyciskanie hantlami leżąc"

    rest_entry = next(d for d in data["days"] if d["day"] == "Wt")
    assert rest_entry["day_type"] == "rest"
    assert rest_entry["workout"]["exercises"] == []


def test_put_plan_current_rejects_invalid_payload():
    """PUT /app/plan/current odrzuca nieprawidłowy payload (plan nie jest obiektem)."""
    user, token = _seed_user()
    resp = client.put(
        "/app/plan/current",
        json={"plan": "not-an-object"},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 422


def test_plan_current_preserves_days_structure_for_frontend_editor():
    """Struktura zwracana przez GET pozwala odtworzyć konfigurację edytora (split, dni, ćwiczenia)."""
    user, token = _seed_user()
    today = _DAY_LABELS_PL[date.today().weekday()]
    plan = _weekly_plan(today, with_exercises=True)

    client.put(
        "/app/plan/current",
        json={"plan": plan},
        headers=_auth_headers(token),
    )

    data = client.get("/app/plan/current", headers=_auth_headers(token)).json()
    days_by_name = {d["day"]: d for d in data["days"]}

    # Dzień treningowy ma day_type=strong i ćwiczenia
    assert days_by_name[today]["day_type"] == "strength"
    assert len(days_by_name[today]["workout"]["exercises"]) == 2

    # Dzień odpoczynku ma day_type=rest i brak ćwiczeń
    assert days_by_name["Wt"]["day_type"] == "rest"
    assert days_by_name["Wt"]["workout"]["exercises"] == []
