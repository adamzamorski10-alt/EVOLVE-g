"""Pure Decision Engine domain integration helpers.

These helpers deliberately adapt existing domain read models without
reimplementing their scoring or adaptation algorithms.
"""
from __future__ import annotations
from typing import Any, Iterable

def summarize_training_signal(evaluation: dict[str, Any], session_id: str | None = None) -> dict[str, Any]:
    return {
        "status": "ready" if evaluation.get("overall_decision") else "insufficient_data",
        "overall_decision": evaluation.get("overall_decision", "insufficient_data"),
        "session_id": session_id,
        "reason_codes": list(evaluation.get("reason_codes", [])),
    }

def summarize_nutrition_signal(response: dict[str, Any] | None) -> dict[str, Any]:
    if not response:
        return {"status": "insufficient_data", "adaptation_allowed": False}
    result = dict(response)
    result.setdefault("adaptation_allowed", False)
    return result
