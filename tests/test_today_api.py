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
    if payload["action"]["safety_blocked"]:
        assert payload["action"]["can_start"] is False
    else:
        assert payload["action"]["can_start"] == payload["training"]["can_start"]
    assert payload["status"] == payload["action"]["decision"] if "decision" in payload["action"] else payload["status"] == payload["action"]["key"]


def test_today_action_contract_blocks_start_on_recovery_override(monkeypatch):
    from app import today_routes

    user, token = _seed_user()

    monkeypatch.setattr(
        today_routes,
        "decision_today",
        lambda user, db: {
            "decision": "recover",
            "priority": "critical",
            "action": "Prioritize recovery and avoid normal training volume.",
            "reason_codes": ["RECOVERY_OVERRIDE"],
            "supporting_goal_ids": [],
            "supporting_session_ids": [],
            "constraints": ["reduce_volume_50"],
            "sufficient_data": True,
            "algorithm_version": "deterministic-decision-v1",
            "mutates_plan": False,
        },
    )

    response = client.get("/app/today", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, response.text
    assert response.json()["action"]["safety_blocked"] is True
    assert response.json()["action"]["can_start"] is False


def test_today_cross_user_isolation(monkeypatch):
    from app import today_routes

    user_a, token_a = _seed_user()
    user_b, token_b = _seed_user()

    def user_scoped_decision(user, db):
        return {
            "decision": "maintain_training",
            "priority": "normal",
            "action": "User-scoped decision.",
            "reason_codes": ["USER_SCOPED"],
            "supporting_goal_ids": [str(user.id)],
            "supporting_session_ids": [],
            "constraints": [],
            "sufficient_data": True,
            "algorithm_version": "deterministic-decision-v1",
            "mutates_plan": False,
        }

    monkeypatch.setattr(today_routes, "decision_today", user_scoped_decision)

    response_a = client.get("/app/today", headers={"Authorization": f"Bearer {token_a}"})
    response_b = client.get("/app/today", headers={"Authorization": f"Bearer {token_b}"})

    assert response_a.status_code == 200
    assert response_b.status_code == 200
    payload_a = response_a.json()
    payload_b = response_b.json()
    assert payload_a["evidence"]["goal_ids"] == [str(user_a.id)]
    assert payload_b["evidence"]["goal_ids"] == [str(user_b.id)]
    assert payload_a["evidence"]["goal_ids"] != payload_b["evidence"]["goal_ids"]


def test_today_exposes_stable_semantic_contract():
    _, token = _seed_user()
    response = client.get("/app/today", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, response.text
    payload = response.json()

    assert set(payload) >= {
        "date",
        "status",
        "primary_action",
        "explanation",
        "safety",
        "workout",
        "evidence",
        "data_quality",
        "read_only",
    }
    assert payload["primary_action"]["key"] == payload["status"]
    assert payload["read_only"] is True
