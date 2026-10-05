"""Deterministic Goal -> Training signal domain service for Stage 9B.

This module is intentionally pure: it consumes already-computed goal progress
and never mutates goals, plans, sessions, or adaptation state.
"""
from __future__ import annotations

from datetime import date
from typing import Any


def classify_trajectory(
    *,
    progress_pct: float | None,
    on_track: bool | None,
    target_date: date | None,
    today: date | None = None,
) -> str:
    if progress_pct is None:
        return "insufficient_data"
    if on_track is True:
        if target_date is not None:
            days_left = (target_date - (today or date.today())).days
            if days_left <= 7 and progress_pct < 100:
                return "on_track_urgent"
        return "on_track"
    if target_date is not None:
        days_left = (target_date - (today or date.today())).days
        if days_left < 0:
            return "overdue"
        if days_left <= 7:
            return "behind_urgent"
    return "behind"


def build_goal_training_signal(
    goal: dict[str, Any],
    progress: dict[str, Any],
    *,
    today: date | None = None,
) -> dict[str, Any]:
    metric = progress.get("metric") or {}
    metric_key = metric.get("key") or goal.get("metric_key")
    current = progress.get("current_value")
    target = progress.get("target_value", goal.get("target_value"))
    progress_pct = progress.get("progress_pct")
    on_track = progress.get("on_track")
    target_date_raw = progress.get("deadline") or goal.get("target_date")
    target_date = date.fromisoformat(target_date_raw) if target_date_raw else None

    metadata = goal.get("metadata") or {}
    exercise_key = metadata.get("exercise_key")
    trajectory = classify_trajectory(
        progress_pct=progress_pct,
        on_track=on_track,
        target_date=target_date,
        today=today,
    )

    reasons: list[str] = []
    if exercise_key:
        reasons.append("EXPLICIT_EXERCISE_LINK")
    if on_track is True:
        reasons.append("ON_TRACK")
    elif on_track is False:
        reasons.append("BEHIND_TARGET")
    if trajectory.endswith("URGENT"):
        reasons.append("TARGET_DATE_NEAR")
    if trajectory == "overdue":
        reasons.append("TARGET_DATE_PASSED")

    return {
        "goal_id": goal["id"],
        "title": goal["title"],
        "goal_type": goal["goal_type"],
        "priority": int(goal.get("priority", 0)),
        "metric_key": metric_key,
        "direction": metric.get("direction"),
        "baseline_value": goal.get("baseline_value"),
        "current_value": current,
        "target_value": target,
        "progress_pct": progress_pct,
        "remaining": progress.get("remaining"),
        "trend": progress.get("trend"),
        "on_track": on_track,
        "target_date": target_date.isoformat() if target_date else None,
        "trajectory": trajectory,
        "exercise_key": exercise_key,
        "reason_codes": reasons,
    }


def rank_goal_training_signals(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deterministically order signals without changing their meaning."""
    return sorted(
        signals,
        key=lambda item: (
            0 if item.get("exercise_key") else 1,
            -int(item.get("priority", 0)),
            item.get("target_date") or "9999-12-31",
            str(item.get("goal_id", "")),
        ),
    )
