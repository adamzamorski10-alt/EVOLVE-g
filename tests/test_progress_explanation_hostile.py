from __future__ import annotations

from app.training.progress_explanation import explain_progress

def test_explanation_is_fail_safe_for_malformed_evidence():
    result = explain_progress({"status": "sufficient", "sufficient_data": True, "changes": {"average_weight_kg_delta": float("nan")}})
    assert result["status"] == "sufficient"
    assert result["changes"] == []\n    assert result["reason_codes"] == ["NO_MATERIAL_CHANGE"]

def test_explanation_never_emits_recommendation_or_mutation_fields():
    result = explain_progress({"status": "sufficient", "sufficient_data": True, "exercise_key": "squat", "changes": {"average_weight_kg_delta": 5}})
    assert "action" not in result
    assert "proposed" not in result
    assert "decision" not in result