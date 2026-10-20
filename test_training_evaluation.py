from __future__ import annotations

from types import SimpleNamespace

from app.training.evaluation import evaluate_exercise, evaluate_session


def _sets(count: int, reps: int = 5, weight: float = 100, rpe: float = 7):
    return [
        SimpleNamespace(
            actual_reps=reps,
            actual_weight_kg=weight,
            actual_rpe=rpe,
        )
        for _ in range(count)
    ]


def test_evaluate_exercise_progress_after_target_completion():
    result = evaluate_exercise(
        {"sets": 3, "reps": 5, "weight_kg": 100},
        _sets(3),
    )
    assert result["decision"] == "progress"
    assert result["reason_codes"] == ["TARGET_COMPLETED"]
    assert result["completion_pct"] == 100.0


def test_evaluate_exercise_maintains_after_high_rpe():
    result = evaluate_exercise(
        {"sets": 3, "reps": 5, "weight_kg": 100},
        _sets(3, rpe=9),
    )
    assert result["decision"] == "maintain"
    assert result["reason_codes"] == ["HIGH_RPE"]


def test_evaluate_exercise_reduces_after_low_completion():
    result = evaluate_exercise(
        {"sets": 3, "reps": 5, "weight_kg": 100},
        _sets(1),
    )
    assert result["decision"] == "reduce"
    assert result["reason_codes"] == ["LOW_SET_COMPLETION"]


def test_evaluate_exercise_maintains_when_reps_are_below_target():
    result = evaluate_exercise(
        {"sets": 3, "reps": 5, "weight_kg": 100},
        _sets(3, reps=4),
    )
    assert result["decision"] == "maintain"
    assert result["reason_codes"] == ["REPS_BELOW_TARGET"]


def test_evaluate_exercise_missing_data_is_conservative():
    result = evaluate_exercise(
        {"sets": 3, "reps": 5, "weight_kg": 100},
        [],
    )
    assert result["decision"] == "insufficient_data"


def test_evaluate_session_prefers_reduce_over_maintain_and_progress():
    planned = [
        {"exercise_key": "a", "exercise_name": "A", "sets": 3, "reps": 5},
        {"exercise_key": "b", "exercise_name": "B", "sets": 3, "reps": 5},
    ]
    result = evaluate_session(
        planned,
        {"a": _sets(1), "b": _sets(3, rpe=9)},
    )
    assert result["overall_decision"] == "reduce"
    assert result["summary"]["reduce"] == 1
    assert result["summary"]["maintain"] == 1


def test_evaluate_session_requires_all_exercises_for_progression():
    planned = [
        {"exercise_key": "a", "exercise_name": "A", "sets": 3, "reps": 5},
        {"exercise_key": "b", "exercise_name": "B", "sets": 3, "reps": 5},
    ]
    result = evaluate_session(
        planned,
        {"a": _sets(3), "b": _sets(3)},
    )
    assert result["overall_decision"] == "progress"
    assert result["summary"]["progress"] == 2


def test_evaluate_session_is_conservative_with_missing_exercise_data():
    planned = [
        {"exercise_key": "a", "exercise_name": "A", "sets": 3, "reps": 5},
        {"exercise_key": "b", "exercise_name": "B", "sets": 3, "reps": 5},
    ]
    result = evaluate_session(
        planned,
        {"a": _sets(3)},
    )
    assert result["overall_decision"] == "maintain"
    assert result["summary"]["insufficient_data"] == 1
