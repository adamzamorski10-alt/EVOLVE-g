"""Human-readable interpretation of canonical progress evidence.

This layer describes observed changes only. It never recommends, adapts, or
mutates a training plan.
"""

from __future__ import annotations

from math import isfinite
from typing import Any


def explain_progress(evidence: dict[str, Any]) -> dict[str, Any]:
    """Convert progress evidence into deterministic, non-prescriptive changes."""
    if evidence.get("status") != "sufficient" or not evidence.get("sufficient_data"):
        return {
            "status": "insufficient_data",
            "sufficient_data": False,
            "headline": "Brak wystarczających danych do oceny zmian.",
            "changes": [],
            "reason_codes": ["INSUFFICIENT_PROGRESS_HISTORY"],
        }

    changes = evidence.get("changes") or {}
    items: list[dict[str, Any]] = []
    labels = {
        "average_weight_kg_delta": ("load", "Średni ciężar"),
        "average_rpe_delta": ("rpe", "Średnie RPE"),
        "volume_kg_delta": ("volume", "Objętość"),
        "average_reps_delta": ("reps", "Średnia liczba powtórzeń"),
        "completed_sets_delta": ("sets", "Ukończone serie"),
    }
    for key, (metric, label) in labels.items():
        value = changes.get(key)
        if value is None or not isinstance(value, (int, float)) or not isfinite(float(value)) or value == 0:
            continue
        direction = "up" if value > 0 else "down"
        items.append({
            "metric": metric,
            "label": label,
            "direction": direction,
            "delta": value,
        })

    if not items:
        headline = "Brak istotnej zmiany w dostępnych metrykach."
        reason = "NO_MATERIAL_CHANGE"
    else:
        headline = "Zaobserwowano zmiany w wykonaniu treningu."
        reason = "MATERIAL_CHANGE"

    return {
        "status": "sufficient",
        "sufficient_data": True,
        "exercise_key": evidence.get("exercise_key"),
        "headline": headline,
        "changes": items,
        "reason_codes": [reason],
        "source": "progress_evidence",
    }