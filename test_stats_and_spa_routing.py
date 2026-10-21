from __future__ import annotations

import json
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_stats_by_identity_returns_json_even_for_new_user():
    response = client.get("/app/stats/test_identity_123?days=30")
    assert response.status_code == 200
    assert "application/json" in response.headers.get("content-type", "")
    data = response.json()
    assert "weight_entries" in data
    assert "training_volume" in data
    assert "diet_compliance_pct" in data
    assert "kpi" in data
    assert "xp" in data


def test_unmatched_api_routes_return_404_json_not_html():
    response = client.get("/app/unknown_api_subroute")
    assert response.status_code == 404
    assert "application/json" in response.headers.get("content-type", "")
    data = response.json()
    assert "error" in data


def test_seed_data_is_served_and_has_no_double_commas():
    response = client.get("/fitai_seed_data.js")
    assert response.status_code == 200
    content = response.text
    assert "Dragon Flag" in content
    # Ensure no empty array slots
    import re
    assert len(re.findall(r',\s*,', content)) == 0
