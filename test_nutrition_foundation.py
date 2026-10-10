from __future__ import annotations

from datetime import datetime, timedelta
import uuid
from pathlib import Path
import pytest

from app.auth import routes as auth_routes

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.database import engine
from app.models import NutritionAdaptationDB, NutritionEntryDB, TrainingSessionDB, UserDB
from main import app

client = TestClient(app)


ROOT = Path(__file__).parent


@pytest.fixture(autouse=True)
def _disable_registration_rate_limit():
    previous = auth_routes.limiter.enabled
    auth_routes.limiter.enabled = False
    yield
    auth_routes.limiter.enabled = previous


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


def test_nutrition_adherence_excludes_unlogged_days_and_uses_bounded_rules():
    token = _register()
    today = datetime.now()
    today_payload = client.get("/app/nutrition/today", headers=_headers(token)).json()
    target_kcal = float(today_payload["targets"]["calories_kcal"])
    target_protein = float(today_payload["targets"]["protein_g"])
    for day_offset, kcal, protein in [(2, target_kcal, target_protein), (1, target_kcal * 0.25, target_protein * 0.25)]:
        response = client.post(
            "/app/nutrition/entries",
            headers=_headers(token),
            json={
                "name": f"Meal {day_offset}",
                "consumed_at": (today - timedelta(days=day_offset)).isoformat(),
                "calories_kcal": kcal,
                "protein_g": protein,
            },
        )
        assert response.status_code == 201

    response = client.get("/app/nutrition/adherence?days=7", headers=_headers(token))
    assert response.status_code == 200
    payload = response.json()
    assert payload["window_days"] == 7
    assert payload["logged_days"] == 2
    assert len(payload["daily"]) == 2
    assert payload["daily"][0]["calorie_target_met"] is True
    assert payload["daily"][0]["protein_target_met"] is True
    assert payload["daily"][1]["calorie_target_met"] is False
    assert payload["daily"][1]["protein_target_met"] is False
    assert payload["adherence"]["calorie_pct"] == 50.0
    assert payload["adherence"]["protein_pct"] == 50.0


def test_nutrition_adherence_days_are_bounded():
    token = _register()
    response = client.get("/app/nutrition/adherence?days=29", headers=_headers(token))
    assert response.status_code == 422


def test_nutrition_response_requires_evidence_and_never_mutates_target():
    token = _register()
    response = client.post(
        "/app/nutrition/entries",
        headers=_headers(token),
        json={"name": "Evidence day", "calories_kcal": 1000, "protein_g": 50},
    )
    assert response.status_code == 201

    insufficient = client.get("/app/nutrition/response?days=7", headers=_headers(token))
    assert insufficient.status_code == 200
    assert insufficient.json()["status"] == "insufficient_data"
    assert insufficient.json()["adaptation_allowed"] is False

    before = client.get("/app/nutrition/today", headers=_headers(token)).json()["targets"]
    assert before["calories_kcal"] > 0
    assert before["protein_g"] > 0
    after = client.get("/app/nutrition/today", headers=_headers(token)).json()["targets"]
    assert after == before


def test_nutrition_ui_contract_is_native_and_user_scoped():
    source = (ROOT / "app" / "__init__.py").read_text(encoding="utf-8")
    assert 'id="tab-diet"' in source
    assert 'id="nutritionSummary"' in source
    assert 'loadEvolveNutrition' in source
    assert '/app/nutrition/today' in source
    assert '/app/nutrition/response?days=7' in source
    assert '/app/nutrition/entries' in source
    assert 'Authorization: "Bearer " + token' in source
    assert 'adaptation_allowed' in source
    assert 'window.showTab = wrappedShowTab' in source


def test_nutrition_adaptation_requires_evidence_and_is_bounded_and_audited():
    token = _register()
    today = datetime.now()
    with Session(engine) as session:
        user = session.exec(select(UserDB).where(UserDB.email.like("nutrition-%@example.com")).order_by(UserDB.created_at.desc())).first()
        assert user is not None
        base = user.calories_target or 2000
        for offset in range(7):
            session.add(NutritionEntryDB(
                user_id=user.id,
                consumed_at=today - timedelta(days=offset),
                meal_type="meal",
                name=f"Evidence {offset}",
                calories_kcal=base * 0.75,
                protein_g=(user.protein_target or 150),
            ))
        for offset in (2, 5):
            session.add(TrainingSessionDB(
                user_id=user.id,
                session_date=(today - timedelta(days=offset)).date(),
                status="completed",
                planned_snapshot_json="{}",
                completed_at=today - timedelta(days=offset),
            ))
        session.commit()

    preview = client.get("/app/nutrition/adaptation?days=14", headers=_headers(token))
    assert preview.status_code == 200
    data = preview.json()
    assert data["status"] == "ready"
    assert data["adaptation_allowed"] is True
    assert data["change_kcal"] == 100
    assert data["max_change_kcal"] == 100
    assert data["proposed_protein_g"] == data["base_protein_g"]

    applied = client.post("/app/nutrition/adaptation/apply?days=14", headers=_headers(token))
    assert applied.status_code == 200
    result = applied.json()
    assert result["status"] == "applied"
    assert result["change_kcal"] == 100

    with Session(engine) as session:
        user = session.exec(select(UserDB).where(UserDB.email.like("nutrition-%@example.com")).order_by(UserDB.created_at.desc())).first()
        assert user.calories_target == data["proposed_calories_kcal"]
        audit = session.exec(
            select(NutritionAdaptationDB)
            .where(NutritionAdaptationDB.user_id == user.id)
        ).all()
        assert len(audit) == 1


def test_nutrition_adaptation_rejects_insufficient_evidence():
    token = _register()
    response = client.post(
        "/app/nutrition/adaptation/apply?days=14",
        headers=_headers(token),
    )
    assert response.status_code == 422


def test_nutrition_adaptation_ui_contract_is_explicit_and_bounded():
    source = (ROOT / "app" / "__init__.py").read_text(encoding="utf-8")
    assert '/app/nutrition/adaptation?days=14' in source
    assert '/app/nutrition/adaptation/apply?days=14' in source
    assert 'Zastosuj zmianę' in source
    assert 'adaptation_allowed' in source
    assert 'applyButton.disabled = true' in source
