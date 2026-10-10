"""Canonical semantic state mapping for the EVOLVE TODAY surface."""

from __future__ import annotations

from typing import Any

TODAY_STATES = {
    "recover",
    "reduce_training",
    "train_as_planned",
    "progress_training",
    "maintain_training",
    "insufficient_data",
    "rest",
}


def build_today_action(
    *,
    decision: dict[str, Any],
    training: dict[str, Any],
) -> dict[str, Any]:
    """Map canonical Decision Engine output into stable TODAY presentation semantics.

    This function does not decide what the user should do; it only maps an
    already-computed decision into a frontend-safe semantic contract.
    """
    raw_decision = decision.get("decision")
    allowed_decisions = {
        "train_as_planned",
        "reduce_training",
        "recover",
        "progress_training",
        "maintain_training",
        "insufficient_data",
    }
    decision_is_valid = isinstance(raw_decision, str) and raw_decision in allowed_decisions
    decision_key = raw_decision if decision_is_valid else "insufficient_data"
    has_workout = bool(training.get("has_workout"))
    training_can_start = bool(training.get("can_start"))

    if decision_key == "insufficient_data":
        state = "insufficient_data"
        title = "Need more data"
        instruction = "Collect the missing evidence before changing the training direction."
        # Canonical insufficient evidence limits adaptation, but is not itself
        # a safety contraindication. Keep TODAY aligned with the execution gate.
        # An invalid decision payload is different and must fail closed.
        can_start = decision_is_valid and training_can_start and has_workout
        safety_blocked = not decision_is_valid
        data_quality = "insufficient"
    elif decision_key == "recover":
        state = "recover"
        title = "Recover today"
        instruction = "Prioritize recovery and do not start normal training."
        can_start = False
        safety_blocked = True
        data_quality = "sufficient"
    elif decision_key == "reduce_training":
        state = "reduce_training"
        title = "Reduce training"
        instruction = "Follow the constrained effective plan and avoid adding normal volume."
        can_start = training_can_start and has_workout
        safety_blocked = False
        data_quality = "sufficient"
    elif not has_workout:
        state = "rest"
        title = "Rest / no workout planned"
        instruction = "No training session is planned for today."
        can_start = False
        safety_blocked = False
        data_quality = "sufficient"
    elif decision_key == "progress_training":
        state = "progress_training"
        title = "Progress training"
        instruction = "Follow the effective plan and apply only the bounded progression already produced by training adaptation."
        can_start = training_can_start
        safety_blocked = False
        data_quality = "sufficient"
    elif decision_key == "maintain_training":
        state = "maintain_training"
        title = "Maintain training"
        instruction = "Follow the current effective plan without adding progression."
        can_start = training_can_start
        safety_blocked = False
        data_quality = "sufficient"
    else:
        state = "train_as_planned"
        title = "Train as planned"
        instruction = "Follow today's effective training plan as scheduled."
        can_start = training_can_start
        safety_blocked = False
        data_quality = "sufficient"

    reason_codes = (
        [str(code) for code in decision.get("reason_codes", []) if code]
        if decision_is_valid
        else ["INVALID_DECISION_FAIL_CLOSED"]
    )
    return {
        "state": state,
        "primary_action": {
            "key": state,
            "title": title,
            "instruction": instruction,
            "can_start": can_start,
        },
        "explanation": {
            "text": str(decision.get("action") or instruction),
            "reason_codes": reason_codes,
        },
        "safety": {
            "blocked": safety_blocked,
            "priority": str(decision.get("priority") or "normal"),
            "constraints": [str(item) for item in decision.get("constraints", []) if item],
        },
        "workout": {
            "has_workout": has_workout,
            "can_start": can_start,
        },
        "evidence": {
            "goal_ids": [str(item) for item in decision.get("supporting_goal_ids", []) if item],
            "session_ids": [str(item) for item in decision.get("supporting_session_ids", []) if item],
        },
        "data_quality": {
            "status": data_quality,
            "sufficient_data": bool(decision.get("sufficient_data")) and data_quality == "sufficient",
        },
        "read_only": True,
    }
