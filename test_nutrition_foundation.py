from __future__ import annotations

from datetime import datetime, timedelta
import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.database import engine
from app.models import NutritionEntryDB, UserDB
from main import app

client = TestClient(app)


def _register():
    suffix = uuid.uuid4().hex[:10]
    response = client.post(
        "/auth/register",
        json={
            "email": f"nutrition-{suffix}@example.com",
            "password": "SecurePassword123",
            "nickname": f"nutrition_{suffix}",
            "name": "Nutrition Test",
            "age": 20,
            "height": 180,
            "weight": 80,
            "target_weight": 78,
            "gender": "mężczyzna",
            "goal": "weight_loss",
            "frequency": "3-4 razy w tygodniu",
            "diet": "Balanced",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_nutrition_entry_is_persisted_and_today_is_aggregated():
    token = _register()
    response = client.post(
        "/app/nutrition/entries",
        headers=_headers(token),
        json={
            "name": "Owsianka proteinowa",
            "meal_type": "breakfast",
            "calories_kcal": 450,
            "protein_g": 32,
            "carbs_g": 55,
            "fat_g": 10,
            "fiber_g": 8,
            "water_liters": 0.4,
        },
    )
    assert response.status_code == 201
    entry = response.json()
    assert entry["name"] == "Owsianka proteinowa"

    today = client.get("/app/nutrition/today", headers=_headers(token))
    assert today.status_code == 200
    payload = today.json()
    assert payload["totals"]["calories_kcal"] == 450
    assert payload["totals"]["protein_g"] == 32
    assert payload["totals"]["carbs_g"] == 55
    assert payload["totals"]["fat_g"] == 10
    assert payload["totals"]["fiber_g"] == 8
    assert payload["totals"]["water_liters"] == 0.4
    assert payload["targets"]["calories_kcal"] > 0
    assert payload["targets"]["protein_g"] > 0


def test_nutrition_entry_is_user_scoped_and_delete_is_idempotently_not_cross_user():
    owner = _register()
    other = _register()

    created = client.post(
        "/app/nutrition/entries",
        headers=_headers(owner),
        json={"name": "Obiad", "calories_kcal": 700, "protein_g": 45},
    )
    assert created.status_code == 201
    entry_id = created.json()["id"]

    forbidden_lookup = client.delete(
        f"/app/nutrition/entries/{entry_id}",
        headers=_headers(other),
    )
    assert forbidden_lookup.status_code == 404

    with Session(engine) as session:
        row = session.get(NutritionEntryDB, entry_id)
        assert row is not None
        owner_user = session.exec(select(UserDB).where(UserDB.email.like("nutrition-%@example.com"))).first()
        assert owner_user is not None


def test_nutrition_range_rejects_invalid_and_excessive_windows():
    token = _register()
    invalid = client.get(
        "/app/nutrition/entries?start_date=2026-10-10&end_date=2026-10-09",
        headers=_headers(token),
    )
    assert invalid.status_code == 422

    excessive = client.get(
        "/app/nutrition/entries?start_date=2026-01-01&end_date=2026-02-15",
        headers=_headers(token),
    )
    assert excessive.status_code == 422


def test_nutrition_payload_rejects_negative_macros():
    token = _register()
    response = client.post(
        "/app/nutrition/entries",
        headers=_headers(token),
        json={"name": "Invalid", "calories_kcal": -1},
    )
    assert response.status_code == 422
