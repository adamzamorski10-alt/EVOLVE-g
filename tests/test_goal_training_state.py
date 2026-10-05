from datetime import date
from types import SimpleNamespace

from app.goals.training_state import build_goal_training_state


def make_goal(**overrides):
    values = {
        "id": "goal-1", "status": "active", "goal_type": "strength",
        "title": "Bench press", "start_date": date(2026, 10, 1),
        "target_date": date(2026, 10, 31), "metric_key": "best_weight_kg",
        "baseline_value": 100.0, "target_value": 110.0,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_goal_training_state_builds_progress_and_evidence():
    state = build_goal_training_state(
        make_goal(),
        [
            {"date": "2026-10-03", "value": 102.5, "session_id": "s1"},
            {"date": "2026-10-05", "value": 105.0, "session_id": "s2"},
        ],
        as_of=date(2026, 10, 5),
    )
    assert state["current_value"] == 105.0
    assert state["progress_pct"] == 50.0
    assert state["remaining"] == 5.0
    assert state["trend"] == "up"
    assert state["supporting_session_ids"] == ["s1", "s2"]
    assert state["latest_supporting_training_date"] == "2026-10-05"
    assert state["evidence_count"] == 2
    assert state["sufficient_data"] is True
    assert state["reason_codes"] == ["TRAINING_EVIDENCE_AVAILABLE"]


def test_goal_training_state_missing_evidence_never_infers_progress():
    state = build_goal_training_state(make_goal(), [], as_of=date(2026, 10, 5))
    assert state["current_value"] is None
    assert state["progress_pct"] is None
    assert state["remaining"] is None
    assert state["trend"] is None
    assert state["on_track"] is None
    assert state["evidence_count"] == 0
    assert state["sufficient_data"] is False
    assert state["reason_codes"] == ["INSUFFICIENT_TRAINING_EVIDENCE"]


def test_goal_training_state_supports_decreasing_metric():
    state = build_goal_training_state(
        make_goal(
            metric_key="average_rpe",
            baseline_value=9.0,
            target_value=7.0,
        ),
        [{"date": "2026-10-05", "value": 8.0, "session_id": "s1"}],
        as_of=date(2026, 10, 5),
    )
    assert state["progress_pct"] == 50.0
    assert state["remaining"] == 1.0
    assert state["metric"]["direction"] == "decrease"


def test_goal_training_state_is_deterministically_sorted():
    state = build_goal_training_state(
        make_goal(),
        [
            {"date": "2026-10-05", "value": 105.0, "session_id": "s2"},
            {"date": "2026-10-03", "value": 102.5, "session_id": "s1"},
        ],
    )
    assert state["supporting_session_ids"] == ["s1", "s2"]


def test_goal_training_state_does_not_mutate_goal_or_input():
    goal = make_goal()
    evidence = [{"date": "2026-10-05", "value": 105.0, "session_id": "s1"}]
    build_goal_training_state(goal, evidence)
    assert not hasattr(goal, "current_value")
    assert evidence == [{"date": "2026-10-05", "value": 105.0, "session_id": "s1"}]
