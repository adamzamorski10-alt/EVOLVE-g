"""Deterministic read-only Decision Engine for the EVOLVE core loop.

This module selects the highest-priority next action from already-materialized
domain signals. It never reads or mutates persistence.
"""
from __future__ import annotations

from typing import Any, Iterable

DECISION_ALGORITHM = "deterministic-decision-v1"

DECISIONS = {
    "train_as_planned",
    "reduce_training",
    "recover",
    "progress_training",
    "maintain_training",
    "insufficient_data",
}


def _goal_ids(states: Iterable[dict[str, Any]]) -> list[str]:
    return [str(item["goal"]["id"]) for item in states if item.get("goal", {}).get("id")]


def _session_ids(states: Iterable[dict[str, Any]]) -> list[str]:
    result: list[str] = []
    for state in states:
        result.extend(str(item) for item in state.get("supporting_session_ids", []) if item)
    return list(dict.fromkeys(result))


def build_decision(
    *,
    goal_states: Iterable[dict[str, Any]],
    recovery: dict[str, Any] | None = None,
    nutrition: dict[str, Any] | None = None,
    training: dict[str, Any] | None = None,
    constraints: Iterable[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Select one deterministic next action from materialized evidence.

    Inputs are trusted, already-authenticated domain read models. The function
    performs no I/O and never mutates its inputs.
    """
    states = [dict(item) for item in goal_states]
    recovery = dict(recovery or {})
    nutrition = dict(nutrition or {})
    training = dict(training or {})
    explicit_constraints = [dict(item) for item in (constraints or [])]

    goal_ids = _goal_ids(states)
    supporting_sessions = _session_ids(states)
    reason_codes: list[str] = []
    decision = "train_as_planned"
    priority = "normal"
    action = "Continue with the current effective training plan."
    constraint_names: list[str] = []

    critical_missing = not states and not recovery and not training
    recovery_status = recovery.get("status")
    recovery_constraint = recovery.get("constraint", "none")

    if critical_missing:
        decision = "insufficient_data"
        priority = "low"
        action = "Collect enough goal, training, or recovery evidence before optimizing."
        reason_codes.append("INSUFFICIENT_CORE_CONTEXT")
    elif recovery_status == "insufficient_data" and not states and not training:
        decision = "insufficient_data"
        priority = "low"
        action = "Collect more evidence before changing training."
        reason_codes.append("INSUFFICIENT_RECOVERY_DATA")
    elif recovery_constraint == "reduce_volume_50" or recovery_status == "recovery":
        decision = "recover"
        priority = "critical"
        action = "Prioritize recovery and avoid normal training volume."
        reason_codes.append("RECOVERY_OVERRIDE")
        if recovery_constraint != "none":
            constraint_names.append(str(recovery_constraint))
    elif recovery_constraint == "reduce_volume_25" or recovery_status == "caution":
        decision = "reduce_training"
        priority = "high"
        action = "Train with reduced volume because recovery is constrained."
        reason_codes.append("RECOVERY_CONSTRAINT")
        constraint_names.append(str(recovery_constraint or "reduce_volume_25"))
    elif explicit_constraints:
        decision = "reduce_training"
        priority = "high"
        action = "Respect the active training constraints before optimizing progression."
        reason_codes.append("ACTIVE_TRAINING_CONSTRAINT")
        constraint_names.extend(
            str(item.get("key") or item.get("constraint") or "unknown")
            for item in explicit_constraints
        )
    elif training.get("overall_decision") == "reduce":
        decision = "reduce_training"
        priority = "high"
        action = "Reduce training because completed-session evaluation requires it."
        reason_codes.append("TRAINING_REQUIRES_REDUCTION")
        if training.get("session_id"):
            supporting_sessions.append(str(training["session_id"]))
    elif training.get("overall_decision") == "progress":
        decision = "progress_training"
        priority = "normal"
        action = "Use the existing bounded training adaptation for the evaluated session."
        reason_codes.append("TRAINING_READY_TO_PROGRESS")
        if training.get("session_id"):
            supporting_sessions.append(str(training["session_id"]))
    elif training.get("status") == "insufficient_data" or training.get("overall_decision") == "insufficient_data":
        decision = "insufficient_data"
        priority = "low"
        action = "Collect completed training evidence before changing the training direction."
        reason_codes.append("TRAINING_DATA_INSUFFICIENT")
    else:
        usable_states = [item for item in states if item.get("sufficient_data")]
        if not usable_states:
            decision = "insufficient_data"
            priority = "low"
            action = "Collect completed training evidence before changing the plan."
            reason_codes.append("INSUFFICIENT_GOAL_TRAINING_EVIDENCE")
        else:
            progress_states = [item for item in usable_states if item.get("on_track") is True and item.get("trend") == "up"]
            maintain_states = [item for item in usable_states if item.get("on_track") is not True]
            if training.get("status") == "ready" and training.get("overall_decision") == "reduce":
                decision = "reduce_training"
                priority = "high"
                action = "Reduce training based on the completed-session evaluation."
                reason_codes.append("TRAINING_EVALUATION_REDUCE")
            elif training.get("status") == "ready" and training.get("overall_decision") == "maintain":
                decision = "maintain_training"
                priority = "normal"
                action = "Maintain training based on the completed-session evaluation."
                reason_codes.append("TRAINING_EVALUATION_MAINTAIN")
            elif progress_states:
                decision = "progress_training"
                priority = "normal"
                action = "Use the existing bounded training adaptation for goals showing positive evidence."
                reason_codes.append("GOAL_TRAINING_PROGRESS")
            elif maintain_states:
                decision = "maintain_training"
                priority = "normal"
                action = "Maintain the current training direction and collect more evidence."
                reason_codes.append("GOAL_TRAINING_MAINTAIN")
            else:
                decision = "train_as_planned"
                reason_codes.append("NO_MATERIAL_CHANGE")

    if nutrition.get("status") == "insufficient_data":
        reason_codes.append("NUTRITION_DATA_INSUFFICIENT")
    elif nutrition.get("adaptation_allowed") is False:
        reason_codes.append("NUTRITION_ADAPTATION_DISABLED")

    supporting_sessions = list(dict.fromkeys(supporting_sessions))

    return {
        "decision": decision,
        "priority": priority,
        "action": action,
        "reason_codes": list(dict.fromkeys(reason_codes)),
        "supporting_goal_ids": goal_ids,
        "supporting_session_ids": supporting_sessions,
        "constraints": list(dict.fromkeys(constraint_names)),
        "sufficient_data": decision != "insufficient_data",
        "algorithm_version": DECISION_ALGORITHM,
        "mutates_plan": False,
    }
