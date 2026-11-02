from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def _headers() -> dict[str, str]:
    suffix = uuid.uuid4().hex[:8]
    response = client.post(
        "/auth/register",
        json={
            "email": f"sport-drills-{suffix}@example.com",
            "password": "SecurePassword123",
            "nickname": f"sportdrill_{suffix}",
            "name": "Sport Drill Test",
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


def test_drill_search_and_target_bonus():
    headers = _headers()

    search = client.get("/app/drills/search?q=rzut&sport=koszykówka&category=rzuty", headers=headers)
    assert search.status_code == 200
    catalog = search.json()["catalog_drills"]
    assert any(item["name"] == "Rzuty wolne — seria 10" for item in catalog)

    logged = client.post(
        "/app/drill-result",
        headers=headers,
        json={
            "drill_name": "Rzuty wolne — seria 10",
            "drill_sport": "koszykówka",
            "drill_category": "rzuty",
            "target_pct": 80,
            "success_count": 80,
            "total_attempts": 100,
            "rpe": 7,
        },
    )
    assert logged.status_code == 200
    payload = logged.json()
    assert payload["accuracy_pct"] == 80
    assert payload["target_reached"] is True
    assert payload["xp_earned"] == 35
    assert payload["drill"]["target_pct"] == 80

    history_search = client.get("/app/drills/search?q=rzut", headers=headers)
    assert history_search.status_code == 200
    assert history_search.json()["user_drills"][0]["total_sessions"] == 1


def test_drill_result_can_be_deleted_only_by_owner():
    headers = _headers()
    logged = client.post(
        "/app/drill-result",
        headers=headers,
        json={
            "drill_name": "Test usuwania",
            "drill_sport": "koszykówka",
            "drill_category": "rzuty",
            "success_count": 5,
            "total_attempts": 10,
            "rpe": 5,
        },
    )
    assert logged.status_code == 200
    result_id = logged.json()["drill"]["id"]

    deleted = client.delete(f"/app/drill-result/{result_id}", headers=headers)
    assert deleted.status_code == 200
    assert client.delete(f"/app/drill-result/{result_id}", headers=headers).status_code == 404
