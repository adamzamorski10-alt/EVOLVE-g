"""Deterministic assessment-to-planning performance signals.

The signal layer is intentionally small, explicit, and bounded. It converts
basketball assessment baselines into stable planning priorities without using
AI, historical guessing, or hidden state.
"""

from __future__ import annotations

from typing import Any


_SIGNAL_ORDER = ("shooting", "free_throw", "speed", "explosiveness")

# Conservative thresholds: a signal is emitted only when the baseline clearly
# indicates an area with room for improvement.
_THRESHOLDS = {
    "shooting": 60.0,
    "free_throw": 70.0,
    "speed": 5.0,          # seconds; higher is slower
    "explosiveness": 45.0, # cm; lower is less explosive
}


def _value(assessment: Any, field: str) -> float | None:
    raw = getattr(assessment, field, None) if assessment is not None else None
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def build_performance_signals(
    assessment: Any,
    *,
    sport_focus: str | None,
) -> dict:
    """Return deterministic, bounded assessment signals.

    Signals are only emitted for basketball-focused users. Missing metrics do
    not produce inferred signals.
    """
    focus = (sport_focus or "").strip().lower()
    if focus != "koszykówka":
        return {"sport": focus or None, "priorities": [], "signals": {}}

    checks = {
        "shooting": _value(assessment, "shooting_pct"),
        "free_throw": _value(assessment, "free_throw_pct"),
        "speed": _value(assessment, "sprint_30m_seconds"),
        "explosiveness": _value(assessment, "vertical_jump_cm"),
    }
    signals: dict[str, dict] = {}
    for key in _SIGNAL_ORDER:
        value = checks[key]
        threshold = _THRESHOLDS[key]
        if value is None:
            continue
        if key in {"shooting", "free_throw"}:
            priority = value < threshold
        elif key == "speed":
            priority = value > threshold
        else:
            priority = value < threshold
        signals[key] = {
            "value": value,
            "threshold": threshold,
            "priority": bool(priority),
        }

    priorities = [key for key in _SIGNAL_ORDER if signals.get(key, {}).get("priority")]
    return {
        "sport": "koszykówka",
        "priorities": priorities,
        "signals": signals,
    }


def _drill_bucket(name: str) -> str | None:
    value = name.lower()
    if any(token in value for token in ("rzut", "shoot", "free throw", "wolny")):
        return "shooting"
    if any(token in value for token in ("sprint", "bieg", "przyspies", "speed")):
        return "speed"
    if any(token in value for token in ("wyskok", "vertical", "skok", "explos")):
        return "explosiveness"
    return None


def prioritize_sport_drills(
    drills: list[dict],
    signals: dict,
    *,
    secondary_drills: list[dict] | None = None,
    max_secondary: int = 2,
) -> list[dict]:
    """Prioritize the selected specialization and add bounded secondary drills.

    Explicit sport specialization remains first-class: its drills stay first
    and are only reordered by matching priorities. If an explicit assessment
    priority has no matching drill in that specialization, at most
    `max_secondary` deterministic drills are appended from the wider sport
    catalog. This makes assessment signals materially affect the generated plan
    without replacing the user's specialization.
    """
    priorities = signals.get("priorities", []) if isinstance(signals, dict) else []
    rank = {key: index for index, key in enumerate(priorities)}
    base = list(drills)
    if not rank:
        return base

    indexed = list(enumerate(base))
    indexed.sort(
        key=lambda pair: (
            0 if _drill_bucket(str(pair[1].get("name", ""))) in rank else 1,
            rank.get(_drill_bucket(str(pair[1].get("name", ""))), len(rank)),
            pair[0],
        )
    )
    ordered = [drill for _, drill in indexed]

    if not secondary_drills or max_secondary <= 0:
        return ordered

    existing_buckets = {
        bucket
        for drill in ordered
        if (bucket := _drill_bucket(str(drill.get("name", "")))) is not None
    }
    seen_names = {str(drill.get("name", "")) for drill in ordered}
    additions: list[dict] = []

    for priority in priorities:
        if len(additions) >= max_secondary or priority in existing_buckets:
            continue
        for candidate in secondary_drills:
            name = str(candidate.get("name", ""))
            if name in seen_names or _drill_bucket(name) != priority:
                continue
            additions.append(candidate)
            seen_names.add(name)
            existing_buckets.add(priority)
            break

    return ordered + additions
