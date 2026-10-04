from datetime import date

from app.models import DailyLogDB
from app.recovery.routes import evaluate_recovery, summarize_recovery_history
from app.training.routes import _apply_recovery_constraint


def _log(**kwargs):
    return DailyLogDB(user_id="u", log_date=date.today(), **kwargs)


def test_recovery_requires_at_least_two_signals():
    result = evaluate_recovery(_log(energy_level=8))
    assert result["status"] == "insufficient_data"
    assert result["constraint"] == "none"


def test_recovery_ready_has_no_training_reduction():
    result = evaluate_recovery(_log(sleep_hours=8, sleep_quality=9, energy_level=9, stress_level=2))
    assert result["status"] == "ready"
    assert result["readiness_score"] >= 75
    assert result["constraint"] == "none"


def test_recovery_caution_reduces_volume():
    result = evaluate_recovery(_log(sleep_hours=6, sleep_quality=6, energy_level=6, stress_level=6))
    assert result["status"] == "caution"
    assert result["constraint"] == "reduce_volume_25"


def test_recovery_low_reduces_volume_more():
    result = evaluate_recovery(_log(sleep_hours=4, sleep_quality=3, energy_level=3, stress_level=9))
    assert result["status"] == "recovery"
    assert result["constraint"] == "reduce_volume_50"


def test_recovery_missing_checkin_is_safe():
    result = evaluate_recovery(None)
    assert result["status"] == "insufficient_data"
    assert result["readiness_score"] is None



def test_recovery_constraint_reduces_planned_sets_without_mutating_input():
    plan = {"days": [{"workout": {"exercises": [{"name": "Squat", "sets": 4, "reps": 5}]}}]}
    constrained, constraint = _apply_recovery_constraint(plan, {"constraint": "reduce_volume_50"})
    assert constraint == "reduce_volume_50"
    assert constrained["days"][0]["workout"]["exercises"][0]["sets"] == 2
    assert plan["days"][0]["workout"]["exercises"][0]["sets"] == 4


def test_recovery_history_summary_is_deterministic():
    history = [
        {"status": "ready", "readiness_score": 90, "constraint": "none"},
        {"status": "caution", "readiness_score": 60, "constraint": "reduce_volume_25"},
        {"status": "recovery", "readiness_score": 40, "constraint": "reduce_volume_50"},
        {"status": "missing", "readiness_score": None, "constraint": "none"},
    ]
    summary = summarize_recovery_history(history)
    assert summary["days_with_data"] == 3
    assert summary["missing_days"] == 1
    assert summary["average_readiness"] == 63.3
    assert summary["constrained_days"] == 2
    assert summary["caution_days"] == 1
    assert summary["recovery_days"] == 1


def test_recovery_today_and_history_are_user_scoped():
    from datetime import date
    from sqlmodel import Session, select
    from app.database import engine
    from app.models import UserDB
    from test_training_execution import _context, _headers, client

    first = _context()
    second = _context()
    with Session(engine) as session:
        user = session.exec(select(UserDB).where(UserDB.email == first["email"])).first()
        assert user is not None
        session.add(DailyLogDB(
            user_id=user.id,
            log_date=date.today(),
            sleep_hours=6,
            sleep_quality=6,
            energy_level=6,
            stress_level=6,
        ))
        session.commit()

    today = client.get("/app/recovery/today", headers=_headers(first["token"]))
    assert today.status_code == 200
    assert today.json()["status"] == "caution"

    history = client.get("/app/recovery/history?days=2", headers=_headers(first["token"]))
    assert history.status_code == 200
    assert history.json()["summary"]["days_with_data"] == 1
    assert history.json()["summary"]["missing_days"] == 1

    other = client.get("/app/recovery/today", headers=_headers(second["token"]))
    assert other.status_code == 200
    assert other.json()["status"] == "insufficient_data"


def test_recovery_caution_reduces_today_training_without_mutating_stored_plan():
    from datetime import date
    from sqlmodel import Session, select
    from app.database import engine
    from app.models import UserDB
    from test_training_execution import _context, _headers, client

    ctx = _context()
    with Session(engine) as session:
        user = session.exec(select(UserDB).where(UserDB.email == ctx["email"])).first()
        assert user is not None
        original_plan = user.weekly_plan_json
        session.add(DailyLogDB(
            user_id=user.id,
            log_date=date.today(),
            sleep_hours=6,
            sleep_quality=6,
            energy_level=6,
            stress_level=6,
        ))
        session.commit()

    today = client.get("/app/training/today", headers=_headers(ctx["token"]))
    assert today.status_code == 200
    data = today.json()
    assert data["plan"]["source"] == "base"
    assert data["exercises"][0]["sets"] == 2

    with Session(engine) as session:
        user = session.exec(select(UserDB).where(UserDB.email == ctx["email"])).first()
        assert user.weekly_plan_json == original_plan


def test_recovery_ignores_invalid_out_of_range_signals():
    invalid = _log(sleep_hours=-4, sleep_quality=99, energy_level=99, stress_level=-10)
    result = evaluate_recovery(invalid)
    assert result["signal_count"] == 0
    assert result["status"] == "insufficient_data"
    assert result["constraint"] == "none"


def test_recovery_boundary_scores_are_stable():
    ready = evaluate_recovery(_log(energy_level=10, stress_level=1))
    caution = evaluate_recovery(_log(energy_level=6, stress_level=6))
    low = evaluate_recovery(_log(energy_level=1, stress_level=10))
    assert ready["readiness_score"] == 100.0
    assert caution["readiness_score"] == 55.0
    assert low["readiness_score"] == 10.0
