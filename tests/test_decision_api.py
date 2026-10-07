from __future__ import annotations

import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.auth.jwt_utils import create_access_token
from app.database import engine
from app.models import UserDB
from main import app


client = TestClient(app)


def _seed_user() -> tuple[UserDB, str]:
    suffix = uuid.uuid4().hex[:10]
    user = UserDB(
        user_key=f"test-decision:{suffix}",
        email=f"decision-{suffix}@example.com",
        nickname=f"decision_{suffix}",
        name="Decision API Test",
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
        token = create_access_token(user.id, user.email or "", user.role)
        return user, token


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_decision_today_requires_authentication():
    response = client.get("/app/decision/today")
    assert response.status_code in {401, 403}


def test_decision_today_returns_read_only_decision_for_authenticated_user():
    _, token = _seed_user()
    response = client.get("/app/decision/today", headers=_auth_headers(token))
    assert response.status_code == 200

    payload = response.json()
    assert payload["decision"] in {
        "train_as_planned",
        "reduce_training",
        "recover",
        "progress_training",
        "maintain_training",
        "insufficient_data",
    }
    assert isinstance(payload["reason_codes"], list)
    assert isinstance(payload["supporting_goal_ids"], list)
    assert isinstance(payload["supporting_session_ids"], list)
    assert payload["mutates_plan"] is False
    assert payload["algorithm_version"] == "deterministic-decision-v1"
