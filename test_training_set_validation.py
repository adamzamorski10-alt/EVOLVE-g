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


def test_training_history_is_user_scoped_and_returns_completed_sessions():
    ctx = _context()
    started = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
    assert started.status_code == 200
    sid = started.json()["session"]["id"]
    for number in (1, 2, 3):
        assert _log_set(ctx["token"], sid, number).status_code == 200
    completed = client.post(
        f"/app/training/sessions/{sid}/complete",
        json={"final_rpe": 7, "notes": "test"},
        headers=_headers(ctx["token"]),
    )
    assert completed.status_code == 200

    history = client.get("/app/training/sessions/history", headers=_headers(ctx["token"]))
    assert history.status_code == 200
    body = history.json()
    assert body["count"] >= 1
    assert any(item["session_id"] == sid for item in body["sessions"])


def test_exercise_history_is_user_scoped():
    first = _context()
    second = _context()
    started = client.post("/app/training/sessions/start", headers=_headers(first["token"]))
    assert started.status_code == 200
    sid = started.json()["session"]["id"]
    for number in (1, 2, 3):
        assert _log_set(first["token"], sid, number).status_code == 200
    assert client.post(
        f"/app/training/sessions/{sid}/complete",
        json={"final_rpe": 7},
        headers=_headers(first["token"]),
    ).status_code == 200

    own = client.get("/app/training/exercises/squat-1/history", headers=_headers(first["token"]))
    foreign = client.get("/app/training/exercises/squat-1/history", headers=_headers(second["token"]))
    assert own.status_code == 200
    assert own.json()["count"] >= 1
    assert foreign.status_code == 200
    assert foreign.json()["count"] == 0


def test_adaptive_preview_aggregates_recent_training_without_mutating_plan():
    ctx = _context()
    started = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
    assert started.status_code == 200
    sid = started.json()["session"]["id"]
    for number in (1, 2, 3):
        assert _log_set(ctx["token"], sid, number, reps=5, weight=100, rpe=7).status_code == 200
    assert client.post(
        f"/app/training/sessions/{sid}/complete",
        json={"final_rpe": 7},
        headers=_headers(ctx["token"]),
    ).status_code == 200

    preview = client.get("/app/training/adaptive/preview", headers=_headers(ctx["token"]))
    assert preview.status_code == 200
    body = preview.json()
    assert body["has_data"] is True
    assert body["sessions_analyzed"] >= 1
    assert body["plan_mutated"] is False
    assert body["exercises"][0]["proposed"]["weight_kg"] == 102.5


def test_adaptive_preview_is_user_scoped():
    first = _context()
    second = _context()
    started = client.post("/app/training/sessions/start", headers=_headers(first["token"]))
    sid = started.json()["session"]["id"]
    for number in (1, 2, 3):
        assert _log_set(first["token"], sid, number).status_code == 200
    assert client.post(
        f"/app/training/sessions/{sid}/complete",
        json={"final_rpe": 7},
        headers=_headers(first["token"]),
    ).status_code == 200

    own = client.get("/app/training/adaptive/preview", headers=_headers(first["token"]))
    foreign = client.get("/app/training/adaptive/preview", headers=_headers(second["token"]))
    assert own.status_code == 200
    assert own.json()["has_data"] is True
    assert foreign.status_code == 200
    assert foreign.json()["has_data"] is False


def test_training_dashboard_is_available():
    response = client.get("/app/training/dashboard")
    assert response.status_code == 200
    assert "Postępy treningowe" in response.text


def test_adaptive_preview_exposes_trend_and_data_sufficiency_without_mutation():
    ctx = _context()
    started = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
    sid = started.json()["session"]["id"]
    for number in (1, 2, 3):
        assert _log_set(ctx["token"], sid, number, reps=5, weight=100, rpe=7).status_code == 200
    assert client.post(
        f"/app/training/sessions/{sid}/complete",
        json={"final_rpe": 7},
        headers=_headers(ctx["token"]),
    ).status_code == 200

    preview = client.get("/app/training/adaptive/preview", headers=_headers(ctx["token"]))
    assert preview.status_code == 200
    exercise = preview.json()["exercises"][0]
    assert exercise["data_sufficiency"] == "low"
    assert exercise["trend"] == "new_baseline"
    assert preview.json()["plan_mutated"] is False


def test_adaptive_plan_preview_is_read_only_and_user_scoped():
    first = _context()
    second = _context()
    started = client.post("/app/training/sessions/start", headers=_headers(first["token"]))
    sid = started.json()["session"]["id"]
    for number in (1, 2, 3):
        assert _log_set(first["token"], sid, number, reps=5, weight=100, rpe=7).status_code == 200
    assert client.post(
        f"/app/training/sessions/{sid}/complete",
        json={"final_rpe": 7},
        headers=_headers(first["token"]),
    ).status_code == 200

    own = client.get("/app/training/adaptive/plan-preview", headers=_headers(first["token"]))
    foreign = client.get("/app/training/adaptive/plan-preview", headers=_headers(second["token"]))
    assert own.status_code == 200
    assert own.json()["has_data"] is True
    assert own.json()["plan_mutated"] is False
    assert len(own.json()["weeks"]) == 2
    assert own.json()["weeks"][0]["exercises"][0]["week_1"]["weight_kg"] == 102.5
    assert foreign.status_code == 200
    assert foreign.json()["has_data"] is False


def test_adaptive_preview_holds_when_recent_rpe_is_sustained_high():
    ctx = _context()
    for weight in (100, 100, 100):
        started = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
        sid = started.json()["session"]["id"]
        for number in (1, 2, 3):
            assert _log_set(ctx["token"], sid, number, reps=5, weight=weight, rpe=9).status_code == 200
        assert client.post(
            f"/app/training/sessions/{sid}/complete",
            json={"final_rpe": 9},
            headers=_headers(ctx["token"]),
        ).status_code == 200

    preview = client.get("/app/training/adaptive/preview", headers=_headers(ctx["token"]))
    assert preview.status_code == 200
    exercise = preview.json()["exercises"][0]
    assert exercise["decision"] == "maintain"
    assert "SUSTAINED_HIGH_RPE" in exercise["reason_codes"]
    assert exercise["data_sufficiency"] == "high"


def test_training_dashboard_contains_history_and_adaptation_sections():
    response = client.get("/app/training/dashboard")
    assert response.status_code == 200
    assert "Adaptacja ćwiczeń" in response.text
    assert "Ostatnie sesje" in response.text
    assert "Podgląd planu 2-tygodniowego" in response.text
