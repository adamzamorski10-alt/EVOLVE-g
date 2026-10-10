from test_training_execution import _context, _headers, client


def _complete(ctx, reps=5, weight=100, rpe=7):
    started = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
    assert started.status_code == 200, started.text
    sid = started.json()["session"]["id"]
    logged = client.post(
        f"/app/training/sessions/{sid}/sets",
        json={
            "exercise_key": "squat-1",
            "set_number": 1,
            "actual_reps": reps,
            "actual_weight_kg": weight,
            "actual_rpe": rpe,
        },
        headers=_headers(ctx["token"]),
    )
    assert logged.status_code == 200, logged.text
    completed = client.post(
        f"/app/training/sessions/{sid}/complete",
        json={"final_rpe": rpe},
        headers=_headers(ctx["token"]),
    )
    assert completed.status_code == 200, completed.text
    return sid


def test_next_effective_preview_is_read_only_and_matches_apply():
    ctx = _context()
    sid = _complete(ctx)

    preview = client.get("/app/training/adaptive/next-effective-preview", headers=_headers(ctx["token"]))
    assert preview.status_code == 200, preview.text
    data = preview.json()
    assert data["has_data"] is True
    assert data["plan_mutated"] is False
    assert data["current_version"] == 0
    assert data["proposed_version"] == 1
    assert sid in data["source_session_ids"]
    assert data["algorithm"] == "deterministic-v2"
    assert data["plan"]["days"][0]["workout"]["exercises"][0]["weight_kg"] == 97.5

    applied = client.post("/app/training/adaptive/apply", headers=_headers(ctx["token"]))
    assert applied.status_code == 200, applied.text
    assert applied.json()["version"] == data["proposed_version"]
    assert applied.json()["plan"] == data["plan"]


def test_adaptive_preview_exposes_canonical_next_effective_plan():
    ctx = _context()
    _complete(ctx)

    preview = client.get("/app/training/adaptive/preview", headers=_headers(ctx["token"]))
    assert preview.status_code == 200, preview.text
    data = preview.json()
    assert data["next_effective_plan"]["days"][0]["workout"]["exercises"][0]["weight_kg"] == 97.5
    assert data["next_effective_algorithm"] == "deterministic-v2"


def test_next_effective_preview_is_user_scoped():
    first = _context()
    second = _context()
    _complete(first)

    first_preview = client.get("/app/training/adaptive/next-effective-preview", headers=_headers(first["token"]))
    second_preview = client.get("/app/training/adaptive/next-effective-preview", headers=_headers(second["token"]))
    assert first_preview.status_code == 200
    assert second_preview.status_code == 200
    assert first_preview.json()["has_data"] is True
    assert second_preview.json()["has_data"] is False
    assert second_preview.json()["source_session_ids"] == []



def test_rolling_plan_preserves_schedule_diagnostics_after_adaptation():
    import json

    from sqlmodel import Session, select

    from app.database import engine
    from app.models import UserDB

    ctx = _context()
    diagnostics = {
        "requested_training_days": 4,
        "scheduled_training_days": 2,
        "unmet_training_days": 2,
        "sport_reserved_days": [],
        "excluded_days": [
            {"day": "Wtorek", "reason_code": "unavailable_day"},
            {"day": "Czwartek", "reason_code": "insufficient_window"},
        ],
    }

    with Session(engine) as db:
        user = db.exec(select(UserDB).where(UserDB.email == ctx["email"])).first()
        assert user is not None
        plan = user.get_dict("weekly_plan_json")
        plan["_planner"] = {
            "version": "deterministic-v2",
            "schedule_diagnostics": diagnostics,
        }
        user.set_dict("weekly_plan_json", plan)
        db.add(user)
        db.commit()

    _complete(ctx)

    applied = client.post(
        "/app/training/adaptive/apply",
        headers=_headers(ctx["token"]),
    )
    assert applied.status_code == 200, applied.text
    assert applied.json()["version"] == 1
    assert applied.json()["plan"]["_planner"]["schedule_diagnostics"] == diagnostics

    rolling = client.get(
        "/app/plan/rolling?horizon_days=14",
        headers=_headers(ctx["token"]),
    )
    assert rolling.status_code == 200, rolling.text
    payload = rolling.json()
    assert payload["effective_plan"]["source"] == "adaptive"
    assert payload["schedule_diagnostics"] == diagnostics
