from __future__ import annotations

from fastapi.testclient import TestClient

from app.auth.jwt_utils import create_access_token
from app.database import engine
from app.models import UserDB
from sqlmodel import Session
from main import app

client = TestClient(app)


def _seed_user() -> tuple[UserDB, str]:
    import uuid

    suffix = uuid.uuid4().hex[:10]
    user = UserDB(
        user_key=f"test-today:{suffix}",
        email=f"today-{suffix}@example.com",
        nickname=f"today_{suffix}",
        name="Today API Test",
        age=30,
        height=180.0,
        weight=82.0,
        start_weight=82.0,
        target_weight=78.0,
        gender="mężczyzna",
        goal="weight_loss",
        frequency="3-4 razy w tygodniu",
        diet="Balanced",
        calories_target=2200,
        protein_target=180,
    )
    with Session(engine) as session:
        session.add(user)
        session.commit()
        session.refresh(user)
        return user, create_access_token(user.id, user.email or "", user.role)


def test_today_requires_authentication():
    response = client.get("/app/today")
    assert response.status_code in {401, 403}


def test_today_aggregates_decision_and_training_without_mutation():
    _, token = _seed_user()
    response = client.get(
        "/app/today",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text

    payload = response.json()
    assert payload["read_only"] is True
    assert payload["decision"]["decision"] in {
        "train_as_planned",
        "reduce_training",
        "recover",
        "progress_training",
        "maintain_training",
        "insufficient_data",
    }
    assert "training" in payload
    assert "action" in payload
    assert payload["action"]["decision"] == payload["decision"]["decision"]
    assert payload["action"]["can_start"] == payload["training"]["can_start"]
