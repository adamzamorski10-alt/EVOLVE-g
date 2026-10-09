"""Canonical deterministic progress evidence derived from training history.

This module is read-only and contains no optimization/adaptation rules.
"""

from __future__ import annotations

from math import isfinite
from typing import Any


def build_progress_evidence(
    history: list[dict[str, Any]], *, exercise_key: str | None = None
) -> dict[str, Any]:
    """Compare the two most recent completed observations."""
    observations: list[dict[str, Any]] = []

    for session in history:
        if not isinstance(session, dict):
            continue
        raw_exercises = session.get("exercises")
        if not isinstance(raw_exercises, list):
            continue
        for exercise in raw_exercises:
            if not isinstance(exercise, dict):
                continue
            if exercise_key and exercise.get("exercise_key") != exercise_key:
                continue

            raw_sets = exercise.get("sets")
            if not isinstance(raw_sets, list):
                continue
            sets = [
                item for item in raw_sets
                if isinstance(item, dict) and item.get("completed") is True
            ]
            if not sets:
                continue

            valid_sets: list[tuple[float | None, int | None, float | None]] = []
            for item in sets:
                weight = item.get("actual_weight_kg")
                reps = item.get("actual_reps")
                rpe = item.get("actual_rpe")

                try:
                    parsed_weight = float(weight) if weight is not None else None
                    parsed_reps = int(reps) if reps is not None else None
                    parsed_rpe = float(rpe) if rpe is not None else None
                except (TypeError, ValueError, OverflowError):
                    continue

                numeric_values = (
                    parsed_weight, parsed_reps, parsed_rpe
                )
                if any(
                    value is not None and not isfinite(float(value))
                    for value in numeric_values
                ):
                    malformed = True
                    continue

                if parsed_weight is None and parsed_reps is None and parsed_rpe is None:
                    continue

                valid_sets.append((parsed_weight, parsed_reps, parsed_rpe))

            if not valid_sets:
                continue

            weights = [
                weight for weight, _, _ in valid_sets if weight is not None
            ]
            reps = [
                reps_value for _, reps_value, _ in valid_sets
                if reps_value is not None
            ]
            rpes = [
                rpe for _, _, rpe in valid_sets if rpe is not None
            ]
            paired_volume = [
                weight * reps_value
                for weight, reps_value, _ in valid_sets
                if weight is not None and reps_value is not None
            ]

            observations.append(
                {
                    "session_id": session.get("session_id"),
                    "session_date": session.get("session_date"),
                    "exercise_key": exercise.get("exercise_key"),
                    "exercise_name": exercise.get("exercise_name"),
                    "completed_sets": len(valid_sets),
                    "average_weight_kg": (
                        round(sum(weights) / len(weights), 2)
                        if weights else None
                    ),
                    "average_reps": (
                        round(sum(reps) / len(reps), 2)
                        if reps else None
                    ),
                    "average_rpe": (
                        round(sum(rpes) / len(rpes), 2)
                        if rpes else None
                    ),
                    "volume_kg": (
                        round(sum(paired_volume), 2)
                        if paired_volume else None
                    ),
                }
            )

    observations.sort(
        key=lambda item: (
            item.get("session_date") or "",
            item.get("session_id") or "",
            item.get("exercise_key") or "",
        ),
        reverse=True,
    )

    if len(observations) < 2:
        return {
            "status": "insufficient_data",
            "sufficient_data": False,
            "exercise_key": exercise_key,
            "observations": observations,
            "changes": {},
            "reason_codes": ["INSUFFICIENT_PROGRESS_HISTORY"],
        }

    latest, previous = observations[0], observations[1]

    def delta(key: str) -> float | None:
        current, prior = latest.get(key), previous.get(key)
        if current is None or prior is None:
            return None
        return round(float(current) - float(prior), 2)

    changes = {
        "completed_sets_delta": delta("completed_sets"),
        "average_weight_kg_delta": delta("average_weight_kg"),
        "average_reps_delta": delta("average_reps"),
        "average_rpe_delta": delta("average_rpe"),
        "volume_kg_delta": delta("volume_kg"),
    }
    material = any(
        value is not None and value != 0
        for value in changes.values()
    )

    return {
        "status": "sufficient",
        "sufficient_data": True,
        "exercise_key": exercise_key or latest.get("exercise_key"),
        "latest": latest,
        "previous": previous,
        "changes": changes,
        "material_change": material,
        "reason_codes": [
            "MATERIAL_CHANGE" if material else "NO_MATERIAL_CHANGE"
        ],
    }
