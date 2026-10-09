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

_WEEKDAYS_PL = ("poniedziałek", "wtorek", "środa", "czwartek", "piątek", "sobota", "niedziela")


def _safe_horizon_days(value: int) -> int:
    try:
        requested = int(value)
    except (TypeError, ValueError, OverflowError):
        requested = DEFAULT_HORIZON_DAYS
    return max(MIN_HORIZON_DAYS, min(MAX_HORIZON_DAYS, requested))


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
    """Expand a weekly template across a dated 7–14 day window."""
    safe_days = _safe_horizon_days(horizon_days)
    end = horizon_start + timedelta(days=safe_days - 1)
    completed_by_date: dict[date, list[dict[str, Any]]] = {}
    completed = []

    for item in completed_sessions or []:
        if not isinstance(item, dict) or item.get("status") != "completed":
            continue
        raw_date = item.get("session_date")
        try:
            session_date = raw_date if isinstance(raw_date, date) else date.fromisoformat(str(raw_date))
        except (TypeError, ValueError):
            continue
        if horizon_start <= session_date <= end:
            normalized = {**item, "session_date": session_date.isoformat()}
            completed.append(normalized)
            completed_by_date.setdefault(session_date, []).append(normalized)

    if not isinstance(plan, dict):
        return {
            "horizon_start": horizon_start.isoformat(),
            "horizon_end": end.isoformat(),
            "upcoming_sessions": [],
            "planned_days": [],
            "rest_days": [],
            "completed_sessions": completed,
            "planned_sessions": [],
            "plan_version": plan_version,
            "source": source,
            "sufficient_data": False,
            "reason_codes": ["INVALID_PLAN"],
        }

    raw_days = plan.get("days") if isinstance(plan.get("days"), list) else []
    templates: dict[str, list[dict[str, Any]]] = {}
    for item in raw_days:
        if isinstance(item, dict) and item.get("day"):
            templates.setdefault(_day_key(item.get("day")), []).append(item)

    upcoming = []
    planned_days = []
    rest_days = []
    completed_scheduled = []
    for offset in range(safe_days):
        scheduled_date = horizon_start + timedelta(days=offset)
        day_key = _WEEKDAYS_PL[scheduled_date.weekday()]
        for item in templates.get(day_key, []):
            matched = completed_by_date.get(scheduled_date, [])
            is_rest = str(item.get("day_type") or "").casefold() == "rest"
            planned_day = {
                "day": item.get("day"),
                "scheduled_date": scheduled_date.isoformat(),
                "day_type": item.get("day_type"),
                "workout": item.get("workout", {}),
                "status": "rest" if is_rest else ("completed" if matched else "planned"),
            }
            planned_days.append(planned_day)
            if is_rest:
                rest_days.append(planned_day)
                continue
            if matched:
                completed_scheduled.extend(matched)
                continue
            upcoming.append(planned_day)

    # Keep all completed sessions in the horizon, including sessions on a weekday
    # that is not represented by the weekly template; deduplicate by stable session ID/date.
    seen = set()
    completed_result = []
    for item in completed_scheduled + completed:
        key = (str(item.get("session_id") or item.get("id") or ""), item.get("session_date"))
        if key not in seen:
            seen.add(key)
            completed_result.append(item)

    return {
        "horizon_start": horizon_start.isoformat(),
        "horizon_end": end.isoformat(),
        "upcoming_sessions": upcoming,
        "completed_sessions": completed_result,
        "planned_sessions": list(upcoming),
        "plan_version": plan_version,
        "source": source,
        "sufficient_data": bool(upcoming or completed_result),
        "reason_codes": [] if (upcoming or completed_result) else ["NO_PLANNED_SESSIONS"],
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
