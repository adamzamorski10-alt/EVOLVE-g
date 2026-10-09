from datetime import date

from app.plan.rolling import (
    DEFAULT_HORIZON_DAYS,
    MAX_HORIZON_DAYS,
    MIN_HORIZON_DAYS,
    build_rolling_horizon,
    build_rolling_plan_contract,
)


def _plan():
    return {
        "days": [
            {
                "day": "Poniedziałek",
                "day_type": "heavy",
                "workout": {"title": "Strength", "exercises": [{"name": "Bench"}]},
            },
            {"day": "Wtorek", "day_type": "rest", "workout": {}},
        ]
    }


def test_rolling_contract_has_stable_7_to_14_day_horizon():
    result = build_rolling_horizon(_plan(), horizon_start=date(2026, 10, 12))
    assert result["horizon_start"] == "2026-10-12"
    assert result["horizon_end"] == "2026-10-25"
    assert result["plan_version"] == "rolling-v1"
    assert result["source"] == "deterministic_rolling"
    assert [item["scheduled_date"] for item in result["upcoming_sessions"]] == [
        "2026-10-12", "2026-10-19"
    ]
    assert [item["scheduled_date"] for item in result["planned_days"]] == [
        "2026-10-12", "2026-10-13", "2026-10-19", "2026-10-20"
    ]
    assert [item["scheduled_date"] for item in result["rest_days"]] == [
        "2026-10-13", "2026-10-20"
    ]
    assert result["planned_sessions"] == result["upcoming_sessions"]


def test_rolling_horizon_clamps_requested_length():
    start = date(2026, 10, 12)
    assert build_rolling_horizon(_plan(), horizon_start=start, horizon_days=1)["horizon_end"] == "2026-10-18"
    assert build_rolling_horizon(_plan(), horizon_start=start, horizon_days=99)["horizon_end"] == "2026-10-25"


def test_invalid_plan_is_fail_safe():
    result = build_rolling_horizon(None, horizon_start=date(2026, 10, 12))
    assert result["sufficient_data"] is False
    assert result["upcoming_sessions"] == []
    assert result["planned_sessions"] == []
    assert result["reason_codes"] == ["INVALID_PLAN"]


def test_empty_plan_is_insufficient_data():
    result = build_rolling_plan_contract(
        {"days": []},
        horizon_start=date(2026, 10, 12),
        horizon_days=DEFAULT_HORIZON_DAYS,
    )
    assert result["sufficient_data"] is False
    assert result["reason_codes"] == ["NO_PLANNED_SESSIONS"]


def test_rolling_builder_is_read_only_and_deterministic():
    plan = _plan()
    before = repr(plan)
    first = build_rolling_horizon(plan, horizon_start=date(2026, 10, 12))
    second = build_rolling_horizon(plan, horizon_start=date(2026, 10, 12))
    assert repr(plan) == before
    assert first == second
    assert first["completed_sessions"] == []


def test_contract_exports_expected_bounds():
    assert MIN_HORIZON_DAYS == 7
    assert MAX_HORIZON_DAYS == 14


def test_completed_history_is_removed_from_upcoming_and_kept_in_completed():
    completed = [{"session_id": "s1", "session_date": "2026-10-12", "status": "completed"}]
    result = build_rolling_horizon(
        _plan(),
        horizon_start=date(2026, 10, 12),
        completed_sessions=completed,
    )
    assert [item["scheduled_date"] for item in result["upcoming_sessions"]] == [
        "2026-10-19"
    ]
    assert [item["status"] for item in result["planned_days"]] == [
        "completed", "rest", "planned", "rest"
    ]
    assert result["completed_sessions"] == completed
    assert result["planned_sessions"] == result["upcoming_sessions"]


def test_foreign_or_unrelated_history_does_not_remove_planned_day():
    completed = [{"session_id": "s1", "session_date": "2026-10-18", "status": "completed"}]
    result = build_rolling_horizon(
        _plan(),
        horizon_start=date(2026, 10, 12),
        completed_sessions=completed,
    )
    assert [item["scheduled_date"] for item in result["upcoming_sessions"]] == [
        "2026-10-12", "2026-10-19"
    ]
    assert len(result["planned_days"]) == 4
    assert result["completed_sessions"] == completed


def test_completed_history_only_consumes_sessions_inside_horizon():
    completed = [{"session_id": "s1", "session_date": "2026-10-26", "status": "completed"}]
    result = build_rolling_horizon(
        _plan(),
        horizon_start=date(2026, 10, 12),
        completed_sessions=completed,
    )
    assert result["completed_sessions"] == []
    assert len(result["upcoming_sessions"]) == 2
    assert len(result["planned_days"]) == 4


def test_malicious_history_payload_does_not_create_execution_decision():
    result = build_rolling_horizon(
        _plan(),
        horizon_start=date(2026, 10, 12),
        completed_sessions=[{
            "session_id": "x",
            "session_date": "2026-10-12",
            "status": "active",
            "decision": "recover",
            "can_start": True,
            "mutates_plan": True,
        }],
    )
    assert result["completed_sessions"] == []
    assert len(result["upcoming_sessions"]) == 2
