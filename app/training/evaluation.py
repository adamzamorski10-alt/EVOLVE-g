"""Deterministic training-result evaluation for the Stage 8 adaptation loop.

This module is deliberately side-effect free. It converts an executed session
snapshot plus completed set results into structured, explainable decisions.
"""

from __future__ import annotations

from typing import Any


HIGH_RPE_THRESHOLD = 8.0
LOW_COMPLETION_PCT = 80.0


def evaluate_exercise(
    planned: dict[str, Any],
    completed_sets: list[Any],
) -> dict[str, Any]:
    """Evaluate one planned exercise without mutating input data."""
    planned_sets = max(0, int(planned.get("sets") or 0))
    planned_reps = max(0, int(planned.get("reps") or 0))
    planned_weight = max(0.0, float(planned.get("weight_kg") or 0))

    completed_count = len(completed_sets)
    completion_pct = (
        round((completed_count / planned_sets) * 100, 1)
        if planned_sets
        else 0.0
    )

    reps = [max(0, int(item.actual_reps or 0)) for item in completed_sets]
    weights = [max(0.0, float(item.actual_weight_kg or 0)) for item in completed_sets]
    rpes = [
        float(item.actual_rpe)
        for item in completed_sets
        if item.actual_rpe is not None
    ]

    average_reps = round(sum(reps) / len(reps), 2) if reps else None
    average_weight = round(sum(weights) / len(weights), 2) if weights else None
    average_rpe = round(sum(rpes) / len(rpes), 2) if rpes else None

    if completed_count == 0:
        decision = "insufficient_data"
        reason_codes = ["NO_COMPLETED_SETS"]
    elif planned_sets == 0:
        decision = "insufficient_data"
        reason_codes = ["NO_PLANNED_SETS"]
    elif completion_pct < LOW_COMPLETION_PCT:
        decision = "reduce"
        reason_codes = ["LOW_SET_COMPLETION"]
    elif average_rpe is not None and average_rpe > HIGH_RPE_THRESHOLD:
        decision = "maintain"
        reason_codes = ["HIGH_RPE"]
    elif planned_reps > 0 and average_reps is not None and average_reps < planned_reps:
        decision = "maintain"
        reason_codes = ["REPS_BELOW_TARGET"]
    else:
        decision = "progress"
        reason_codes = ["TARGET_COMPLETED"]

    return {
        "decision": decision,
        "reason_codes": reason_codes,
        "planned_sets": planned_sets,
        "completed_sets": completed_count,
        "completion_pct": completion_pct,
        "planned_reps": planned_reps,
        "average_actual_reps": average_reps,
        "planned_weight_kg": planned_weight,
        "average_actual_weight_kg": average_weight,
        "average_rpe": average_rpe,
    }


def evaluate_session(
    planned_items: list[dict[str, Any]],
    completed_by_exercise: dict[str, list[Any]],
) -> dict[str, Any]:
    """Evaluate all exercises in a session with deterministic precedence."""
    exercises = []

    for index, planned in enumerate(planned_items):
        if not isinstance(planned, dict):
            continue

        key = str(
            planned.get("exercise_key")
            or planned.get("id")
            or planned.get("item_id")
            or f"exercise-{index + 1}"
        )
        result = evaluate_exercise(
            planned,
            completed_by_exercise.get(key, []),
        )
        result["exercise_key"] = key
        result["exercise_name"] = str(
            planned.get("exercise_name")
            or planned.get("name")
            or "Ćwiczenie"
        )
        exercises.append(result)

    decisions = [item["decision"] for item in exercises]
    if not decisions or all(item == "insufficient_data" for item in decisions):
        overall = "insufficient_data"
        overall_reason_codes = ["INSUFFICIENT_SESSION_DATA"]
    elif "reduce" in decisions:
        overall = "reduce"
        overall_reason_codes = ["EXERCISE_REQUIRES_REDUCTION"]
    elif "maintain" in decisions:
        overall = "maintain"
        overall_reason_codes = ["EXERCISE_REQUIRES_MAINTENANCE"]
    elif "insufficient_data" in decisions:
        overall = "maintain"
        overall_reason_codes = ["INSUFFICIENT_EXERCISE_DATA"]
    else:
        overall = "progress"
        overall_reason_codes = ["ALL_EXERCISES_READY_TO_PROGRESS"]

    summary = {
        "progress": sum(item == "progress" for item in decisions),
        "maintain": sum(item == "maintain" for item in decisions),
        "reduce": sum(item == "reduce" for item in decisions),
        "insufficient_data": sum(item == "insufficient_data" for item in decisions),
    }

    return {
        "overall_decision": overall,
        "overall_reason_codes": overall_reason_codes,
        "summary": summary,
        "exercises": exercises,
        "rules": {
            "high_rpe_threshold": HIGH_RPE_THRESHOLD,
            "low_completion_pct": LOW_COMPLETION_PCT,
            "mutates_plan": False,
        },
    }
