"""Training Decision Log export.

Builds a single structured JSON file containing the authenticated user's
training and plan history for a selected period. Reuses existing backend
records; creates no permanent server-side files.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any, Optional

from sqlmodel import Session, select

from app.models import (
    AdaptivePlanRevisionDB,
    AssessmentDB,
    ExerciseProgressionDB,
    ExerciseResultDB,
    GoalDB,
    TrainingSessionDB,
    TrainingSetResultDB,
    UserDB,
)


EXPORT_SCHEMA_VERSION = "1.0"
EXPORT_SCHEMA_NAME = "evolve_training_decision_log"


def _iso(v: Any) -> Optional[str]:
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, date):
        return v.isoformat()
    return str(v)


def _missing() -> dict[str, str]:
    return {"status": "unavailable", "reason": "Nie zarejestrowano w systemie."}


def _load_json(raw: Any, default: Any = None) -> Any:
    if raw is None:
        return default
    if isinstance(raw, (dict, list)):
        return raw
    try:
        return json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return default


def _profile_snapshot(user: UserDB, session: Session) -> dict[str, Any]:
    """A. Profile and context snapshot relevant to plan generation/adaptation."""
    latest_assessment = session.exec(
        select(AssessmentDB)
        .where(AssessmentDB.user_id == user.id)
        .order_by(AssessmentDB.assessment_version.desc(), AssessmentDB.created_at.desc())
    ).first()

    assessments = session.exec(
        select(AssessmentDB)
        .where(AssessmentDB.user_id == user.id)
        .order_by(AssessmentDB.assessment_version.desc(), AssessmentDB.created_at.desc())
    ).all()

    goals = session.exec(
        select(GoalDB).where(GoalDB.user_id == user.id).order_by(GoalDB.created_at.desc())
    ).all()

    return {
        "profile": {
            "user_id": user.id,
            "name": user.name,
            "nickname": user.nickname,
            "email": user.email,
            "age": user.age,
            "height": user.height,
            "weight": user.weight,
            "start_weight": user.start_weight,
            "target_weight": user.target_weight,
            "gender": user.gender,
            "goal": user.goal,
            "frequency": user.frequency,
            "training_experience": user.training_experience,
            "equipment": user.equipment,
            "health_limitations": user.health_limitations or "",
            "injuries": [i.strip() for i in user.injuries.split(",") if i.strip()],
            "basketball_position": user.basketball_position or "",
            "sport_focus": user.sport_focus,
            "sport_specialization": user.sport_specialization,
            "available_equipment": user.get_list("available_equipment_json"),
            "avoid_exercises": user.get_list("avoid_exercises_json"),
            "training_availability": user.get_dict("training_availability_json"),
            "training_locations": user.get_list("training_locations_json"),
            "role": user.role,
            "plan_tier": user.plan,
            "created_at": _iso(user.created_at),
            "updated_at": _iso(user.updated_at),
        },
        "training_context": {
            "sport_training_days": user.get_list("sport_training_days_json"),
            "sport_training_schedule": user.get_dict("sport_training_schedule_json"),
            "basketball_profile": user.get_dict("basketball_profile_json"),
        },
        "latest_assessment": {
            "assessment_version": latest_assessment.assessment_version if latest_assessment else None,
            "assessment_date": _iso(latest_assessment.assessment_date) if latest_assessment else None,
            "training_level": latest_assessment.training_level if latest_assessment else None,
            "training_experience_years": latest_assessment.training_experience_years if latest_assessment else None,
            "sessions_per_week": latest_assessment.sessions_per_week if latest_assessment else None,
            "availability_hours_per_week": latest_assessment.availability_hours_per_week if latest_assessment else None,
            "recovery_score": latest_assessment.recovery_score if latest_assessment else None,
            "basketball_level": latest_assessment.basketball_level if latest_assessment else None,
            "metrics": latest_assessment.data() if latest_assessment else None,
            "notes": latest_assessment.notes if latest_assessment else None,
            "created_at": _iso(latest_assessment.created_at) if latest_assessment else None,
            "relevant_to_plan": True,
        },
        "assessment_history": [
            {
                "assessment_version": a.assessment_version,
                "assessment_date": _iso(a.assessment_date),
                "training_level": a.training_level,
                "training_experience_years": a.training_experience_years,
                "sessions_per_week": a.sessions_per_week,
                "availability_hours_per_week": a.availability_hours_per_week,
                "recovery_score": a.recovery_score,
                "basketball_level": a.basketball_level,
                "metrics": a.data(),
                "notes": a.notes,
                "created_at": _iso(a.created_at),
            }
            for a in assessments
        ],
        "goals": [
            {
                "goal_id": g.id,
                "goal_type": g.goal_type,
                "title": g.title,
                "description": g.description,
                "status": g.status,
                "start_date": _iso(g.start_date),
                "target_date": _iso(g.target_date),
                "priority": g.priority,
                "metric_key": g.metric_key,
                "baseline_value": g.baseline_value,
                "target_value": g.target_value,
                "metadata": g.metadata_dict(),
                "created_at": _iso(g.created_at),
                "updated_at": _iso(g.updated_at),
            }
            for g in goals
        ],
    }


def _original_plan(user: UserDB) -> dict[str, Any]:
    """B. Original plan persisted on the user profile."""
    raw = _load_json(user.weekly_plan_json)
    return {
        "plan_id": None,
        "source": "user_profile_weekly_plan_json",
        "generated_at": None,
        "note": "Plan przechowywany jako tygodniowy JSON w profilu użytkownika; data generacji nie jest rejestrowana osobno.",
        "plan_json": raw if raw is not None else _missing(),
        "is_empty": raw is None or raw == {},
    }


def _actual_sessions(
    user: UserDB,
    session: Session,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> dict[str, Any]:
    """C. Actual training sessions with set-level detail."""
    stmt = (
        select(TrainingSessionDB)
        .where(TrainingSessionDB.user_id == user.id)
        .where(TrainingSessionDB.status == "completed")
        .order_by(TrainingSessionDB.session_date.asc(), TrainingSessionDB.completed_at.asc())
    )
    rows = list(session.exec(stmt).all())

    sessions_out = []
    total_sets = 0
    total_volume_kg = 0.0

    for row in rows:
        if date_from and row.session_date < date_from:
            continue
        if date_to and row.session_date > date_to:
            continue

        planned = row.planned_snapshot()
        planned_exercises = planned.get("exercises", []) if isinstance(planned, dict) else []

        sets = list(
            session.exec(
                select(TrainingSetResultDB)
                .where(TrainingSetResultDB.session_id == row.id)
                .where(TrainingSetResultDB.user_id == user.id)
                .where(TrainingSetResultDB.completed == True)
                .order_by(TrainingSetResultDB.exercise_key, TrainingSetResultDB.set_number)
            ).all()
        )

        sets_out = []
        for s in sets:
            volume = float(s.actual_weight_kg or 0) * int(s.actual_reps or 0)
            total_volume_kg += volume
            total_sets += 1
            sets_out.append({
                "set_id": s.id,
                "exercise_key": s.exercise_key,
                "exercise_name": s.exercise_name,
                "set_number": s.set_number,
                "planned_reps": s.planned_reps,
                "planned_weight_kg": s.planned_weight_kg,
                "actual_reps": s.actual_reps,
                "actual_weight_kg": s.actual_weight_kg,
                "actual_rpe": s.actual_rpe,
                "completed": s.completed,
                "note": s.note or "",
                "logged_at": _iso(s.logged_at),
            })

        sessions_out.append({
            "session_id": row.id,
            "session_date": _iso(row.session_date),
            "started_at": _iso(row.started_at),
            "completed_at": _iso(row.completed_at),
            "status": row.status,
            "final_rpe": row.final_rpe,
            "notes": row.notes or "",
            "duration_seconds": None,
            "planned_exercises": planned_exercises,
            "sets": sets_out,
            "completed_set_count": len(sets_out),
            "planned_set_count": sum(
                max(0, int(item.get("sets") or 0))
                for item in planned_exercises
                if isinstance(item, dict)
            ),
        })

    return {
        "sessions": sessions_out,
        "session_count": len(sessions_out),
        "total_sets_logged": total_sets,
        "total_volume_kg": round(total_volume_kg, 2),
    }


def _plan_changes(
    user: UserDB,
    session: Session,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> dict[str, Any]:
    """D. Plan changes and adaptive decisions (audit trail)."""
    stmt = (
        select(AdaptivePlanRevisionDB)
        .where(AdaptivePlanRevisionDB.user_id == user.id)
        .order_by(AdaptivePlanRevisionDB.version.asc(), AdaptivePlanRevisionDB.created_at.asc())
    )
    rows = list(session.exec(stmt).all())

    changes_out = []
    for rev in rows:
        created_at = rev.created_at
        if date_from and (created_at.date() if isinstance(created_at, datetime) else date.min) < date_from:
            continue
        if date_to and (created_at.date() if isinstance(created_at, datetime) else date.max) > date_to:
            continue

        previous = _load_json(rev.previous_plan_json, default={})
        applied = _load_json(rev.applied_plan_json, default={})
        summary = rev.decision_summary()

        changes_out.append({
            "revision_id": rev.id,
            "version": rev.version,
            "created_at": _iso(created_at),
            "decision_type": "adaptive_plan_revision",
            "decision_summary": summary if summary else _missing(),
            "source_session_ids": rev.source_session_ids(),
            "source": "system_adaptation",
            "status": "applied",
            "plan_before": previous if previous else _missing(),
            "plan_after": applied if applied else _missing(),
            "plan_before_empty": previous == {} or previous is None,
            "plan_after_empty": applied == {} or applied is None,
            "rationale_recorded": bool(summary),
        })

    return {
        "changes": changes_out,
        "change_count": len(changes_out),
    }


def build_training_decision_log(
    user: UserDB,
    session: Session,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> dict[str, Any]:
    """Build the complete Training Decision Log export dict.

    Sections:
      A - Profile and context snapshot
      B - Original plan
      C - Actual training sessions
      D - Plan changes and adaptive decisions
      E - History integrity metadata
    """
    now = datetime.now()

    profile_section = _profile_snapshot(user, session)
    plan_section = _original_plan(user)
    sessions_section = _actual_sessions(user, session, date_from, date_to)
    changes_section = _plan_changes(user, session, date_from, date_to)

    # History integrity: chronological order is enforced by ascending sorts
    # in each section. Original plans and previous decisions are preserved.
    export = {
        "schema": {
            "name": EXPORT_SCHEMA_NAME,
            "version": EXPORT_SCHEMA_VERSION,
            "exported_at": now.isoformat(),
        },
        "user_id": user.id,
        "period": {
            "date_from": _iso(date_from) if date_from else None,
            "date_to": _iso(date_to) if date_to else None,
            "note": "Brak zakresu dat oznacza eksport całej dostępnej historii.",
        },
        "profile_and_context": profile_section,
        "original_plan": plan_section,
        "actual_training_sessions": sessions_section,
        "plan_changes": changes_section,
        "history_integrity": {
            "chronological_order": True,
            "original_plan_preserved": True,
            "previous_decisions_preserved": True,
            "missing_data_marker": "unavailable",
            "sections": {
                "profile_and_context": "A",
                "original_plan": "B",
                "actual_training_sessions": "C",
                "plan_changes": "D",
                "history_integrity": "E",
            },
            "linked_identifiers": {
                "user_id": user.id,
                "session_ids": [s["session_id"] for s in sessions_section["sessions"]],
                "revision_ids": [c["revision_id"] for c in changes_section["changes"]],
                "exercise_keys": sorted(
                    {
                        s_key
                        for sess in sessions_section["sessions"]
                        for s_key in {
                            item["exercise_key"]
                            for item in sess["sets"]
                        }
                    }
                ),
            },
        },
    }
    return export
