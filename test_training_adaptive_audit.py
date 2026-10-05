from test_training_execution import _context, _headers, client


def _complete(ctx):
    started = client.post("/app/training/sessions/start", headers=_headers(ctx["token"]))
    assert started.status_code == 200, started.text
    sid = started.json()["session"]["id"]
    logged = client.post(
        f"/app/training/sessions/{sid}/sets",
        json={
            "exercise_key": "squat-1",
            "set_number": 1,
            "actual_reps": 5,
            "actual_weight_kg": 100,
            "actual_rpe": 7,
        },
        headers=_headers(ctx["token"]),
    )
    assert logged.status_code == 200, logged.text
    completed = client.post(
        f"/app/training/sessions/{sid}/complete",
        json={"final_rpe": 7},
        headers=_headers(ctx["token"]),
    )
    assert completed.status_code == 200, completed.text
    return sid


def test_adaptive_history_is_user_scoped_and_versioned():
    first = _context()
    second = _context()
    sid = _complete(first)

    applied = client.post("/app/training/adaptive/apply", headers=_headers(first["token"]))
    assert applied.status_code == 200, applied.text

    history = client.get("/app/training/adaptive/history", headers=_headers(first["token"]))
    assert history.status_code == 200
    data = history.json()
    assert data["count"] == 1
    assert data["revisions"][0]["version"] == 1
    assert sid in data["revisions"][0]["source_session_ids"]
    assert data["revisions"][0]["algorithm"] == "deterministic-v2"

    other = client.get("/app/training/adaptive/history", headers=_headers(second["token"]))
    assert other.status_code == 200
    assert other.json()["count"] == 0


def test_reapplying_same_latest_adaptation_is_idempotent():
    ctx = _context()
    _complete(ctx)

    first = client.post("/app/training/adaptive/apply", headers=_headers(ctx["token"]))
    second = client.post("/app/training/adaptive/apply", headers=_headers(ctx["token"]))

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["status"] == "applied"
    assert second.json()["status"] == "unchanged"
    assert second.json()["version"] == first.json()["version"]
