"""Bounded deterministic adaptation policy for Stage 8C.

Pure function only: no database writes, no plan mutation, no user access.
The policy consumes the canonical Stage 8B exercise evaluation contract.
"""

from __future__ import annotations

from typing import Any


ADAPTATION_ALGORITHM = "deterministic-v2"
LOAD_STEP_PCT = 0.025
MAX_LOAD_CHANGE_PCT = 0.05
LOAD_ROUNDING_KG = 2.5


def _round_load(value: float) -> float:
    return round(value / LOAD_ROUNDING_KG) * LOAD_ROUNDING_KG


def adapt_exercise(
    planned: dict[str, Any],
    evaluation: dict[str, Any],
) -> dict[str, Any]:
    """Return one bounded next-plan proposal without mutating the inputs."""
    current_sets = max(0, int(planned.get("sets") or 0))
    current_reps = max(0, int(planned.get("reps") or 0))
    current_weight = max(0.0, float(planned.get("weight_kg") or 0))

    decision = str(evaluation.get("decision") or "insufficient_data")
    action = "unchanged"
    next_reps = current_reps
    next_weight = current_weight

    if decision == "progress":
        action = "progress_load" if current_weight > 0 else "progress_reps"
        if current_weight > 0:
            next_weight = min(
                current_weight * (1 + MAX_LOAD_CHANGE_PCT),
                current_weight * (1 + LOAD_STEP_PCT),
            )
            next_weight = _round_load(next_weight)
        else:
            next_reps = current_reps + 1
    elif decision == "reduce":
        action = "reduce_load" if current_weight > 0 else "reduce_reps"
        if current_weight > 0:
            next_weight = max(
                0.0,
                _round_load(current_weight * (1 - LOAD_STEP_PCT)),
            )
        elif current_reps > 1:
            next_reps = current_reps - 1

    return {
        "exercise_key": str(planned.get("exercise_key") or ""),
        "exercise_name": str(planned.get("exercise_name") or planned.get("name") or "Ćwiczenie"),
        "decision": decision,
        "action": action,
        "current": {
            "sets": current_sets,
            "reps": current_reps,
            "weight_kg": current_weight,
        },
        "proposed": {
            "sets": current_sets,
            "reps": next_reps,
            "weight_kg": next_weight,
        },
        "reason_codes": list(evaluation.get("reason_codes") or []),
        "algorithm": ADAPTATION_ALGORITHM,
        "max_load_change_pct": MAX_LOAD_CHANGE_PCT * 100,
    }
