from datetime import date
from types import SimpleNamespace

from app.decision_engine import DECISION_ALGORITHM, build_decision


def _goal(
    goal_id="g1",
    *,
    sufficient=True,
    on_track=True,
    trend="up",
    sessions=("s1",),
):
    return {
        "goal": {"id": goal_id},
        "sufficient_data": sufficient,
        "on_track": on_track,
        "trend": trend,
        "supporting_session_ids": list(sessions),
    }


def test_progression_is_selected_from_positive_goal_training_evidence():
    result = build_decision(goal_states=[_goal()])
    assert result["decision"] == "progress_training"
    assert result["priority"] == "normal"
    assert "GOAL_TRAINING_PROGRESS" in result["reason_codes"]
    assert result["mutates_plan"] is False
    assert result["algorithm_version"] == DECISION_ALGORITHM


def test_recovery_override_has_priority_over_progression():
    result = build_decision(
        goal_states=[_goal()],
        recovery={
            "status": "recovery",
            "constraint": "reduce_volume_50",
        },
    )
    assert result["decision"] == "recover"
    assert result["priority"] == "critical"
    assert "RECOVERY_OVERRIDE" in result["reason_codes"]


def test_caution_recovery_reduces_training():
    result = build_decision(
        goal_states=[_goal()],
        recovery={
            "status": "caution",
            "constraint": "reduce_volume_25",
        },
    )
    assert result["decision"] == "reduce_training"
    assert result["priority"] == "high"
    assert result["constraints"] == ["reduce_volume_25"]


def test_missing_evidence_never_becomes_progress():
    result = build_decision(goal_states=[_goal(sufficient=False)])
    assert result["decision"] == "insufficient_data"
    assert result["sufficient_data"] is False
    assert "INSUFFICIENT_GOAL_TRAINING_EVIDENCE" in result["reason_codes"]


def test_maintain_is_selected_when_goal_evidence_is_usable_but_not_on_track():
    result = build_decision(
        goal_states=[_goal(on_track=False, trend="stable")],
    )
    assert result["decision"] == "maintain_training"


def test_explicit_constraint_precedes_performance_optimization():
    result = build_decision(
        goal_states=[_goal()],
        constraints=[{"key": "schedule_conflict"}],
    )
    assert result["decision"] == "reduce_training"
    assert result["priority"] == "high"
    assert result["constraints"] == ["schedule_conflict"]

def test_explicit_constraint_precedes_missing_core_context():
    result = build_decision(
        goal_states=[],
        constraints=[{"key": "schedule_conflict"}],
    )
    assert result["decision"] == "reduce_training"
    assert result["priority"] == "high"
    assert result["constraints"] == ["schedule_conflict"]


def test_explicit_constraint_precedes_training_progress_signal():
    result = build_decision(
        goal_states=[_goal()],
        training={"status": "ready", "overall_decision": "progress", "session_id": "s1"},
        constraints=[{"key": "schedule_conflict"}],
    )
    assert result["decision"] == "reduce_training"
    assert result["priority"] == "high"
    assert result["constraints"] == ["schedule_conflict"]


def test_nutrition_is_supporting_evidence_and_never_mutates_plan():
    result = build_decision(
        goal_states=[_goal()],
        nutrition={"adaptation_allowed": False},
    )
    assert result["decision"] == "progress_training"
    assert "NUTRITION_ADAPTATION_DISABLED" in result["reason_codes"]
    assert result["mutates_plan"] is False


def test_output_contains_deduplicated_supporting_evidence():
    result = build_decision(
        goal_states=[
            _goal("g1", sessions=("s1", "s2")),
            _goal("g2", sessions=("s2", "s3")),
        ],
    )
    assert result["supporting_goal_ids"] == ["g1", "g2"]
    assert result["supporting_session_ids"] == ["s1", "s2", "s3"]


def test_inputs_are_not_mutated():
    goals = [_goal()]
    recovery = {"status": "caution", "constraint": "reduce_volume_25"}
    nutrition = {"adaptation_allowed": False}
    before = (repr(goals), repr(recovery), repr(nutrition))

    build_decision(
        goal_states=goals,
        recovery=recovery,
        nutrition=nutrition,
    )

    assert (repr(goals), repr(recovery), repr(nutrition)) == before


from app.decision_engine import build_decision


def goal(*, sufficient=True, on_track=True, trend="up"):
    return {
        "goal": {"id": "g1"},
        "sufficient_data": sufficient,
        "on_track": on_track,
        "trend": trend,
        "supporting_session_ids": ["s1"],
    }


def test_training_progress_signal_is_consumed_without_reimplementing_evaluation():
    result = build_decision(
        goal_states=[goal()],
        training={
            "status": "ready",
            "overall_decision": "progress",
            "reason_codes": ["ALL_EXERCISES_READY_TO_PROGRESS"],
            "session_id": "s1",
        },
    )
    assert result["decision"] == "progress_training"
    assert "TRAINING_READY_TO_PROGRESS" in result["reason_codes"]


def test_training_reduce_signal_precedes_goal_progress():
    result = build_decision(
        goal_states=[goal()],
        training={
            "status": "ready",
            "overall_decision": "reduce",
            "reason_codes": ["EXERCISE_REQUIRES_REDUCTION"],
            "session_id": "s1",
        },
    )
    assert result["decision"] == "reduce_training"
    assert "TRAINING_REQUIRES_REDUCTION" in result["reason_codes"]


def test_training_insufficient_signal_does_not_create_progress():
    result = build_decision(
        goal_states=[goal()],
        training={
            "status": "insufficient_data",
            "overall_decision": "insufficient_data",
        },
    )
    assert result["decision"] != "progress_training"
    assert "TRAINING_DATA_INSUFFICIENT" in result["reason_codes"]


def test_recovery_still_overrides_training_progress():
    result = build_decision(
        goal_states=[goal()],
        training={"status": "ready", "overall_decision": "progress"},
        recovery={"status": "recovery", "constraint": "reduce_volume_50"},
    )
    assert result["decision"] == "recover"
