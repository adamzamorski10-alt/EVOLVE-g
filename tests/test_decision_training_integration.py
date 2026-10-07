from __future__ import annotations

from app.decision_engine import build_decision


def _goal(goal_id="g1", *, sufficient=True, on_track=True, trend="up", sessions=("s1",)):
    return {
        "goal": {"id": goal_id},
        "sufficient_data": sufficient,
        "on_track": on_track,
        "trend": trend,
        "supporting_session_ids": list(sessions),
    }


def test_training_signal_is_evidence_not_a_second_evaluation_engine():
    result = build_decision(
        goal_states=[_goal()],
        training={"status": "ready", "overall_decision": "reduce", "session_id": "s9"},
    )
    assert result["decision"] == "reduce_training"
    assert result["supporting_session_ids"] == ["s1", "s9"]
    assert result["mutates_plan"] is False


def test_recovery_still_overrides_training_and_goal_signals():
    result = build_decision(
        goal_states=[_goal()],
        training={"status": "ready", "overall_decision": "progress"},
        recovery={"status": "recovery", "constraint": "reduce_volume_50"},
    )
    assert result["decision"] == "recover"
    assert result["priority"] == "critical"


def test_training_insufficient_data_does_not_create_progression():
    result = build_decision(
        goal_states=[_goal(sufficient=False)],
        training={"status": "insufficient_data", "overall_decision": "insufficient_data"},
    )
    assert result["decision"] == "insufficient_data"


def test_training_insufficient_status_overrides_conflicting_progress_signal():
    result = build_decision(
        goal_states=[_goal()],
        training={"status": "insufficient_data", "overall_decision": "progress", "session_id": "s9"},
    )
    assert result["decision"] == "insufficient_data"
    assert result["priority"] == "low"
    assert "TRAINING_DATA_INSUFFICIENT" in result["reason_codes"]
    assert result["supporting_session_ids"] == ["s1"]


def test_training_insufficient_status_overrides_conflicting_reduce_signal():
    result = build_decision(
        goal_states=[_goal()],
        training={"status": "insufficient_data", "overall_decision": "reduce", "session_id": "s9"},
    )
    assert result["decision"] == "insufficient_data"
    assert result["priority"] == "low"
    assert "TRAINING_DATA_INSUFFICIENT" in result["reason_codes"]
    assert result["supporting_session_ids"] == ["s1"]
