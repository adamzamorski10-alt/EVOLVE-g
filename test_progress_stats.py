from __future__ import annotations

import uuid

import pytest

from app.auth import routes as auth_routes
from main import app
from fastapi.testclient import TestClient


client = TestClient(app)


@pytest.fixture(autouse=True)
def _disable_registration_rate_limit():
    previous = auth_routes.limiter.enabled
    auth_routes.limiter.enabled = False
    yield
    auth_routes.limiter.enabled = previous


def _user():
    suffix = uuid.uuid4().hex[:10]
    response = client.post(
        "/auth/register",
        json={
            "email": f"progress-{suffix}@example.com",
            "password": "SecurePassword123",
            "nickname": f"progress_{suffix}",
            "name": "Progress Test",
            "age": 25,
            "height": 180,
            "weight": 80,
            "target_weight": 78,
            "goal": "redukcja",
            "frequency": "3",
            "diet": "zbilansowana",
        },
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_progress_stats_aggregate_drills_assessment_and_goals():
    headers = _user()

    drill = client.post(
        "/app/drill-result",
        json={"drill_name": "Rzuty za 3 punkty", "attempts": 50, "made": 38, "rpe": 7},
        headers=headers,
    )
    assert drill.status_code == 200, drill.text

    assessment = client.post(
        "/app/assessment",
        json={"training_level": "intermediate", "vertical_jump_cm": 72, "sprint_30m_seconds": 4.1},
        headers=headers,
    )
    assert assessment.status_code == 200, assessment.text

    goal = client.post(
        "/app/goals",
        json={
            "goal_type": "strength",
            "title": "Wyciskanie 100 kg",
            "metric_key": "best_weight_kg",
            "baseline_value": 80,
            "target_value": 100,
            "priority": 90,
        },
        headers=headers,
    )
    assert goal.status_code == 200, goal.text

    stats = client.get("/app/stats", headers=headers)
    assert stats.status_code == 200, stats.text
    payload = stats.json()
    assert payload["shooting_stats"]["total_attempts"] == 50
    assert payload["shooting_stats"]["total_made"] == 38
    assert payload["shooting_stats"]["accuracy_pct"] == 76.0
    assert payload["assessment_history"][-1]["vertical_jump_cm"] == 72.0
    assert payload["goals"][0]["title"] == "Wyciskanie 100 kg"
