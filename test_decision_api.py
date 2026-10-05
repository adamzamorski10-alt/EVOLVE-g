from __future__ import annotations

import uuid
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def _register():
    suffix = uuid.uuid4().hex[:10]
    response = client.post(
        "/auth/register",
        json={
            "email": f"decision-api-{suffix}@example.com",
            "password": "SecurePassword123",
            "nickname": f"decision_{suffix}",
            "name": "Decision API",
            "age": 25,
            "height": 180,
            "weight": 80,
            "target_weight": 80,
            "gender": "mężczyzna",
            "goal": "performance",
            "frequency": "3",
            "diet": "balanced",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_decision_today_requires_authentication():
    response = client.get("/app/decision/today")
    assert response.status_code in {401, 403}


def test_decision_today_returns_read_only_deterministic_contract():
    token = _register()
    response = client.get("/app/decision/today", headers=_headers(token))
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["decision"] in {
        "train_as_planned",
        "reduce_training",
        "recover",
        "progress_training",
        "maintain_training",
        "insufficient_data",
    }
    assert data["algorithm_version"] == "deterministic-decision-v1"
    assert data["mutates_plan"] is False
    assert isinstance(data["reason_codes"], list)
    assert isinstance(data["supporting_goal_ids"], list)
    assert isinstance(data["supporting_session_ids"], list)


def test_decision_today_is_user_scoped():
    first = _register()
    second = _register()

    first_data = client.get(
        "/app/decision/today", headers=_headers(first)
    ).json()
    second_data = client.get(
        "/app/decision/today", headers=_headers(second)
    ).json()

    assert first_data["supporting_goal_ids"] == []
    assert second_data["supporting_goal_ids"] == []
    assert first_data["supporting_session_ids"] == []
    assert second_data["supporting_session_ids"] == []


def test_decision_today_is_idempotent_read_only():
    token = _register()

    before = client.get("/app/decision/today", headers=_headers(token))
    after = client.get("/app/decision/today", headers=_headers(token))

    assert before.status_code == after.status_code == 200
    assert before.json() == after.json()
