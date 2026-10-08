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


def build_rolling_plan_contract(
    plan: dict[str, Any] | None,
    *,
    horizon_start: date,
    horizon_days: int = DEFAULT_HORIZON_DAYS,
    plan_version: str = ROLLING_PLAN_VERSION,
    source: str = "deterministic_rolling",
) -> dict[str, Any]:
    """Normalize a generated plan into the canonical rolling-plan envelope."""
    safe_days = _safe_horizon_days(horizon_days)
    end = horizon_start + timedelta(days=safe_days - 1)
    if not isinstance(plan, dict):
        return {
            "horizon_start": horizon_start.isoformat(),
            "horizon_end": end.isoformat(),
            "upcoming_sessions": [],
            "completed_sessions": [],
            "planned_sessions": [],
            "plan_version": plan_version,
            "source": source,
            "sufficient_data": False,
            "reason_codes": ["INVALID_PLAN"],
        }

    raw_days = plan.get("days") if isinstance(plan.get("days"), list) else []
    upcoming = [
        {
            "day": item.get("day"),
            "day_type": item.get("day_type"),
            "workout": item.get("workout", {}),
        }
        for item in raw_days
        if isinstance(item, dict) and item.get("day")
    ]
    return {
        "horizon_start": horizon_start.isoformat(),
        "horizon_end": end.isoformat(),
        "upcoming_sessions": upcoming,
        "completed_sessions": [],
        "planned_sessions": list(upcoming),
        "plan_version": plan_version,
        "source": source,
        "sufficient_data": bool(upcoming),
        "reason_codes": [] if upcoming else ["NO_PLANNED_SESSIONS"],
    }


def build_rolling_horizon(
    plan: dict[str, Any] | None,
    *,
    horizon_start: date,
    horizon_days: int = DEFAULT_HORIZON_DAYS,
) -> dict[str, Any]:
    """Build a deterministic, non-mutating rolling horizon from an existing plan."""
    return build_rolling_plan_contract(
        plan,
        horizon_start=horizon_start,
        horizon_days=horizon_days,
    )
