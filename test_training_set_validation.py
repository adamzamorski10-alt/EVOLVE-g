import pytest

from app.auth import routes as auth_routes
from test_training_execution import _context, _headers, client


@pytest.fixture(autouse=True)
def _disable_registration_rate_limit():
    previous = auth_routes.limiter.enabled
    auth_routes.limiter.enabled = False
    yield
    auth_routes.limiter.enabled = previous



def test_set_number_cannot_exceed_planned_sets():
    ctx = _context()
    started = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
    assert started.status_code == 200
    sid = started.json()["session"]["id"]
    response = client.post(
        f"/app/training/sessions/{sid}/sets",
        json={
            "exercise_key": "squat-1",
            "set_number": 4,
            "actual_reps": 5,
            "actual_weight_kg": 100,
        },
        headers=_headers(ctx["token"]),
    )
    assert response.status_code == 422



def test_analysis_endpoint_exists():
    ctx = _context()
    started = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
    assert started.status_code == 200
    sid = started.json()["session"]["id"]
    response = client.get(f"/app/training/sessions/{sid}/analysis", headers=_headers(ctx["token"]))
    assert response.status_code == 200
    assert response.json()["session_id"] == sid


def _log_set(token, sid, set_number, reps=5, weight=100, rpe=7):
    return client.post(
        f"/app/training/sessions/{sid}/sets",
        json={
            "exercise_key": "squat-1",
            "set_number": set_number,
            "actual_reps": reps,
            "actual_weight_kg": weight,
            "actual_rpe": rpe,
        },
        headers=_headers(token),
    )


def test_progression_returns_progress_after_target_completion():
    ctx = _context()
    started = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
    sid = started.json()["session"]["id"]
    for number in (1, 2, 3):
        response = _log_set(ctx["token"], sid, number)
        assert response.status_code == 200

    result = client.get(f"/app/training/sessions/{sid}/progression", headers=_headers(ctx["token"]))
    assert result.status_code == 200
    exercise = result.json()["exercises"][0]
    assert exercise["decision"] == "progress"
    assert exercise["reason_codes"] == ["TARGET_COMPLETED"]
    assert result.json()["rules"]["mutates_plan"] is False


def test_progression_maintains_after_high_rpe():
    ctx = _context()
    started = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
    sid = started.json()["session"]["id"]
    for number in (1, 2, 3):
        response = _log_set(ctx["token"], sid, number, rpe=9)
        assert response.status_code == 200

    result = client.get(f"/app/training/sessions/{sid}/progression", headers=_headers(ctx["token"]))
    assert result.status_code == 200
    assert result.json()["exercises"][0]["decision"] == "maintain"
    assert result.json()["exercises"][0]["reason_codes"] == ["HIGH_RPE"]


def test_progression_reduces_after_low_set_completion():
    ctx = _context()
    started = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
    sid = started.json()["session"]["id"]
    response = _log_set(ctx["token"], sid, 1)
    assert response.status_code == 200

    result = client.get(f"/app/training/sessions/{sid}/progression", headers=_headers(ctx["token"]))
    assert result.status_code == 200
    assert result.json()["exercises"][0]["decision"] == "reduce"
    assert result.json()["exercises"][0]["reason_codes"] == ["LOW_SET_COMPLETION"]


def test_next_plan_preview_proposes_load_change_without_mutating_plan():
    ctx = _context()
    started = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
    sid = started.json()["session"]["id"]

    for number in (1, 2, 3):
        response = _log_set(ctx["token"], sid, number, reps=5, weight=100, rpe=7)
        assert response.status_code == 200

    preview = client.get(
        f"/app/training/sessions/{sid}/next-plan-preview",
        headers=_headers(ctx["token"]),
    )
    assert preview.status_code == 200
    body = preview.json()
    assert body["plan_mutated"] is False
    exercise = body["exercises"][0]
    assert exercise["decision"] == "progress"
    assert exercise["current"]["weight_kg"] == 100
    assert exercise["proposed"]["weight_kg"] == 102.5


def test_next_plan_preview_is_user_scoped():
    first = _context()
    second = _context()
    started = client.post("/app/training/sessions/start", headers=_headers(first["token"]))
    sid = started.json()["session"]["id"]

    response = client.get(
        f"/app/training/sessions/{sid}/next-plan-preview",
        headers=_headers(second["token"]),
    )
    assert response.status_code == 404
