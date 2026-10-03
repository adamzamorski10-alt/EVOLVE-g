"""Deterministic recovery/readiness response for the EVOLVE core loop."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.auth.dependencies import get_current_user
from app.database import get_session
from app.models import DailyLogDB, UserDB

router = APIRouter(prefix="/app/recovery", tags=["recovery"])

_SIGNAL_LABELS = {
    "sleep_hours": "sen",
    "sleep_quality": "jakość snu",
    "energy_level": "energia",
    "stress_level": "stres",
    "fatigue_score": "zmęczenie",
    "mood_score": "nastrój",
}


def _signal_scores(log: DailyLogDB) -> dict[str, float]:
    scores: dict[str, float] = {}
    if log.sleep_hours is not None:
        scores["sleep_hours"] = min(float(log.sleep_hours) / 8.0, 1.0) * 100.0
    if log.sleep_quality is not None:
        scores["sleep_quality"] = float(log.sleep_quality) * 10.0
    if log.energy_level is not None:
        scores["energy_level"] = float(log.energy_level) * 10.0
    if log.stress_level is not None:
        scores["stress_level"] = (11.0 - float(log.stress_level)) * 10.0
    if log.fatigue_score is not None:
        scores["fatigue_score"] = (11.0 - float(log.fatigue_score)) * 10.0
    if log.mood_score is not None:
        scores["mood_score"] = float(log.mood_score) * 20.0
    return {key: round(max(0.0, min(100.0, value)), 1) for key, value in scores.items()}


def evaluate_recovery(log: DailyLogDB | None) -> dict[str, Any]:
    if log is None:
        return {"status": "insufficient_data", "readiness_score": None, "signal_count": 0, "signals": {}, "constraint": "none", "plan_effect": "Brak zmian planu — uzupełnij dzisiejszy check-in.", "message": "Brakuje danych recovery z dzisiejszego check-inu."}

    scores = _signal_scores(log)
    if len(scores) < 2:
        return {"status": "insufficient_data", "readiness_score": round(sum(scores.values()) / len(scores), 1) if scores else None, "signal_count": len(scores), "signals": scores, "constraint": "none", "plan_effect": "Brak automatycznej zmiany planu przy niewystarczających danych.", "message": "Uzupełnij co najmniej dwa sygnały recovery."}

    score = round(sum(scores.values()) / len(scores), 1)
    if score >= 75:
        status, constraint, effect, message = "ready", "none", "Plan bez redukcji objętości.", "Recovery wygląda dobrze — utrzymaj zaplanowaną objętość."
    elif score >= 55:
        status, constraint, effect, message = "caution", "reduce_volume_25", "Objętość ćwiczeń zostanie ograniczona o około 25%.", "Recovery jest umiarkowane — wykonaj trening z mniejszą objętością."
    else:
        status, constraint, effect, message = "recovery", "reduce_volume_50", "Objętość ćwiczeń zostanie ograniczona o około 50%.", "Recovery jest niskie — priorytetem jest ograniczenie obciążenia."

    return {"status": status, "readiness_score": score, "signal_count": len(scores), "signals": scores, "signal_labels": {key: _SIGNAL_LABELS[key] for key in scores}, "constraint": constraint, "plan_effect": effect, "message": message}


def recovery_for_date(session: Session, user_id: str, target_date: date) -> dict[str, Any]:
    log = session.exec(select(DailyLogDB).where(DailyLogDB.user_id == user_id).where(DailyLogDB.log_date == target_date)).first()
    result = evaluate_recovery(log)
    result["date"] = target_date.isoformat()
    result["has_checkin"] = log is not None
    return result


@router.get("/today")
def get_recovery_today(user: UserDB = Depends(get_current_user), session: Session = Depends(get_session)):
    return recovery_for_date(session, user.id, date.today())


@router.get("/history")
def get_recovery_history(days: int = Query(default=14, ge=1, le=28), user: UserDB = Depends(get_current_user), session: Session = Depends(get_session)):
    start = date.today() - timedelta(days=days - 1)
    rows = list(session.exec(select(DailyLogDB).where(DailyLogDB.user_id == user.id).where(DailyLogDB.log_date >= start).where(DailyLogDB.log_date <= date.today()).order_by(DailyLogDB.log_date.desc())).all())
    by_date = {row.log_date: evaluate_recovery(row) for row in rows}
    history = []
    for offset in range(days):
        target = date.today() - timedelta(days=offset)
        item = by_date.get(target)
        history.append({"date": target.isoformat(), **(item if item else {"status": "missing", "readiness_score": None, "signal_count": 0, "signals": {}, "constraint": "none", "message": "Brak check-inu."})})
    scored = [item for item in history if item.get("readiness_score") is not None]
    constrained = [item for item in history if item.get("constraint") in {"reduce_volume_25", "reduce_volume_50"}]
    summary = {
        "days_with_data": len(scored),
        "missing_days": sum(1 for item in history if item.get("status") == "missing"),
        "average_readiness": round(sum(item["readiness_score"] for item in scored) / len(scored), 1) if scored else None,
        "constrained_days": len(constrained),
        "recovery_days": sum(1 for item in history if item.get("constraint") == "reduce_volume_50"),
        "caution_days": sum(1 for item in history if item.get("constraint") == "reduce_volume_25"),
    }
    return {"days": days, "history": history, "summary": summary}
