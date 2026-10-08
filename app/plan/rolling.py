"""Canonical rolling planning contract and deterministic horizon builder.

This module is orchestration-only. It does not evaluate recovery, adapt exercises,
or decide whether training may start.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

ROLLING_PLAN_VERSION = "rolling-v1"
DEFAULT_HORIZON_DAYS = 14
MIN_HORIZON_DAYS = 7
MAX_HORIZON_DAYS = 14


def _safe_horizon_days(value: int) -> int:
    return max(MIN_HORIZON_DAYS, min(MAX_HORIZON_DAYS, int(value)))


def _day_key(value: Any) -> str:
    return str(value or "").strip().casefold()


def build_rolling_plan_contract(
    plan: dict[str, Any] | None,
    *,
    horizon_start: date,
    horizon_days: int = DEFAULT_HORIZON_DAYS,
    completed_sessions: list[dict[str, Any]] | None = None,
    plan_version: str = ROLLING_PLAN_VERSION,
    source: str = "deterministic_rolling",
) -> dict[str, Any]:
    """Normalize a plan and completed execution history into a rolling envelope."""
    safe_days = _safe_horizon_days(horizon_days)
    end = horizon_start + timedelta(days=safe_days - 1)
    completed = [item for item in (completed_sessions or []) if isinstance(item, dict)]
    completed_by_date = {
        str(item.get("session_date")): item
        for item in completed
        if item.get("session_date")
    }

    if not isinstance(plan, dict):
        return {
            "horizon_start": horizon_start.isoformat(),
            "horizon_end": end.isoformat(),
            "upcoming_sessions": [],
            "completed_sessions": completed,
            "planned_sessions": [],
            "plan_version": plan_version,
            "source": source,
            "sufficient_data": False,
            "reason_codes": ["INVALID_PLAN"],
        }

    raw_days = plan.get("days") if isinstance(plan.get("days"), list) else []
    upcoming = []
    completed_in_horizon = []
    for item in raw_days:
        if not isinstance(item, dict) or not item.get("day"):
            continue
        day = item.get("day")
        matched = completed_by_date.get(str(day))
        if matched is not None:
            completed_in_horizon.append(matched)
            continue
        upcoming.append({
            "day": day,
            "day_type": item.get("day_type"),
            "workout": item.get("workout", {}),
        })

    return {
        "horizon_start": horizon_start.isoformat(),
        "horizon_end": end.isoformat(),
        "upcoming_sessions": upcoming,
        "completed_sessions": completed_in_horizon,
        "planned_sessions": list(upcoming),
        "plan_version": plan_version,
        "source": source,
        "sufficient_data": bool(upcoming or completed_in_horizon),
        "reason_codes": [] if (upcoming or completed_in_horizon) else ["NO_PLANNED_SESSIONS"],
    }


def build_rolling_horizon(
    plan: dict[str, Any] | None,
    *,
    horizon_start: date,
    horizon_days: int = DEFAULT_HORIZON_DAYS,
    completed_sessions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a deterministic, non-mutating rolling horizon."""
    return build_rolling_plan_contract(
        plan,
        horizon_start=horizon_start,
        horizon_days=horizon_days,
        completed_sessions=completed_sessions,
    )
