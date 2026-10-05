"""Canonical deterministic Goal ↔ Training state builder.

This module is intentionally pure: it consumes a goal definition and already
materialized completed-training evidence. It never reads or mutates the DB,
goal lifecycle, training plan, or adaptive plan.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Iterable

from app.goals.service import SUPPORTED_METRICS, calculate_progress, validate_metric_key


def build_goal_training_state(
    goal: Any,
    training_snapshots: Iterable[dict[str, Any]],
    *,
    as_of: date | None = None,
) -> dict[str, Any]:
    """Build canonical read-only state joining one goal to training evidence.

    ``training_snapshots`` must contain only completed-session evidence. The
    builder deliberately does not infer progress from missing evidence.
    """
    metric = validate_metric_key(goal.metric_key)
    definition = {"key": metric, **SUPPORTED_METRICS[metric]} if metric else None

    snapshots = [
        {
            "date": item.get("date"),
            "value": float(item["value"]) if item.get("value") is not None else None,
            "session_id": item.get("session_id"),
        }
        for item in training_snapshots
        if item.get("value") is not None and item.get("session_id")
    ]
    snapshots.sort(key=lambda item: (item["date"] or "", item["session_id"] or ""))

    current = snapshots[-1]["value"] if snapshots else None
    calc = (
        calculate_progress(current, goal.baseline_value, goal.target_value, definition["direction"])
        if definition
        else {"percent": None, "remaining": None, "on_track": None}
    )

    trend = None
    if len(snapshots) >= 2:
        delta = snapshots[-1]["value"] - snapshots[-2]["value"]
        trend = "up" if delta > 0 else "down" if delta < 0 else "stable"

    on_track = calc["on_track"]
    reference_date = as_of or date.today()
    if (
        on_track is not True
        and calc["percent"] is not None
        and goal.target_date
        and goal.baseline_value is not None
        and goal.target_value is not None
        and goal.target_date > goal.start_date
    ):
        total_days = (goal.target_date - goal.start_date).days
        elapsed_days = max(0, min(total_days, (reference_date - goal.start_date).days))
        expected_pct = (elapsed_days / total_days) * 100
        on_track = calc["percent"] >= round(expected_pct, 1)

    reason_codes: list[str] = []
    if not metric:
        reason_codes.append("NO_METRIC")
    elif not snapshots:
        reason_codes.append("INSUFFICIENT_TRAINING_EVIDENCE")
    else:
        reason_codes.append("TRAINING_EVIDENCE_AVAILABLE")
    if current is not None and goal.target_value is not None:
        reached = (
            current <= goal.target_value
            if definition and definition["direction"] == "decrease"
            else current >= goal.target_value
        )
        if reached:
            reason_codes.append("TARGET_REACHED")
    if goal.status != "active":
        reason_codes.append("GOAL_NOT_ACTIVE")

    return {
        "goal": {
            "id": goal.id,
            "status": goal.status,
            "goal_type": goal.goal_type,
            "title": goal.title,
            "start_date": goal.start_date.isoformat(),
            "target_date": goal.target_date.isoformat() if goal.target_date else None,
        },
        "metric": definition,
        "baseline_value": goal.baseline_value,
        "target_value": goal.target_value,
        "current_value": current,
        "progress_pct": calc["percent"],
        "remaining": calc["remaining"],
        "on_track": on_track,
        "trend": trend,
        "supporting_session_ids": [item["session_id"] for item in snapshots],
        "latest_supporting_training_date": snapshots[-1]["date"] if snapshots else None,
        "evidence_count": len(snapshots),
        "sufficient_data": bool(snapshots) and current is not None,
        "reason_codes": reason_codes,
    }
