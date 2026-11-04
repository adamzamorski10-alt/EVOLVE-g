from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def _headers(prefix: str = "integrity") -> dict[str, str]:
    suffix = uuid.uuid4().hex[:8]
    response = client.post(
        "/auth/register",
        json={
            "email": f"{prefix}-{suffix}@example.com",
            "password": "SecurePassword123",
            "nickname": f"{prefix}_{suffix}",
            "name": "Sport Integrity",
            "age": 28,
            "height": 181.0,
            "weight": 80.0,
            "target_weight": 78.0,
            "gender": "mężczyzna",
            "goal": "performance",
            "frequency": "3-4 razy w tygodniu",
            "diet": "Balanced",
        },
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_sport_attempt_validation_idempotency_zone_and_owner_isolation():
    owner = _headers()
    other = _headers("other")
    payload = {
        "date": "2026-11-04",
        "source": "manual",
        "category": "three",
        "zone": "corner_l",
        "made": 7,
        "attempts": 10,
        "client_id": "client-shot-1",
    }
    first = client.post("/app/sport/attempt", headers=owner, json=payload)
    assert first.status_code == 200
    attempt_id = first.json()["attempt"]["id"]
    repeated = client.post("/app/sport/attempt", headers=owner, json=payload)
    assert repeated.status_code == 200
    assert repeated.json()["attempt"]["id"] == attempt_id
    assert client.post(
        "/app/sport/attempt",
        headers=owner,
        json={**payload, "client_id": "invalid", "made": 11},
    ).status_code == 422
    assert client.get("/app/sport/attempts", headers=other).json()["attempts"] == []
    assert client.delete(f"/app/sport/attempt/{attempt_id}", headers=other).status_code == 404


def test_partial_test_run_and_deterministic_ratings():
    headers = _headers("ratings")
    response = client.post(
        "/app/sport/test-run",
        headers=headers,
        json={
            "attempts": [
                {"category": "free", "made": 15, "attempts": 20, "source": "manual", "client_id": "run-free"},
                {"category": "mid", "made": 10, "attempts": 20, "source": "manual", "client_id": "run-mid"},
                {"category": "three", "zone": "top3", "made": 8, "attempts": 20, "source": "manual", "client_id": "run-three"},
                {"category": "speed", "value": 15, "unit": "seconds", "source": "manual", "client_id": "run-speed"},
            ],
        },
    )
    assert response.status_code == 200
    assert len(response.json()["attempts"]) == 4
    ratings = client.get("/app/sport/ratings", headers=headers)
    assert ratings.status_code == 200
    body = ratings.json()
    assert body["overall"] is not None
    assert body["details"]["free"]["attempts"] == 20
    assert body["details"]["defense"]["reason"] == "brak testu"
    assert body["calibration"] == {"speed": False, "jump": False}


def test_legacy_assessment_is_materialized_without_deleting_profile_data():
    headers = _headers("legacy")
    update = client.put(
        "/app/profile",
        headers=headers,
        json={
            "basketball_profile": {
                "assessmentDate": "2026-11-01",
                "assessment": {"free": {"made": 12, "attempts": 20}},
            }
        },
    )
    assert update.status_code == 200
    attempts = client.get("/app/sport/attempts", headers=headers)
    assert attempts.status_code == 200
    assert len(attempts.json()["attempts"]) == 1
    assert client.get("/app/profile", headers=headers).json()["basketball_profile"]["assessment"]["free"]["made"] == 12
