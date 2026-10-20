from app.training.progress import build_progress_evidence
from app.training.progress_explanation import explain_progress

def test_explanation_reports_only_observed_nonzero_changes():
    history = [
        {"session_id": "new", "session_date": "2026-10-05", "exercises": [{"exercise_key": "squat", "sets": [{"actual_weight_kg": 105, "actual_reps": 5, "actual_rpe": 7, "completed": True}]}]},
        {"session_id": "old", "session_date": "2026-10-01", "exercises": [{"exercise_key": "squat", "sets": [{"actual_weight_kg": 100, "actual_reps": 5, "actual_rpe": 8, "completed": True}]}]},
    ]
    result = explain_progress(build_progress_evidence(history, exercise_key="squat"))
    assert result["status"] == "sufficient"
    assert result["reason_codes"] == ["MATERIAL_CHANGE"]
    assert [(x["metric"], x["direction"], x["delta"]) for x in result["changes"]] == [("load", "up", 5.0), ("rpe", "down", -1.0), ("volume", "up", 25.0)]

def test_explanation_is_non_prescriptive():
    evidence = {"status": "sufficient", "sufficient_data": True, "exercise_key": "x", "changes": {"average_weight_kg_delta": 0, "average_reps_delta": 0, "completed_sets_delta": 0, "volume_kg_delta": 0, "average_rpe_delta": 0}}
    result = explain_progress(evidence)
    assert result["reason_codes"] == ["NO_MATERIAL_CHANGE"]
    assert result["changes"] == []
    assert "action" not in result

def test_explanation_preserves_insufficient_data():
    result = explain_progress({"status": "insufficient_data", "sufficient_data": False})
    assert result["status"] == "insufficient_data"
    assert result["sufficient_data"] is False
    assert result["changes"] == []