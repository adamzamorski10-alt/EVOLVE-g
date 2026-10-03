from datetime import date

from app.models import DailyLogDB
from app.recovery.routes import evaluate_recovery


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
