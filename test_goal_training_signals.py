from __future__ import annotations

from datetime import date

from app.goals.training_signals import (
    build_goal_training_signal,
    classify_trajectory,
    rank_goal_training_signals,
)


def _goal(**overrides):
    base = {
        "id": "goal-1",
        "title": "Squat 120 kg",
        "goal_type": "strength",
        "priority": 80,
        "metric_key": "best_weight_kg",
        "baseline_value": 100,
        "target_value": 120,
        "target_date": "2026-11-01",
        "metadata": {"exercise_key": "squat"},
    }
    return {**base, **overrides}


def _progress(**overrides):
    base = {
        "metric": {"key": "best_weight_kg", "direction": "increase", "unit": "kg"},
        "current_value": 110,
        "target_value": 120,
        "remaining": 10,
        "progress_pct": 50.0,
        "trend": "up",
        "on_track": True,
        "deadline": "2026-11-01",
    }
    return {**base, **overrides}


def test_goal_training_signal_is_deterministic_and_explainable():
    signal = build_goal_training_signal(_goal(), _progress(), today=date(2026, 10, 5))

    assert signal["goal_id"] == "goal-1"
    assert signal["metric_key"] == "best_weight_kg"
    assert signal["current_value"] == 110
    assert signal["progress_pct"] == 50.0
    assert signal["exercise_key"] == "squat"
    assert signal["trajectory"] == "on_track"
    assert "EXPLICIT_EXERCISE_LINK" in signal["reason_codes"]
    assert "ON_TRACK" in signal["reason_codes"]


def test_goal_training_signal_does_not_invent_exercise_links():
    goal = _goal(metadata={})
    signal = build_goal_training_signal(goal, _progress())
    assert signal["exercise_key"] is None
    assert "EXPLICIT_EXERCISE_LINK" not in signal["reason_codes"]


def test_trajectory_classification_handles_missing_and_urgent_states():
    assert classify_trajectory(progress_pct=None, on_track=None) == "insufficient_data"
    assert classify_trajectory(
        progress_pct=70, on_track=False, target_date=date(2026, 10, 10), today=date(2026, 10, 5)
    ) == "behind_urgent"
    assert classify_trajectory(
        progress_pct=70, on_track=False, target_date=date(2026, 10, 1), today=date(2026, 10, 5)
    ) == "overdue"


def test_goal_training_signal_ranking_is_deterministic():
    generic = build_goal_training_signal(
        _goal(id="generic", priority=100, metadata={}),
        _progress(),
        today=date(2026, 10, 5),
    )
    linked = build_goal_training_signal(
        _goal(id="linked", priority=10),
        _progress(),
        today=date(2026, 10, 5),
    )
    ranked = rank_goal_training_signals([generic, linked])
    assert [item["goal_id"] for item in ranked] == ["linked", "generic"]


def test_goal_training_signal_is_read_only():
    goal = _goal()
    progress = _progress()
    original_goal = dict(goal)
    original_progress = dict(progress)

    build_goal_training_signal(goal, progress)

    assert goal == original_goal
    assert progress == original_progress
