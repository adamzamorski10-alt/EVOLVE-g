"""Canonical deterministic progress evidence derived from training history.

This module is read-only and contains no optimization/adaptation rules. It
describes measurable changes in completed execution so later Progress UI and
decision layers can consume one stable evidence contract.
"""

from __future__ import annotations

from math import isfinite\nfrom typing import Any


def build_progress_evidence(history: list[dict[str, Any]], *, exercise_key: str | None = None) -> dict[str, Any]:
    """Compare the two most recent completed observations."""
    observations: list[dict[str, Any]] = []
    for session in history:
        for exercise in session.get("exercises", []):
            if exercise_key and exercise.get("exercise_key") != exercise_key:
                continue
            sets = [item for item in exercise.get("sets", []) if item.get("completed")]
            if not sets:
                continue
            weights = [float(item["actual_weight_kg"]) for item in sets if item.get("actual_weight_kg") is not None]
            reps = [int(item["actual_reps"]) for item in sets if item.get("actual_reps") is not None]
            rpes = [float(item["actual_rpe"]) for item in sets if item.get("actual_rpe") is not None]
            if not valid_sets:\n                continue\n            paired_volume = [weight * reps_value for weight, reps_value, _ in valid_sets if weight is not None and reps_value is not None]\n            observations.append({
                "session_id": session.get("session_id"),
                "session_date": session.get("session_date"),
                "exercise_key": exercise.get("exercise_key"),
                "exercise_name": exercise.get("exercise_name"),
                "completed_sets": len(sets),
                "average_weight_kg": round(sum(weights) / len(weights), 2) if weights else None,
                "average_reps": round(sum(reps) / len(reps), 2) if reps else None,
                "average_rpe": round(sum(rpes) / len(rpes), 2) if rpes else None,
                "volume_kg": round(sum(paired_volume), 2) if paired_volume else None,
            })
    observations.sort(key=lambda x: (x.get("session_date") or "", x.get("session_id") or "", x.get("exercise_key") or ""), reverse=True)
    if len(observations) < 2:
        return {"status": "insufficient_data", "sufficient_data": False, "exercise_key": exercise_key, "observations": observations, "changes": {}, "reason_codes": ["INSUFFICIENT_PROGRESS_HISTORY"]}
    latest, previous = observations[0], observations[1]
    def delta(key: str) -> float | None:
        current, prior = latest.get(key), previous.get(key)
        return None if current is None or prior is None else round(float(current) - float(prior), 2)
    changes = {
        "completed_sets_delta": delta("completed_sets"),
        "average_weight_kg_delta": delta("average_weight_kg"),
        "average_reps_delta": delta("average_reps"),
        "average_rpe_delta": delta("average_rpe"),
        "volume_kg_delta": delta("volume_kg"),
    }
    material = any(value is not None and value != 0 for value in changes.values())
    return {"status": "sufficient", "sufficient_data": True, "exercise_key": exercise_key or latest.get("exercise_key"), "latest": latest, "previous": previous, "changes": changes, "material_change": material, "reason_codes": ["MATERIAL_CHANGE" if material else "NO_MATERIAL_CHANGE"]}