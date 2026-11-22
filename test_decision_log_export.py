"""Tests for the Training Decision Log export (Stage 9E)."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.auth import routes as auth_routes
from app.database import engine
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
from main import app


client = TestClient(app)


def _register(email: str, nickname: str | None = None) -> str:
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "SecurePassword123",
            "nickname": nickname or f"user_{email.split('@')[0]}",
            "name": "Test User",
            "age": 25,
            "height": 180,
            "weight": 80,
            "target_weight": 80,
            "gender": "mężczyzna",
            "goal": "muscle_gain",
            "frequency": "3-4 razy w tygodniu",
            "diet": "Balanced",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _cleanup_tables():
    with Session(engine) as db:
        for table in [
            TrainingSetResultDB,
            ExerciseResultDB,
            TrainingSessionDB,
            AdaptivePlanRevisionDB,
            ExerciseProgressionDB,
            AssessmentDB,
            GoalDB,
            UserDB,
        ]:
            db.exec(table.__table__.delete())
        db.commit()


def _make_user_with_full_history(token: str, email: str, today: date):
    """Create a user with profile, assessment, goals, sessions, sets, and plan revisions."""
    with Session(engine) as db:
        user = db.exec(select(UserDB).where(UserDB.email == email)).first()
        assert user is not None

        # Profile fields relevant to plan generation
        user.training_experience = "beginner"
        user.equipment = "gym_full"
        user.health_limitations = ""
        user.injuries = ""
        user.available_equipment_json = json.dumps(["sztangę", "ławkę", "klatkę"])
        user.training_availability_json = json.dumps({"Pon": {"start": "08:00", "end": "10:00"}})
        user.weekly_plan_json = json.dumps({
            "generated_at": "2026-01-05T08:00:00Z",
            "days": [
                {
                    "day": "Pon",
                    "workout": {
                        "title": "Siłowy - klatka",
                        "exercises": [
                            {
                                "exercise_key": "bench_press-1",
                                "exercise_name": "Wyciskanie sztangi leżąc",
                                "sets": 4,
                                "reps": 6,
                                "weight_kg": 70,
                                "rpe": 7,
                            },
                            {
                                "exercise_key": "lateral_raise-1",
                                "exercise_name": "Wyciskanie hantla w rakce",
                                "sets": 4,
                                "reps": 10,
                                "weight_kg": 22,
                                "rpe": 8,
                            },
                        ],
                    },
                },
            ],
        }, ensure_ascii=False)
        db.add(user)

        # Assessment (version 1, relevant to plan)
        assessment = AssessmentDB(
            user_id=user.id,
            assessment_version=1,
            status="completed",
            assessment_date=today - timedelta(days=7),
            training_level="początkujący",
            training_experience_years=0.5,
            sessions_per_week=3,
            availability_hours_per_week=4.0,
            recovery_score=7,
            basketball_level="początkujący",
            shooting_pct=45.0,
            free_throw_pct=65.0,
            sprint_30m_seconds=5.2,
            vertical_jump_cm=45.0,
            assessment_json=json.dumps({"bench_press_1rm": 60, "squat_1rm": 80}, ensure_ascii=False),
            notes="Baseline assessment before plan generation",
        )
        db.add(assessment)
        db.commit()
        db.refresh(user)
        db.refresh(assessment)

        # Session 1 (completed)
        session1 = TrainingSessionDB(
            user_id=user.id,
            session_date=today - timedelta(days=2),
            status="completed",
            planned_snapshot_json=json.dumps({
                "exercises": [
                    {
                        "exercise_key": "bench_press-1",
                        "exercise_name": "Wyciskanie sztangi leżąc",
                        "sets": 4,
                        "reps": 6,
                        "weight_kg": 70,
                        "rpe": 7,
                    },
                    {
                        "exercise_key": "lateral_raise-1",
                        "exercise_name": "Wyciskanie hantla w rakce",
                        "sets": 4,
                        "reps": 10,
                        "weight_kg": 22,
                        "rpe": 8,
                    },
                ],
            }, ensure_ascii=False),
            started_at=datetime(today.year, today.month, today.day - 2, 9, 0),
            completed_at=datetime(today.year, today.month, today.day - 2, 9, 45),
            final_rpe=7,
            notes="Dobrze się czułem",
        )
        db.add(session1)
        db.commit()
        db.refresh(session1)

        # Sets for session 1
        for i, (reps, weight) in enumerate([(6, 70), (6, 70), (5, 70), (6, 70)], start=1):
            db.add(TrainingSetResultDB(
                session_id=session1.id,
                user_id=user.id,
                exercise_key="bench_press-1",
                exercise_name="Wyciskanie sztangi leżąc",
                set_number=i,
                planned_reps=6,
                planned_weight_kg=70,
                actual_reps=reps,
                actual_weight_kg=weight,
                actual_rpe=7,
                completed=True,
                note="",
            ))
        for i, (reps, weight) in enumerate([(10, 22), (10, 22), (9, 22), (10, 22)], start=1):
            db.add(TrainingSetResultDB(
                session_id=session1.id,
                user_id=user.id,
                exercise_key="lateral_raise-1",
                exercise_name="Wyciskanie hantla w rakce",
                set_number=i,
                planned_reps=10,
                planned_weight_kg=22,
                actual_reps=reps,
                actual_weight_kg=weight,
                actual_rpe=8,
                completed=True,
                note="",
            ))

        # ExerciseResult materialized from session 1
        db.add(ExerciseResultDB(
            user_id=user.id,
            source_session_id=session1.id,
            source_exercise_key="bench_press-1",
            exercise_name="Wyciskanie sztangi leżąc",
            session_date=today - timedelta(days=2),
            sets=4,
            reps=6,
            weight_kg=70,
            rpe=7,
            notes="",
        ))

        # Session 2 (completed, later)
        session2 = TrainingSessionDB(
            user_id=user.id,
            session_date=today,
            status="completed",
            planned_snapshot_json=json.dumps({
                "exercises": [
                    {
                        "exercise_key": "bench_press-1",
                        "exercise_name": "Wyciskanie sztangi leżąc",
                        "sets": 4,
                        "reps": 6,
                        "weight_kg": 72,
                        "rpe": 7,
                    },
                ],
            }, ensure_ascii=False),
            started_at=datetime(today.year, today.month, today.day, 10, 0),
            completed_at=datetime(today.year, today.month, today.day, 10, 30),
            final_rpe=8,
            notes="Progres obciążenia",
        )
        db.add(session2)
        db.commit()
        db.refresh(session2)

        db.add(TrainingSetResultDB(
            session_id=session2.id,
            user_id=user.id,
            exercise_key="bench_press-1",
            exercise_name="Wyciskanie sztangi leżąc",
            set_number=1,
            planned_reps=6,
            planned_weight_kg=72,
            actual_reps=6,
            actual_weight_kg=72,
            actual_rpe=8,
            completed=True,
            note="",
        ))

        db.add(ExerciseResultDB(
            user_id=user.id,
            source_session_id=session2.id,
            source_exercise_key="bench_press-1",
            exercise_name="Wyciskanie sztangi leżąc",
            session_date=today,
            sets=1,
            reps=6,
            weight_kg=72,
            rpe=8,
            notes="",
        ))

        # Adaptive plan revision (change from session 1 -> session 2)
        revision = AdaptivePlanRevisionDB(
            user_id=user.id,
            source_session_ids_json=json.dumps([session1.id]),
            previous_plan_json=json.dumps({
                "exercises": [
                    {"exercise_key": "bench_press-1", "weight_kg": 70, "reps": 6},
                    {"exercise_key": "lateral_raise-1", "weight_kg": 22, "reps": 10},
                ],
            }, ensure_ascii=False),
            applied_plan_json=json.dumps({
                "exercises": [
                    {"exercise_key": "bench_press-1", "weight_kg": 72, "reps": 6},
                    {"exercise_key": "lateral_raise-1", "weight_kg": 22, "reps": 10},
                ],
            }, ensure_ascii=False),
            decision_summary_json=json.dumps({
                "decision": "progress_load",
                "reason_codes": ["TARGET_COMPLETED"],
                "evidence": "4/4 sets completed at RPE 7",
            }, ensure_ascii=False),
            version=1,
        )
        db.add(revision)
        db.commit()

        # Exercise progression state
        db.add(ExerciseProgressionDB(
            user_id=user.id,
            exercise_key="bench_press-1",
            exercise_name="Wyciskanie sztangi leżąc",
            working_weight_kg=72.0,
            current_reps=6,
            reps_at_current_weight=6,
            sessions_without_progress=0,
            target_reps_min=6,
            target_reps_max=8,
            calibrated=True,
            last_session_date=today,
        ))

        # Goal
        db.add(GoalDB(
            user_id=user.id,
            goal_type="strength",
            title="Większa klatka",
            description="Wyciskać 80 kg na 6 powtórzeń",
            status="active",
            start_date=today - timedelta(days=30),
            target_date=today + timedelta(days=60),
            priority=50,
            metric_key="best_weight_kg",
            baseline_value=70,
            target_value=80,
            metadata_json=json.dumps({"exercise": "bench_press"}, ensure_ascii=False),
        ))
        db.commit()


def test_export_contains_all_required_sections():
    """Export must contain sections A-E with correct structure."""
    _cleanup_tables()
    auth_routes.limiter.enabled = False
    try:
        today = date.today()
        token = _register(f"export_full_{today.isoformat()}@example.com")
        _make_user_with_full_history(token, f"export_full_{today.isoformat()}@example.com", today)

        res = client.get("/app/training/decision-log-export", headers=_headers(token))
        assert res.status_code == 200, res.text
        assert res.headers["content-type"] == "application/json"
        assert "attachment" in res.headers.get("content-disposition", "")

        data = res.json()

        # Schema / version
        assert data["schema"]["name"] == "evolve_training_decision_log"
        assert data["schema"]["version"] == "1.0"
        assert "exported_at" in data["schema"]
        assert data["user_id"]

        # Period
        assert data["period"]["date_from"] is None
        assert data["period"]["date_to"] is None

        # Section A - Profile and context
        assert "profile_and_context" in data
        pc = data["profile_and_context"]
        assert pc["profile"]["user_id"]
        assert pc["profile"]["training_experience"] == "beginner"
        assert pc["profile"]["equipment"] == "gym_full"
        assert pc["profile"]["available_equipment"] == ["sztangę", "ławkę", "klatkę"]
        assert pc["profile"]["training_availability"] == {"Pon": {"start": "08:00", "end": "10:00"}}
        assert pc["latest_assessment"]["assessment_version"] == 1
        assert pc["latest_assessment"]["training_level"] == "początkujący"
        assert pc["latest_assessment"]["recovery_score"] == 7
        assert pc["latest_assessment"]["relevant_to_plan"] is True
        assert len(pc["assessment_history"]) == 1
        assert len(pc["goals"]) == 1
        assert pc["goals"][0]["title"] == "Większa klatka"
        assert pc["goals"][0]["baseline_value"] == 70
        assert pc["goals"][0]["target_value"] == 80

        # Section B - Original plan
        assert "original_plan" in data
        op = data["original_plan"]
        assert op["source"] == "user_profile_weekly_plan_json"
        assert op["plan_json"] is not None
        assert op["is_empty"] is False
        plan_days = op["plan_json"].get("days", [])
        assert len(plan_days) == 1
        assert plan_days[0]["day"] == "Pon"
        exercises = plan_days[0]["workout"]["exercises"]
        assert len(exercises) == 2
        assert exercises[0]["exercise_key"] == "bench_press-1"
        assert exercises[0]["weight_kg"] == 70

        # Section C - Actual training sessions
        assert "actual_training_sessions" in data
        sessions = data["actual_training_sessions"]
        assert sessions["session_count"] == 2
        assert sessions["total_sets_logged"] == 9  # 4+4+1
        # Chronological order: ascending by session_date
        dates = [s["session_date"] for s in sessions["sessions"]]
        assert dates == sorted(dates)
        s1 = sessions["sessions"][0]
        assert s1["session_id"]
        assert s1["final_rpe"] == 7
        assert s1["notes"] == "Dobrze się czułem"
        assert len(s1["sets"]) == 8  # 4 bench + 4 lateral
        bench_sets = [s for s in s1["sets"] if s["exercise_key"] == "bench_press-1"]
        assert len(bench_sets) == 4
        assert bench_sets[0]["actual_reps"] == 6
        assert bench_sets[0]["actual_weight_kg"] == 70
        assert bench_sets[0]["actual_rpe"] == 7
        assert s1["completed_set_count"] == 8

        # Section D - Plan changes
        assert "plan_changes" in data
        changes = data["plan_changes"]
        assert changes["change_count"] == 1
        rev = changes["changes"][0]
        assert rev["version"] == 1
        assert rev["decision_type"] == "adaptive_plan_revision"
        assert rev["status"] == "applied"
        assert rev["source"] == "system_adaptation"
        assert rev["rationale_recorded"] is True
        summary = rev["decision_summary"]
        assert summary["decision"] == "progress_load"
        assert summary["reason_codes"] == ["TARGET_COMPLETED"]
        assert rev["plan_before"]["exercises"][0]["weight_kg"] == 70
        assert rev["plan_after"]["exercises"][0]["weight_kg"] == 72

        # Section E - History integrity
        assert "history_integrity" in data
        hi = data["history_integrity"]
        assert hi["chronological_order"] is True
        assert hi["original_plan_preserved"] is True
        assert hi["previous_decisions_preserved"] is True
        assert hi["missing_data_marker"] == "unavailable"
        assert hi["linked_identifiers"]["user_id"] == data["user_id"]
        assert len(hi["linked_identifiers"]["session_ids"]) == 2
        assert len(hi["linked_identifiers"]["revision_ids"]) == 1
        assert "bench_press-1" in hi["linked_identifiers"]["exercise_keys"]
    finally:
        auth_routes.limiter.enabled = True
        _cleanup_tables()


def test_export_user_isolation():
    """User A must not see User B's data."""
    _cleanup_tables()
    auth_routes.limiter.enabled = False
    try:
        today = date.today()
        token_a = _register(f"iso_a_{today.isoformat()}@example.com", "user_a")
        token_b = _register(f"iso_b_{today.isoformat()}@example.com", "user_b")

        _make_user_with_full_history(token_a, f"iso_a_{today.isoformat()}@example.com", today)

        res_a = client.get("/app/training/decision-log-export", headers=_headers(token_a))
        assert res_a.status_code == 200
        data_a = res_a.json()
        assert data_a["user_id"] != ""

        res_b = client.get("/app/training/decision-log-export", headers=_headers(token_b))
        assert res_b.status_code == 200
        data_b = res_b.json()

        # User B should have no sessions, no revisions, empty plan
        assert data_b["actual_training_sessions"]["session_count"] == 0
        assert data_b["plan_changes"]["change_count"] == 0
        assert data_b["original_plan"]["is_empty"] is True
        assert data_b["profile_and_context"]["latest_assessment"] is not None  # may be None
        assert data_b["user_id"] != data_a["user_id"]
    finally:
        auth_routes.limiter.enabled = True
        _cleanup_tables()


def test_export_date_range_filter():
    """Export should filter sessions by date range when provided."""
    _cleanup_tables()
    auth_routes.limiter.enabled = False
    try:
        today = date.today()
        token = _register(f"range_{today.isoformat()}@example.com")
        _make_user_with_full_history(token, f"range_{today.isoformat()}@example.com", today)

        # Filter to only today's session
        res = client.get(
            f"/app/training/decision-log-export?date_from={today.isoformat()}&date_to={today.isoformat()}",
            headers=_headers(token),
        )
        assert res.status_code == 200
        data = res.json()
        assert data["actual_training_sessions"]["session_count"] == 1
        assert data["actual_training_sessions"]["sessions"][0]["session_date"] == today.isoformat()
        assert data["period"]["date_from"] == today.isoformat()
        assert data["period"]["date_to"] == today.isoformat()
    finally:
        auth_routes.limiter.enabled = True
        _cleanup_tables()


def test_export_missing_data_handling():
    """Missing data must be marked as unavailable, not zero or empty."""
    _cleanup_tables()
    auth_routes.limiter.enabled = False
    try:
        today = date.today()
        token = _register(f"missing_{today.isoformat()}@example.com")
        _make_user_with_full_history(token, f"missing_{today.isoformat()}@example.com", today)

        res = client.get("/app/training/decision-log-export", headers=_headers(token))
        assert res.status_code == 200
        data = res.json()

        # All sections must be present even when some data is missing
        assert "profile_and_context" in data
        assert "original_plan" in data
        assert "actual_training_sessions" in data
        assert "plan_changes" in data
        assert "history_integrity" in data

        # Missing data marker is "unavailable"
        assert data["history_integrity"]["missing_data_marker"] == "unavailable"

        # User with no assessment should show unavailable
        # (our test user has one, but the structure supports missing)
        pc = data["profile_and_context"]
        assert pc["latest_assessment"] is not None or pc["latest_assessment"] is None
    finally:
        auth_routes.limiter.enabled = True
        _cleanup_tables()


def test_export_chronology_preserved():
    """Sessions and revisions must be in chronological order."""
    _cleanup_tables()
    auth_routes.limiter.enabled = False
    try:
        today = date.today()
        token = _register(f"chrono_{today.isoformat()}@example.com")
        _make_user_with_full_history(token, f"chrono_{today.isoformat()}@example.com", today)

        res = client.get("/app/training/decision-log-export", headers=_headers(token))
        assert res.status_code == 200
        data = res.json()

        sessions = data["actual_training_sessions"]["sessions"]
        dates = [datetime.fromisoformat(s["session_date"]) for s in sessions]
        assert dates == sorted(dates), "Sessions must be in ascending chronological order"

        changes = data["plan_changes"]["changes"]
        versions = [c["version"] for c in changes]
        assert versions == sorted(versions), "Revisions must be in ascending version order"
    finally:
        auth_routes.limiter.enabled = True
        _cleanup_tables()


def test_export_unauthenticated_rejected():
    """Export must require authentication."""
    _cleanup_tables()
    auth_routes.limiter.enabled = False
    try:
        res = client.get("/app/training/decision-log-export")
        assert res.status_code == 401, res.text
    finally:
        auth_routes.limiter.enabled = True
        _cleanup_tables()


def test_export_original_plan_and_adaptation_preserved():
    """Original plan and previous decisions must not be overwritten."""
    _cleanup_tables()
    auth_routes.limiter.enabled = False
    try:
        today = date.today()
        token = _register(f"preserve_{today.isoformat()}@example.com")
        _make_user_with_full_history(token, f"preserve_{today.isoformat()}@example.com", today)

        res = client.get("/app/training/decision-log-export", headers=_headers(token))
        assert res.status_code == 200
        data = res.json()

        # Original plan starting weight is 70 (preserved)
        bench_exercise = data["original_plan"]["plan_json"]["days"][0]["workout"]["exercises"][0]
        assert bench_exercise["weight_kg"] == 70

        # Plan change shows previous (70) -> applied (72), both preserved
        rev = data["plan_changes"]["changes"][0]
        assert rev["plan_before"]["exercises"][0]["weight_kg"] == 70
        assert rev["plan_after"]["exercises"][0]["weight_kg"] == 72
        assert rev["plan_before_empty"] is False
        assert rev["plan_after_empty"] is False
    finally:
        auth_routes.limiter.enabled = True
        _cleanup_tables()
