from datetime import date
from app.training.progress import build_progress_evidence

def _history(weight1=100.0, weight2=105.0):
    return [
        {"session_id": "new", "session_date": date(2026, 10, 5), "exercises": [{"exercise_key": "squat", "exercise_name": "Squat", "sets": [{"actual_weight_kg": weight2, "actual_reps": 5, "actual_rpe": 7, "completed": True}]}]},
        {"session_id": "old", "session_date": date(2026, 10, 1), "exercises": [{"exercise_key": "squat", "exercise_name": "Squat", "sets": [{"actual_weight_kg": weight1, "actual_reps": 5, "actual_rpe": 8, "completed": True}]}]},
    ]

def test_progress_evidence_is_deterministic_and_explains_change():
    result = build_progress_evidence(_history(), exercise_key="squat")
    assert result["sufficient_data"] is True
    assert result["changes"]["average_weight_kg_delta"] == 5.0
    assert result["changes"]["average_rpe_delta"] == -1.0
    assert result["material_change"] is True
    assert result["reason_codes"] == ["MATERIAL_CHANGE"]
    assert result == build_progress_evidence(_history(), exercise_key="squat")

def test_progress_evidence_returns_insufficient_data_without_two_observations():
    history = _history()[:1]
    result = build_progress_evidence(history, exercise_key="squat")
    assert result["status"] == "insufficient_data"
    assert result["sufficient_data"] is False
    assert result["changes"] == {}

def test_progress_evidence_never_invents_missing_metrics():
    history = _history()
    history[0]["exercises"][0]["sets"][0]["actual_rpe"] = None
    history[1]["exercises"][0]["sets"][0]["actual_rpe"] = None
    result = build_progress_evidence(history, exercise_key="squat")
    assert result["changes"]["average_rpe_delta"] is None
    assert result["changes"]["average_weight_kg_delta"] == 5.0

def test_progress_evidence_filters_exercise_key():
    result = build_progress_evidence(_history(), exercise_key="bench")
    assert result["status"] == "insufficient_data"
    assert result["observations"] == []


def test_progress_evidence_counts_only_valid_completed_sets():
    history = _history()
    history[0]["exercises"][0]["sets"].append({
        "actual_weight_kg": "not-a-number",
        "actual_reps": 5,
        "actual_rpe": 7,
        "completed": True,
    })
    history[0]["exercises"][0]["sets"].append(None)
    history.append(None)

    result = build_progress_evidence(history, exercise_key="squat")
    assert result["status"] == "sufficient"
    assert result["latest"]["completed_sets"] == 1
    assert result["changes"]["completed_sets_delta"] == 0
