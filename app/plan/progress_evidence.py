"""Canonical Progress -> Planning evidence contract.

Translates already-computed Progress Evidence into a small deterministic
planning input. It does not access the database, mutate plans, or bypass
safety/adaptation rules.
"""

from __future__ import annotations

from math import isfinite
from typing import Any


def build_planning_progress_evidence(
    progress: dict[str, Any] | None,
) -> dict[str, Any]:
    """Normalize canonical Progress Evidence into a planner input."""
    if not isinstance(progress, dict):
        return {
            "status": "insufficient_data",
            "sufficient_data": False,
            "exercise_key": None,
            "recommended_action": "none",
            "reason_codes": ["INVALID_PROGRESS_EVIDENCE"],
            "material_change": False,
            "changes": {},
            "source": "canonical_progress",
            "mutates_plan": False,
        }

    sufficient = (
        progress.get("status") == "sufficient"
        and progress.get("sufficient_data") is True
    )
    if not sufficient:
        return {
            "status": "insufficient_data",
            "sufficient_data": False,
            "exercise_key": progress.get("exercise_key"),
            "recommended_action": "none",
            "reason_codes": list(
                progress.get("reason_codes")
                or ["INSUFFICIENT_PROGRESS_HISTORY"]
            ),
            "material_change": False,
            "changes": {},
            "source": "canonical_progress",
            "mutates_plan": False,
        }

    raw_changes = progress.get("changes")
    finite_changes: dict[str, float] = {}
    if isinstance(raw_changes, dict):
        for key, value in raw_changes.items():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                continue
            numeric = float(value)
            if isfinite(numeric):
                finite_changes[str(key)] = round(numeric, 2)

    action = "maintain"
    relevant = (
        finite_changes.get("average_weight_kg_delta"),
        finite_changes.get("average_reps_delta"),
        finite_changes.get("volume_kg_delta"),
    )
    if progress.get("material_change") is True:
        if any(value > 0 for value in relevant if value is not None):
            action = "progress"
        elif any(value < 0 for value in relevant if value is not None):
            action = "reduce"

    return {
        "status": "sufficient",
        "sufficient_data": True,
        "exercise_key": progress.get("exercise_key"),
        "recommended_action": action,
        "reason_codes": list(progress.get("reason_codes") or []),
        "material_change": bool(progress.get("material_change")),
        "changes": finite_changes,
        "latest": progress.get("latest"),
        "previous": progress.get("previous"),
        "source": "canonical_progress",
        "mutates_plan": False,
    }
