"""Deterministic sport ratings calculated only from canonical attempts."""

from datetime import date, timedelta
from typing import Iterable

RATING_ANCHORS = (25.0, 50.0, 75.0, 95.0)
WINDOW_DAYS = 90
MIN_ATTEMPTS = 20
CALIBRATION = {
    "speed": {"calibrated": False, "anchors": (12.0, 11.0, 10.0, 9.0)},
    "jump": {"calibrated": False, "anchors": (20.0, 35.0, 50.0, 65.0)},
}


def _interpolate(value: float, anchors: tuple[float, ...], *, inverse: bool = False) -> float:
    points = list(anchors)
    if inverse:
        points = [-point for point in points]
        value = -value
    if value <= points[0]:
        return RATING_ANCHORS[0]
    for index in range(1, len(points)):
        if value <= points[index]:
            ratio = (value - points[index - 1]) / (points[index] - points[index - 1])
            return round(RATING_ANCHORS[index - 1] + ratio * 20, 1)
    return RATING_ANCHORS[-1]


def _shot_score(category: str, percentage: float) -> float:
    anchors = {
        "free": (40, 60, 75, 88),
        "layup": (40, 60, 75, 88),
        "mid": (25, 38, 48, 58),
        "three": (20, 30, 38, 45),
        "shot": (40, 60, 75, 88),
    }.get(category, (40, 60, 75, 88))
    return _interpolate(percentage, anchors)


def calculate_sport_ratings(rows: Iterable, today: date | None = None) -> dict:
    today = today or date.today()
    cutoff = today - timedelta(days=WINDOW_DAYS)
    current = [row for row in rows if row.attempt_date >= cutoff and row.attempt_date <= today]
    previous = [row for row in rows if today - timedelta(days=180) <= row.attempt_date < cutoff]
    details: dict[str, dict] = {}
    ratings: dict[str, float | None] = {}
    for category in ("free", "layup", "mid", "three", "handle", "speed", "jump", "defense", "condition"):
        matching = [row for row in current if row.category == category]
        count = sum((row.attempts or 0) for row in matching)
        if category in {"speed", "jump"}:
            values = [row.value for row in matching if row.value is not None]
            sufficient = len(values) >= 1
            score = None
            if sufficient:
                average = sum(values) / len(values)
                score = _interpolate(average, CALIBRATION[category]["anchors"], inverse=category == "speed")
        else:
            made = sum((row.made or 0) for row in matching)
            errors = sum((row.errors or 0) for row in matching)
            denominator = count or sum((row.attempts or 0) for row in matching)
            sufficient = denominator >= MIN_ATTEMPTS
            percentage = (made / denominator * 100) if denominator else None
            if category == "handle" and denominator:
                percentage = (1 - errors / denominator) * 100
            score = _shot_score(category, percentage) if sufficient and percentage is not None else None
        ratings[category] = score
        details[category] = {
            "attempts": count,
            "measurements": len(matching),
            "rating": score,
            "reason": None if score is not None else ("brak testu" if category in {"defense", "condition"} else f"brakuje: {max(0, MIN_ATTEMPTS - count)} prób"),
        }

    measured = [value for value in ratings.values() if value is not None]
    overall = round(sum(measured) / len(measured), 1) if len(measured) >= 3 else None
    overall_reason = None if overall is not None else "brakuje: minimum 3 zmierzone umiejętności"
    total_attempts = sum(item["attempts"] for item in details.values())
    newest = max((row.attempt_date for row in current), default=None)
    days_old = (today - newest).days if newest else None
    confidence = "wysoka" if total_attempts >= 100 and len(measured) >= 4 and (days_old or 999) <= 30 else (
        "średnia" if total_attempts >= 40 and len(measured) >= 2 and (days_old or 999) <= 90 else "niska"
    )
    trend: dict[str, float | None] = {}
    for category in ratings:
        old = [row for row in previous if row.category == category]
        if not old or ratings[category] is None:
            trend[category] = None
            continue
        old_score = calculate_sport_ratings(old, today=cutoff - timedelta(days=1))["ratings"].get(category)
        trend[category] = round(ratings[category] - old_score, 1) if old_score is not None else None
    return {
        "ratings": ratings,
        "details": details,
        "overall": overall,
        "overall_reason": overall_reason,
        "confidence": confidence,
        "trend": trend,
        "calibration": {"speed": False, "jump": False},
    }
