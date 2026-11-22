"""
Unit and integration tests for Evolve progression engine and ExerciseProgressionDB.
"""

from __future__ import annotations

import json
from datetime import date
import pytest
from sqlmodel import Session, select

from app.models import ExerciseProgressionDB, TrainingSessionDB, TrainingSetResultDB, UserDB
from app.plan.progression_engine import (
    decide_next_step,
    estimate_starting_weight,
    get_rep_range_for_goal,
    get_weight_step,
    round_to_step,
)
from app.training.routes import _enrich_plan_with_progressions, _update_exercise_progressions


# ── 1. Unit tests: progression_engine pure functions ──────────────────────────


def test_round_to_step():
    assert round_to_step(21.3, 2.5) == 22.5
    assert round_to_step(21.2, 2.5) == 20.0
    assert round_to_step(11.0, 2.0) == 12.0
    assert round_to_step(0.0, 2.5) == 0.0
    assert round_to_step(-5.0, 2.5) == 0.0


def test_get_weight_step():
    assert get_weight_step(["barbell"]) == 2.5
    assert get_weight_step(["dumbbell"]) == 2.0
    assert get_weight_step(["hantle"]) == 2.0
    assert get_weight_step(["machine"]) == 2.5
    assert get_weight_step(["cable"]) == 2.5
    assert get_weight_step([]) == 2.5


def test_get_rep_range_for_goal():
    # Masa / hipertrofia
    rmin, rmax = get_rep_range_for_goal("Masa mięśniowa", "compound")
    assert (rmin, rmax) == (6, 12)
    rmin, rmax = get_rep_range_for_goal("Budowa beztłuszczowej masy mięśniowej", "isolation")
    assert (rmin, rmax) == (10, 20)

    # Siła
    rmin, rmax = get_rep_range_for_goal("Maksymalna siła i dynamika", "compound")
    assert (rmin, rmax) == (3, 6)
    rmin, rmax = get_rep_range_for_goal("siła", "isolation")
    assert (rmin, rmax) == (8, 12)

    # Redukcja
    rmin, rmax = get_rep_range_for_goal("Redukcja tkanki tłuszczowej", "compound")
    assert (rmin, rmax) == (8, 15)
    rmin, rmax = get_rep_range_for_goal("redukcja", "isolation")
    assert (rmin, rmax) == (12, 20)

    # Rekompozycja
    rmin, rmax = get_rep_range_for_goal("Rekompozycja sylwetki", "compound")
    assert (rmin, rmax) == (6, 10)

    # Default
    rmin, rmax = get_rep_range_for_goal(None, "compound")
    assert (rmin, rmax) == (6, 12)


def test_estimate_starting_weight():
    # 80 kg male, intermediate, bench press (horizontal_push)
    weight = estimate_starting_weight(
        user_weight_kg=80.0,
        exercise_type="compound",
        movement_pattern="horizontal_push",
        gender="mężczyzna",
        training_level="intermediate",
        equipment=["barbell"],
    )
    # 80 * 0.55 * 0.80 = ~35.2 -> rounded to 35.0 kg
    assert weight == 35.0

    # Bodyweight exercise should be 0.0 kg
    bw_weight = estimate_starting_weight(
        user_weight_kg=80.0,
        exercise_type="compound",
        movement_pattern="horizontal_push",
        gender="mężczyzna",
        training_level="intermediate",
        equipment=["bodyweight"],
    )
    assert bw_weight == 0.0

    # Core exercise should be 0.0 kg
    core_weight = estimate_starting_weight(
        user_weight_kg=80.0,
        exercise_type="compound",
        movement_pattern="core",
        gender="mężczyzna",
        training_level="intermediate",
        equipment=["bodyweight"],
    )
    assert core_weight == 0.0

    # Dumbbells should be scaled per hand
    db_weight = estimate_starting_weight(
        user_weight_kg=80.0,
        exercise_type="compound",
        movement_pattern="horizontal_push",
        gender="mężczyzna",
        training_level="intermediate",
        equipment=["dumbbell"],
    )
    assert 14.0 <= db_weight <= 18.0


def test_decide_next_step_progress_reps():
    # Within range (8-12), did 9 reps -> next target should be 10 reps, same weight
    res = decide_next_step(
        current_weight=50.0,
        current_reps=9,
        reps_min=8,
        reps_max=12,
        average_rpe=7.5,
        completion_pct=100.0,
        equipment=["barbell"],
    )
    assert res["action"] == "progress_reps"
    assert res["next_weight"] == 50.0
    assert res["next_reps"] == 10


def test_decide_next_step_progress_load():
    # Reached top of range (12 reps) at acceptable RPE -> increase load by 2.5 kg, reset reps to 8
    res = decide_next_step(
        current_weight=50.0,
        current_reps=12,
        reps_min=8,
        reps_max=12,
        average_rpe=8.0,
        completion_pct=100.0,
        equipment=["barbell"],
    )
    assert res["action"] == "progress_load"
    assert res["next_weight"] == 52.5
    assert res["next_reps"] == 8


def test_decide_next_step_reduce_on_low_completion():
    # Failed sets: completed only 50% of sets -> reduce load
    res = decide_next_step(
        current_weight=60.0,
        current_reps=6,
        reps_min=8,
        reps_max=12,
        average_rpe=9.0,
        completion_pct=50.0,
        equipment=["barbell"],
    )
    assert res["action"] == "reduce_load"
    assert res["next_weight"] < 60.0
    assert res["next_reps"] == 8


def test_decide_next_step_maintain_on_high_rpe():
    # High RPE (8.8) -> maintain weight
    res = decide_next_step(
        current_weight=50.0,
        current_reps=9,
        reps_min=8,
        reps_max=12,
        average_rpe=8.8,
        completion_pct=100.0,
        equipment=["barbell"],
    )
    assert res["action"] == "maintain"
    assert res["next_weight"] == 50.0


def test_decide_next_step_bodyweight():
    # Pure bodyweight exercise reached max reps (15) -> increment reps to 16
    res = decide_next_step(
        current_weight=0.0,
        current_reps=15,
        reps_min=10,
        reps_max=15,
        average_rpe=7.0,
        completion_pct=100.0,
        equipment=["bodyweight"],
    )
    assert res["action"] == "progress_reps"
    assert res["next_weight"] == 0.0
    assert res["next_reps"] == 16


# ── 2. Integration tests: Database & Session Progression Loop ─────────────────


def test_enrich_plan_and_session_progression_update():
    from sqlmodel import create_engine, SQLModel
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)

    with Session(test_engine) as session:
        # Setup test user
        user = UserDB(
            user_key="test:progression_user",
            name="Tester",
            weight=80.0,
            gender="mężczyzna",
            goal="Budowa beztłuszczowej masy mięśniowej",
            training_experience="intermediate",
            strength_training_experience="intermediate",
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        raw_exercises = [
            {
                "exercise_key": "barbell_bench_press",
                "exercise_name": "Wyciskanie sztangi leżąc",
                "sets": 3,
                "reps": 0,
                "weight_kg": 0.0,
            }
        ]

        # 1. Enrich plan before any progression state exists -> estimates starting weight
        enriched = _enrich_plan_with_progressions(raw_exercises, user.id, session, user)
        assert len(enriched) == 1
        assert enriched[0]["weight_kg"] == 35.0  # Estimated 35.0 kg for 80kg male bench press
        assert enriched[0]["reps"] == 6  # Minimum for masa mięśniowa (6-12)

        # 2. Simulate training session execution: user completes 3 sets of 12 reps at 40 kg with RPE 8
        training_session = TrainingSessionDB(
            user_id=user.id,
            session_date=date.today(),
            status="completed",
            planned_snapshot_json=json.dumps({"exercises": enriched}, ensure_ascii=False),
        )
        session.add(training_session)
        session.commit()
        session.refresh(training_session)

        completed_sets = [
            TrainingSetResultDB(
                session_id=training_session.id,
                user_id=user.id,
                exercise_key="barbell_bench_press",
                exercise_name="Wyciskanie sztangi leżąc",
                set_number=i + 1,
                actual_reps=12,
                actual_weight_kg=40.0,
                actual_rpe=8,
                completed=True,
            )
            for i in range(3)
        ]
        for s in completed_sets:
            session.add(s)
        session.commit()

        # 3. Trigger _update_exercise_progressions
        updates = _update_exercise_progressions(
            user_id=user.id,
            db_session=session,
            training_session=training_session,
            completed_sets=completed_sets,
            user=user,
        )
        session.commit()

        assert len(updates) == 1
        assert updates[0]["exercise_key"] == "barbell_bench_press"
        # Because user completed 12 reps (the max of range 6-12) at RPE 8:
        assert updates[0]["action"] == "progress_load"
        assert updates[0]["new_weight"] == 42.5  # 40 + 2.5 kg
        assert updates[0]["new_reps"] == 6  # Reset to bottom of rep range

        # 4. Verify record in ExerciseProgressionDB
        db_prog = session.exec(
            select(ExerciseProgressionDB)
            .where(ExerciseProgressionDB.user_id == user.id)
            .where(ExerciseProgressionDB.exercise_key == "barbell_bench_press")
        ).first()
        assert db_prog is not None
        assert db_prog.working_weight_kg == 42.5
        assert db_prog.current_reps == 6
        assert db_prog.calibrated is True

        # 5. Enriching next session should now reflect the new progressive weight 42.5 kg
        next_enriched = _enrich_plan_with_progressions(raw_exercises, user.id, session, user)
        assert next_enriched[0]["weight_kg"] == 42.5
        assert next_enriched[0]["reps"] == 6
