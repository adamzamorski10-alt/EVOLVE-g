"""
Unit and integration tests for Evolve progression engine and ExerciseProgressionDB.
"""

from __future__ import annotations

import json
from datetime import date
import pytest
from sqlmodel import Session, select

from app.models import AdaptivePlanRevisionDB, ExerciseProgressionDB, TrainingSessionDB, TrainingSetResultDB, UserDB
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


# ── 3. Minor (under 18) progression safety tests ──────────────────────────────


def test_decide_next_step_minor_target_rir_is_3():
    """Dla niepełnoletnich target_rir=3 → progi RPE bardziej konserwatywne (utrzymanie przy 7.5, redukcja przy 8.0)."""
    # Z target_rir=3: maintain_threshold = max(7.0, 10.0 - 3 + 0.5) = 7.5
    # reduce_threshold = max(8.0, 10.0 - 3 + 1.0) = 8.0
    res = decide_next_step(
        current_weight=40.0,
        current_reps=12,
        reps_min=6,
        reps_max=12,
        average_rpe=7.8,
        completion_pct=100.0,
        equipment=["barbell"],
        target_rir=3,  # minor
    )
    # RPE 7.8 >= maintain 7.5 → maintain, not progress_load
    assert res["action"] == "maintain", f"minor: expected maintain at RPE 7.8, got {res['action']}"
    assert res["next_weight"] == 40.0


def test_decide_next_step_adult_target_rir_is_2():
    """Dla pełnoletnich target_rir=2 → progi standardowe (utrzymanie przy 8.5, redukcja przy 9.5)."""
    res = decide_next_step(
        current_weight=40.0,
        current_reps=12,
        reps_min=6,
        reps_max=12,
        average_rpe=8.2,
        completion_pct=100.0,
        equipment=["barbell"],
        target_rir=2,  # adult default
    )
    # RPE 8.2 < maintain 8.5 → progress_load
    assert res["action"] == "progress_load", f"adult: expected progress_load at RPE 8.2, got {res['action']}"
    assert res["next_weight"] > 40.0


def test_minor_does_not_progress_load_when_rpe_at_maintain_threshold():
    """Niepełnoletni: przy RPE na poziomie maintain (7.5 dla target_rir=3) nie następuje progresja obciążenia."""
    res = decide_next_step(
        current_weight=20.0,
        current_reps=8,
        reps_min=6,
        reps_max=12,
        average_rpe=7.5,
        completion_pct=100.0,
        equipment=["dumbbell"],
        target_rir=3,
    )
    assert res["action"] == "maintain", f"minor at maintain threshold: expected maintain, got {res['action']}"
    assert res["next_weight"] == 20.0


def test_minor_respects_equipment_increment_and_load_cap():
    """Niepełnoletni: progresja szacuje krok wagowy i szanuje potwierdzone maksimum hantla."""
    res = decide_next_step(
        current_weight=10.0,
        current_reps=12,
        reps_min=8,
        reps_max=12,
        average_rpe=7.0,
        completion_pct=100.0,
        equipment=["dumbbell"],
        target_rir=3,
    )
    # Dumbbell step = 2.0 kg, max jump = max(2.0, 10.0 * 0.10) = 2.0 kg
    assert res["action"] == "progress_load"
    assert res["next_weight"] == 12.0  # 10 + 2.0 step


def test_update_exercise_progressions_minor_gets_target_rir_3():
    """_update_exercise_progressions tworzy rekord z target_rir=3 dla niepełnoletniego (wiek < 18)."""
    from sqlmodel import create_engine, SQLModel
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)

    with Session(test_engine) as session:
        user = UserDB(
            user_key="test:minor_user",
            name="Minor Tester",
            weight=60.0,
            gender="mężczyzna",
            goal="Budowa beztłuszczowej masy mięśniowej",
            training_experience="beginner",
            strength_training_experience="beginner",
            age=16,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        raw_exercises = [
            {
                "exercise_key": "dumbbell_bench_press",
                "exercise_name": "Wyciskanie hantli leżąc",
                "sets": 3,
                "reps": 0,
                "weight_kg": 0.0,
            }
        ]

        enriched = _enrich_plan_with_progressions(raw_exercises, user.id, session, user)
        assert len(enriched) == 1

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
                exercise_key="dumbbell_bench_press",
                exercise_name="Wyciskanie hantli leżąc",
                set_number=i + 1,
                actual_reps=10,
                actual_weight_kg=12.0,
                actual_rpe=7,
                completed=True,
            )
            for i in range(3)
        ]
        for s in completed_sets:
            session.add(s)
        session.commit()

        updates = _update_exercise_progressions(
            user_id=user.id,
            db_session=session,
            training_session=training_session,
            completed_sets=completed_sets,
            user=user,
        )
        session.commit()

        assert len(updates) == 1
        db_prog = session.exec(
            select(ExerciseProgressionDB)
            .where(ExerciseProgressionDB.user_id == user.id)
            .where(ExerciseProgressionDB.exercise_key == "dumbbell_bench_press")
        ).first()
        assert db_prog is not None
        assert db_prog.target_rir == 3, f"minor target_rir should be 3, got {db_prog.target_rir}"


def test_update_exercise_progressions_adult_keeps_target_rir_2():
    """_update_exercise_progressions tworzy rekord z target_rir=2 dla pełnoletniego."""
    from sqlmodel import create_engine, SQLModel
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)

    with Session(test_engine) as session:
        user = UserDB(
            user_key="test:adult_user",
            name="Adult Tester",
            weight=80.0,
            gender="mężczyzna",
            goal="Budowa beztłuszczowej masy mięśniowej",
            training_experience="intermediate",
            strength_training_experience="intermediate",
            age=28,
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

        enriched = _enrich_plan_with_progressions(raw_exercises, user.id, session, user)
        assert len(enriched) == 1

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

        updates = _update_exercise_progressions(
            user_id=user.id,
            db_session=session,
            training_session=training_session,
            completed_sets=completed_sets,
            user=user,
        )
        session.commit()

        assert len(updates) == 1
        db_prog = session.exec(
            select(ExerciseProgressionDB)
            .where(ExerciseProgressionDB.user_id == user.id)
            .where(ExerciseProgressionDB.exercise_key == "barbell_bench_press")
        ).first()
        assert db_prog is not None
        assert db_prog.target_rir == 2, f"adult target_rir should be 2, got {db_prog.target_rir}"


# ── 4. Existing-record target_rir alignment ────────────────────────────────


def test_existing_minor_record_target_rir_aligned_2_to_3():
    """Existing minor record with target_rir=2 is aligned to 3 on next update."""
    from sqlmodel import create_engine, SQLModel
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)

    with Session(test_engine) as session:
        user = UserDB(
            user_key="test:existing_minor",
            name="Existing Minor",
            weight=60.0,
            gender="mężczyzna",
            goal="Budowa beztłuszczowej masy mięśniowej",
            training_experience="beginner",
            strength_training_experience="beginner",
            age=16,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        # Pre-existing record created under the old (adult) default target_rir=2.
        prog = ExerciseProgressionDB(
            user_id=user.id,
            exercise_key="dumbbell_bench_press",
            exercise_name="Wyciskanie hantli leżąc",
            working_weight_kg=12.0,
            current_reps=8,
            target_reps_min=6,
            target_reps_max=12,
            target_rir=2,
            calibrated=False,
        )
        session.add(prog)
        session.commit()

        training_session = TrainingSessionDB(
            user_id=user.id,
            session_date=date.today(),
            status="completed",
            planned_snapshot_json=json.dumps(
                {"exercises": [{"exercise_key": "dumbbell_bench_press", "exercise_name": "Wyciskanie hantli leżąc", "sets": 3}]},
                ensure_ascii=False,
            ),
        )
        session.add(training_session)
        session.commit()
        session.refresh(training_session)

        completed_sets = [
            TrainingSetResultDB(
                session_id=training_session.id,
                user_id=user.id,
                exercise_key="dumbbell_bench_press",
                exercise_name="Wyciskanie hantli leżąc",
                set_number=i + 1,
                actual_reps=10,
                actual_weight_kg=12.0,
                actual_rpe=7,
                completed=True,
            )
            for i in range(3)
        ]
        for s in completed_sets:
            session.add(s)
        session.commit()

        updates = _update_exercise_progressions(
            user_id=user.id,
            db_session=session,
            training_session=training_session,
            completed_sets=completed_sets,
            user=user,
        )
        session.commit()

        assert len(updates) == 1
        db_prog = session.exec(
            select(ExerciseProgressionDB)
            .where(ExerciseProgressionDB.user_id == user.id)
            .where(ExerciseProgressionDB.exercise_key == "dumbbell_bench_press")
        ).first()
        assert db_prog is not None
        assert db_prog.target_rir == 3, f"existing minor target_rir should align to 3, got {db_prog.target_rir}"


def test_existing_adult_record_target_rir_stays_2():
    """Existing adult record keeps target_rir=2 (no spurious change to 3)."""
    from sqlmodel import create_engine, SQLModel
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)

    with Session(test_engine) as session:
        user = UserDB(
            user_key="test:existing_adult",
            name="Existing Adult",
            weight=80.0,
            gender="mężczyzna",
            goal="Budowa beztłuszczowej masy mięśniowej",
            training_experience="intermediate",
            strength_training_experience="intermediate",
            age=28,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        prog = ExerciseProgressionDB(
            user_id=user.id,
            exercise_key="barbell_bench_press",
            exercise_name="Wyciskanie sztangi leżąc",
            working_weight_kg=40.0,
            current_reps=8,
            target_reps_min=6,
            target_reps_max=12,
            target_rir=3,
            calibrated=False,
        )
        session.add(prog)
        session.commit()

        training_session = TrainingSessionDB(
            user_id=user.id,
            session_date=date.today(),
            status="completed",
            planned_snapshot_json=json.dumps(
                {"exercises": [{"exercise_key": "barbell_bench_press", "exercise_name": "Wyciskanie sztangi leżąc", "sets": 3}]},
                ensure_ascii=False,
            ),
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

        updates = _update_exercise_progressions(
            user_id=user.id,
            db_session=session,
            training_session=training_session,
            completed_sets=completed_sets,
            user=user,
        )
        session.commit()

        assert len(updates) == 1
        db_prog = session.exec(
            select(ExerciseProgressionDB)
            .where(ExerciseProgressionDB.user_id == user.id)
            .where(ExerciseProgressionDB.exercise_key == "barbell_bench_press")
        ).first()
        assert db_prog is not None
        assert db_prog.target_rir == 2, f"existing adult target_rir should stay 2, got {db_prog.target_rir}"


def test_existing_record_missing_age_keeps_target_rir():
    """Brak wieku nie obniża istniejącego target_rir (bezpieczny domyślny = zachowanie poprzednie)."""
    from sqlmodel import create_engine, SQLModel
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)

    with Session(test_engine) as session:
        user = UserDB(
            user_key="test:no_age",
            name="No Age",
            weight=70.0,
            gender="mężczyzna",
            goal="Budowa beztłuszczowej masy mięśniowej",
            training_experience="beginner",
            strength_training_experience="beginner",
            age=None,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        prog = ExerciseProgressionDB(
            user_id=user.id,
            exercise_key="dumbbell_bench_press",
            exercise_name="Wyciskanie hantli leżąc",
            working_weight_kg=12.0,
            current_reps=8,
            target_reps_min=6,
            target_reps_max=12,
            target_rir=3,
            calibrated=False,
        )
        session.add(prog)
        session.commit()

        training_session = TrainingSessionDB(
            user_id=user.id,
            session_date=date.today(),
            status="completed",
            planned_snapshot_json=json.dumps(
                {"exercises": [{"exercise_key": "dumbbell_bench_press", "exercise_name": "Wyciskanie hantli leżąc", "sets": 3}]},
                ensure_ascii=False,
            ),
        )
        session.add(training_session)
        session.commit()
        session.refresh(training_session)

        completed_sets = [
            TrainingSetResultDB(
                session_id=training_session.id,
                user_id=user.id,
                exercise_key="dumbbell_bench_press",
                exercise_name="Wyciskanie hantli leżąc",
                set_number=i + 1,
                actual_reps=10,
                actual_weight_kg=12.0,
                actual_rpe=7,
                completed=True,
            )
            for i in range(3)
        ]
        for s in completed_sets:
            session.add(s)
        session.commit()

        updates = _update_exercise_progressions(
            user_id=user.id,
            db_session=session,
            training_session=training_session,
            completed_sets=completed_sets,
            user=user,
        )
        session.commit()

        assert len(updates) == 1
        db_prog = session.exec(
            select(ExerciseProgressionDB)
            .where(ExerciseProgressionDB.user_id == user.id)
            .where(ExerciseProgressionDB.exercise_key == "dumbbell_bench_press")
        ).first()
        assert db_prog is not None
        assert db_prog.target_rir == 3, f"missing age must not downgrade target_rir, got {db_prog.target_rir}"


# ── 5. Minor RPE boundary unit tests ───────────────────────────────────────


def test_decide_next_step_minor_rpe_8_0_reduce_load():
    """target_rir=3: RPE dokładnie 8.0 → reduce_load (próg redukcji 8.0)."""
    res = decide_next_step(
        current_weight=40.0,
        current_reps=12,
        reps_min=6,
        reps_max=12,
        average_rpe=8.0,
        completion_pct=100.0,
        equipment=["barbell"],
        target_rir=3,
    )
    assert res["action"] == "reduce_load", f"minor RPE 8.0 expected reduce_load, got {res['action']}"


def test_decide_next_step_minor_rpe_7_4_progress_load():
    """target_rir=3: RPE 7.4 (< maintain 7.5) → progress_load gdy reps w górę zakresu."""
    res = decide_next_step(
        current_weight=40.0,
        current_reps=12,
        reps_min=6,
        reps_max=12,
        average_rpe=7.4,
        completion_pct=100.0,
        equipment=["barbell"],
        target_rir=3,
    )
    assert res["action"] == "progress_load", f"minor RPE 7.4 expected progress_load, got {res['action']}"
    assert res["next_weight"] > 40.0


# ── 6. Load feasibility: starting-load safety ──────────────────────────────


def test_estimate_starting_weight_respects_confirmed_dumbbell_capacity():
    """Potwierdzona pojemność hantla nigdy nie jest przekraczana (per hand)."""
    weight = estimate_starting_weight(
        user_weight_kg=80.0,
        exercise_type="compound",
        movement_pattern="horizontal_push",
        gender="mężczyzna",
        training_level="intermediate",
        equipment=["dumbbell"],
        dumbbell_max_kg_per_dumbbell=10.0,
        dumbbell_increment_kg=2.0,
    )
    assert weight <= 10.0, f"dumbbell load {weight} exceeds confirmed 10 kg per hand"


def test_estimate_starting_weight_per_hand_semantics():
    """Obciążenie hantli wyrażone jest na jeden hantel (~45% oburęcznej sztangi)."""
    barbell = estimate_starting_weight(
        user_weight_kg=80.0,
        exercise_type="compound",
        movement_pattern="horizontal_push",
        gender="mężczyzna",
        training_level="intermediate",
        equipment=["barbell"],
        dumbbell_max_kg_per_dumbbell=None,
        dumbbell_increment_kg=None,
    )
    dumbbell = estimate_starting_weight(
        user_weight_kg=80.0,
        exercise_type="compound",
        movement_pattern="horizontal_push",
        gender="mężczyzna",
        training_level="intermediate",
        equipment=["dumbbell"],
        dumbbell_max_kg_per_dumbbell=None,
        dumbbell_increment_kg=None,
    )
    assert dumbbell > 0
    assert abs(dumbbell - barbell * 0.45) < 3.0, f"per-hand {dumbbell} not ~45% of barbell {barbell}"


def test_estimate_starting_weight_unknown_capacity_returns_estimate_but_caller_masks_it():
    """estimate_starting_weight sama zwraca liczbę; brak pojemności → nieweryfikowana."""
    # Sam silnik szacunkowy zwraca liczbę (zachowanie wsteczne dla testów jednostkowych).
    weight = estimate_starting_weight(
        user_weight_kg=80.0,
        exercise_type="compound",
        movement_pattern="horizontal_push",
        gender="mężczyzna",
        training_level="beginner",
        equipment=["dumbbell"],
        dumbbell_max_kg_per_dumbbell=None,
        dumbbell_increment_kg=None,
    )
    assert isinstance(weight, float) and weight >= 0.0


def test_enrich_unknown_dumbbell_capacity_produces_instruction_not_load():
    """Brak pojemności hantli → weight_kg=0.0 (brak None) i instrukcja doboru obciążenia."""
    from sqlmodel import create_engine, SQLModel
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)

    with Session(test_engine) as session:
        user = UserDB(
            user_key="test:no_dumbbell_cap",
            name="No Dumbbell Cap",
            weight=80.0,
            gender="mężczyzna",
            goal="Budowa beztłuszczowej masy mięśniowej",
            training_experience="beginner",
            strength_training_experience="beginner",
            age=28,
            dumbbell_max_kg_per_dumbbell=None,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        raw_exercises = [
            {
                "exercise_key": "dumbbell_bench_press",
                "exercise_name": "Wyciskanie hantli leżąc",
                "sets": 3,
                "reps": 0,
                "weight_kg": 0.0,
            }
        ]

        enriched = _enrich_plan_with_progressions(raw_exercises, user.id, session, user)
        assert len(enriched) == 1
        assert enriched[0]["weight_kg"] == 0.0, f"expected 0.0, got {enriched[0]['weight_kg']}"
        assert "weight_instruction" in enriched[0]
        assert "hantle" in enriched[0]["weight_instruction"]


def test_enrich_confirmed_dumbbell_capacity_respected():
    """Pojemność hantli znana → przepisany ciężar nie przekracza maksimum per hand."""
    from sqlmodel import create_engine, SQLModel
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)

    with Session(test_engine) as session:
        user = UserDB(
            user_key="test:dumbbell_cap",
            name="Dumbbell Cap",
            weight=80.0,
            gender="mężczyzna",
            goal="Budowa beztłuszczowej masy mięśniowej",
            training_experience="beginner",
            strength_training_experience="beginner",
            age=28,
            dumbbell_max_kg_per_dumbbell=12.0,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        raw_exercises = [
            {
                "exercise_key": "dumbbell_bench_press",
                "exercise_name": "Wyciskanie hantli leżąc",
                "sets": 3,
                "reps": 0,
                "weight_kg": 0.0,
            }
        ]

        enriched = _enrich_plan_with_progressions(raw_exercises, user.id, session, user)
        assert len(enriched) == 1
        assert enriched[0]["weight_kg"] is not None
        assert enriched[0]["weight_kg"] <= 12.0, f"{enriched[0]['weight_kg']} exceeds 12 kg per hand"


def test_enrich_bodyweight_exercise_unaffected():
    """Ćwiczenia własnym ciałem otrzymują weight_kg=0.0, nie instrukcję obciążenia."""
    from sqlmodel import create_engine, SQLModel
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)

    with Session(test_engine) as session:
        user = UserDB(
            user_key="test:bodyweight",
            name="Bodyweight",
            weight=80.0,
            gender="mężczyzna",
            goal="Budowa beztłuszczowej masy mięśniowej",
            training_experience="beginner",
            strength_training_experience="beginner",
            age=28,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        raw_exercises = [
            {
                "exercise_key": "standing_calf_raise",
                "exercise_name": "Wspięcia na palce stojąc",
                "sets": 4,
                "reps": 0,
                "weight_kg": 0.0,
            }
        ]

        enriched = _enrich_plan_with_progressions(raw_exercises, user.id, session, user)
        assert len(enriched) == 1
        assert enriched[0]["weight_kg"] == 0.0
        assert "weight_instruction" not in enriched[0]


# ── 7. Starting-load safety: increment assumption & beginner conservatism ─


def test_estimate_starting_weight_unknown_increment_does_not_assume_equipment_step():
    """Nieznany skok użytkownika nie zaokrągla ani do domyślnego kroku sprzętu.
    Zwracany jest szacunek surowej wartości (np. 11.88 kg), nie 12.0 kg."""
    weight_no_increment = estimate_starting_weight(
        user_weight_kg=80.0,
        exercise_type="compound",
        movement_pattern="horizontal_push",
        gender="mężczyzna",
        training_level="beginner",
        equipment=["dumbbell"],
        dumbbell_max_kg_per_dumbbell=20.0,
        dumbbell_increment_kg=None,
    )
    weight_with_increment = estimate_starting_weight(
        user_weight_kg=80.0,
        exercise_type="compound",
        movement_pattern="horizontal_push",
        gender="mężczyzna",
        training_level="beginner",
        equipment=["dumbbell"],
        dumbbell_max_kg_per_dumbbell=20.0,
        dumbbell_increment_kg=2.0,
    )
    # Nieznany skok: surowy szacunek 11.88 kg, nie zaokrąglony do 12.0 (kroku sprzętu 2.0 kg).
    assert abs(weight_no_increment - 11.88) < 0.001
    assert round_to_step(weight_no_increment, 2.0) != weight_no_increment  # nie wielokrotność 2.0
    # Znany skok 2.0 kg zaokrągla do 12.0.
    assert abs(weight_with_increment - 12.0) < 0.001
    assert weight_no_increment <= 20.0
    assert weight_with_increment <= 20.0


def test_estimate_starting_weight_known_increment_rounded_to_it():
    """Znany skok wagowy jest respektowany (zaokrąglenie do tego skoku)."""
    weight = estimate_starting_weight(
        user_weight_kg=80.0,
        exercise_type="compound",
        movement_pattern="horizontal_push",
        gender="mężczyzna",
        training_level="beginner",
        equipment=["dumbbell"],
        dumbbell_max_kg_per_dumbbell=20.0,
        dumbbell_increment_kg=2.0,
    )
    # Zaokrąglenie do skoku 2.0 kg → wynik musi być wielokrotnością 2.0 (po capie).
    assert weight == round(weight / 2.0) * 2.0 or weight == 20.0


def test_estimate_starting_weight_unknown_increment_still_caps_at_confirmed_max():
    """Nieznany skok nie zwalnia z sztywnego sufitu potwierdzonej pojemności hantla."""
    weight = estimate_starting_weight(
        user_weight_kg=120.0,
        exercise_type="compound",
        movement_pattern="horizontal_push",
        gender="mężczyzna",
        training_level="advanced",
        equipment=["dumbbell"],
        dumbbell_max_kg_per_dumbbell=12.0,
        dumbbell_increment_kg=None,
    )
    assert weight <= 12.0, f"{weight} przekracza potwierdzone 12 kg per hand"


def test_beginner_minor_starting_load_conservative_vs_confirmed_max():
    """Początkujący (w tym niepełnoletni) zaczyna znacznie poniżej potwierdzonego maksimum per hand."""
    weight = estimate_starting_weight(
        user_weight_kg=60.0,
        exercise_type="compound",
        movement_pattern="horizontal_push",
        gender="mężczyzna",
        training_level="beginner",
        equipment=["dumbbell"],
        dumbbell_max_kg_per_dumbbell=20.0,
        dumbbell_increment_kg=None,
    )
    ratio = weight / 20.0
    assert ratio <= 0.55, f"początkujący zaczyna przy {ratio:.0%} potwierdzonego maksimum — za wysoko"
    assert weight > 0.0


# ── 8. Calibration precedence: _enrich_plan_with_progressions ───────────────

def _make_d2_user(session, user_key: str, age: int = 28, weight: float = 80.0,
                  dumbbell_max: float | None = None) -> UserDB:
    user = UserDB(
        user_key=user_key,
        name="D2 Tester",
        weight=weight,
        gender="mężczyzna",
        goal="Budowa beztłuszczowej masy mięśniowej",
        training_experience="intermediate",
        strength_training_experience="intermediate",
        age=age,
        dumbbell_max_kg_per_dumbbell=dumbbell_max,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _make_prog(session, user_id: str, exercise_key: str = "barbell_bench_press",
               working_weight_kg: float = 0.0, current_reps: int = 0,
               calibrated: bool = False, target_rir: int = 2) -> ExerciseProgressionDB:
    prog = ExerciseProgressionDB(
        user_id=user_id,
        exercise_key=exercise_key,
        exercise_name=exercise_key,
        working_weight_kg=working_weight_kg,
        current_reps=current_reps,
        target_reps_min=6,
        target_reps_max=12,
        target_rir=target_rir,
        calibrated=calibrated,
    )
    session.add(prog)
    session.commit()
    return prog


def _make_completed_session(session, user_id: str, exercise_key: str,
                            sets_payload: list[dict]) -> TrainingSessionDB:
    import json
    from datetime import date
    ts = TrainingSessionDB(
        user_id=user_id,
        session_date=date.today(),
        status="completed",
        planned_snapshot_json=json.dumps(
            {"exercises": [{"exercise_key": exercise_key, "exercise_name": exercise_key, "sets": 3}]},
            ensure_ascii=False,
        ),
    )
    session.add(ts)
    session.commit()
    session.refresh(ts)
    completed = [
        TrainingSetResultDB(
            session_id=ts.id,
            user_id=user_id,
            exercise_key=exercise_key,
            exercise_name=exercise_key,
            set_number=i + 1,
            actual_reps=s.get("actual_reps", 0),
            actual_weight_kg=s.get("actual_weight_kg", 0.0),
            actual_rpe=s.get("actual_rpe"),
            completed=True,
        )
        for i, s in enumerate(sets_payload)
    ]
    for s in completed:
        session.add(s)
    session.commit()
    return ts


def test_calibrated_progression_overrides_v2_prescription():
    """Kalibrowany rekord progresji nadpisuje receptę V2 (ciężar i powtórzenia)."""
    from sqlmodel import create_engine, SQLModel
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        user = _make_d2_user(session, "test:cal_overrides_v2")
        _make_prog(session, user.id, working_weight_kg=25.0, current_reps=8, calibrated=True)

        raw = [{"exercise_key": "barbell_bench_press", "exercise_name": "barbell_bench_press",
                "sets": 3, "reps": 6, "weight_kg": 35.0}]
        enriched = _enrich_plan_with_progressions(raw, user.id, session, user)
        assert len(enriched) == 1
        assert enriched[0]["weight_kg"] == 25.0, f"expected calibrated 25.0, got {enriched[0]['weight_kg']}"
        assert enriched[0]["reps"] == 8, f"expected calibrated reps 8, got {enriched[0]['reps']}"


def test_uncalibrated_record_does_not_override_valid_v2_weight():
    """Nieskalibrowany rekord nie nadpisuje ważnej wagi V2."""
    from sqlmodel import create_engine, SQLModel
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        user = _make_d2_user(session, "test:uncal_no_override_weight")
        _make_prog(session, user.id, working_weight_kg=50.0, current_reps=10, calibrated=False)

        raw = [{"exercise_key": "barbell_bench_press", "exercise_name": "barbell_bench_press",
                "sets": 3, "reps": 8, "weight_kg": 35.0}]
        enriched = _enrich_plan_with_progressions(raw, user.id, session, user)
        assert len(enriched) == 1
        assert enriched[0]["weight_kg"] == 35.0, f"V2 weight should be kept, got {enriched[0]['weight_kg']}"


def test_uncalibrated_record_does_not_override_valid_v2_reps():
    """Nieskalibrowany rekord nie nadpisuje ważnych powtórzeń V2."""
    from sqlmodel import create_engine, SQLModel
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        user = _make_d2_user(session, "test:uncal_no_override_reps")
        _make_prog(session, user.id, working_weight_kg=50.0, current_reps=10, calibrated=False)

        raw = [{"exercise_key": "barbell_bench_press", "exercise_name": "barbell_bench_press",
                "sets": 3, "reps": 8, "weight_kg": 0.0}]
        enriched = _enrich_plan_with_progressions(raw, user.id, session, user)
        assert len(enriched) == 1
        # weight: V2 has no valid weight (0.0) → uncalibrated fallback applies
        assert enriched[0]["weight_kg"] == 50.0
        # reps: V2 has valid reps (8) → uncalibrated must NOT overwrite
        assert enriched[0]["reps"] == 8, f"V2 reps should be kept, got {enriched[0]['reps']}"


def test_uncalibrated_record_fallback_when_v2_has_no_weight():
    """Nieskalibrowany szacunek używany jako fallback gdy V2 nie ma ważnej wagi."""
    from sqlmodel import create_engine, SQLModel
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        user = _make_d2_user(session, "test:uncal_fallback")
        _make_prog(session, user.id, working_weight_kg=20.0, current_reps=8, calibrated=False)

        raw = [{"exercise_key": "barbell_bench_press", "exercise_name": "barbell_bench_press",
                "sets": 3, "reps": 0, "weight_kg": 0.0}]
        enriched = _enrich_plan_with_progressions(raw, user.id, session, user)
        assert len(enriched) == 1
        assert enriched[0]["weight_kg"] == 20.0, f"expected uncalibrated fallback 20.0, got {enriched[0]['weight_kg']}"


def test_session_without_meaningful_data_does_not_calibrate():
    """Sesja bez znaczących danych (reps=0, weight=0) nie kalibruje rekordu."""
    from sqlmodel import create_engine, SQLModel
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        user = _make_d2_user(session, "test:no_calibrate")
        _make_prog(session, user.id, working_weight_kg=0.0, current_reps=0, calibrated=False)

        ts = _make_completed_session(session, user.id, "barbell_bench_press", [
            {"actual_reps": 0, "actual_weight_kg": 0.0},
            {"actual_reps": 0, "actual_weight_kg": 0.0},
            {"actual_reps": 0, "actual_weight_kg": 0.0},
        ])

        _update_exercise_progressions(
            user_id=user.id, db_session=session, training_session=ts,
            completed_sets=[], user=user,
        )
        session.commit()

        db_prog = session.exec(
            select(ExerciseProgressionDB)
            .where(ExerciseProgressionDB.user_id == user.id)
            .where(ExerciseProgressionDB.exercise_key == "barbell_bench_press")
        ).first()
        assert db_prog is not None
        assert db_prog.calibrated is False, f"should not calibrate without meaningful data, got {db_prog.calibrated}"


def test_valid_completed_performance_calibrates_record():
    """Poprawne dane z ukończonej serii kalibrują rekord."""
    from sqlmodel import create_engine, SQLModel
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        user = _make_d2_user(session, "test:calibrate_valid")
        _make_prog(session, user.id, working_weight_kg=0.0, current_reps=0, calibrated=False)

        ts = _make_completed_session(session, user.id, "barbell_bench_press", [
            {"actual_reps": 10, "actual_weight_kg": 30.0, "actual_rpe": 7},
            {"actual_reps": 10, "actual_weight_kg": 30.0, "actual_rpe": 7},
            {"actual_reps": 10, "actual_weight_kg": 30.0, "actual_rpe": 7},
        ])

        # Re-load completed sets from DB for the update call
        sets = list(
            session.exec(
                select(TrainingSetResultDB)
                .where(TrainingSetResultDB.session_id == ts.id)
                .where(TrainingSetResultDB.user_id == user.id)
            ).all()
        )

        _update_exercise_progressions(
            user_id=user.id, db_session=session, training_session=ts,
            completed_sets=sets, user=user,
        )
        session.commit()

        db_prog = session.exec(
            select(ExerciseProgressionDB)
            .where(ExerciseProgressionDB.user_id == user.id)
            .where(ExerciseProgressionDB.exercise_key == "barbell_bench_press")
        ).first()
        assert db_prog is not None
        assert db_prog.calibrated is True, f"should calibrate with meaningful data, got {db_prog.calibrated}"


def test_calibrated_bodyweight_record_overrides_reps_not_weight():
    """Kalibrowany rekord własnym ciałem nadpisuje powtórzenia, a nie wagę (0.0)."""
    from sqlmodel import create_engine, SQLModel
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        user = _make_d2_user(session, "test:bw_cal")
        _make_prog(session, user.id, exercise_key="standing_calf_raise",
                   working_weight_kg=0.0, current_reps=15, calibrated=True)

        raw = [{"exercise_key": "standing_calf_raise", "exercise_name": "standing_calf_raise",
                "sets": 4, "reps": 10, "weight_kg": 0.0}]
        enriched = _enrich_plan_with_progressions(raw, user.id, session, user)
        assert len(enriched) == 1
        assert enriched[0]["weight_kg"] == 0.0, f"bodyweight weight stays 0.0, got {enriched[0]['weight_kg']}"
        assert enriched[0]["reps"] == 15, f"bodyweight reps overridden to 15, got {enriched[0]['reps']}"


def test_active_adaptive_revision_takes_precedence_over_progression():
    """Aktywna rewizja adaptacyjna blokuje nadpisanie przez rekord progresji."""
    from sqlmodel import create_engine, SQLModel
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        user = _make_d2_user(session, "test:adaptive_prec")
        _make_prog(session, user.id, working_weight_kg=99.0, current_reps=5, calibrated=True)

        rev = AdaptivePlanRevisionDB(
            user_id=user.id,
            source_session_ids_json="[]",
            previous_plan_json="{}",
            applied_plan_json="{}",
            decision_summary_json="{}",
            version=1,
        )
        session.add(rev)
        session.commit()

        raw = [{"exercise_key": "barbell_bench_press", "exercise_name": "barbell_bench_press",
                "sets": 3, "reps": 8, "weight_kg": 35.0}]
        enriched = _enrich_plan_with_progressions(raw, user.id, session, user)
        assert len(enriched) == 1
        # Adaptacyjna ma pierwszeństwo → progresja nie nadpisuje V2
        assert enriched[0]["weight_kg"] == 35.0, f"adaptive precedence: V2 weight kept, got {enriched[0]['weight_kg']}"
        assert enriched[0]["reps"] == 8, f"adaptive precedence: V2 reps kept, got {enriched[0]['reps']}"


# ── 9. Calibration classification: exercise loading models ────────────────────

def _calibration_for(key: str, sets_payload: list[dict], user_key: str) -> bool:
    """Uruchom pełny cykl aktualizacji progresji i zwróć wynikową kalibrację."""
    from sqlmodel import create_engine, SQLModel
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        user = _make_d2_user(session, user_key)
        _make_prog(session, user.id, exercise_key=key, working_weight_kg=0.0, current_reps=0, calibrated=False)
        ts = _make_completed_session(session, user.id, key, sets_payload)
        sets = list(
            session.exec(
                select(TrainingSetResultDB)
                .where(TrainingSetResultDB.session_id == ts.id)
                .where(TrainingSetResultDB.user_id == user.id)
            ).all()
        )
        _update_exercise_progressions(
            user_id=user.id, db_session=session, training_session=ts,
            completed_sets=sets, user=user,
        )
        session.commit()
        db_prog = session.exec(
            select(ExerciseProgressionDB)
            .where(ExerciseProgressionDB.user_id == user.id)
            .where(ExerciseProgressionDB.exercise_key == key)
        ).first()
        assert db_prog is not None
        return db_prog.calibrated, db_prog.working_weight_kg


def test_pullups_and_dips_calibrate_on_reps_only():
    """Podciąganie i dipy (sprzęt bez mierzalnych kg) kalibrują się na powtórzeniach."""
    for key in ("pullup_wide", "dips"):
        calibrated, weight = _calibration_for(
            key, [{"actual_reps": 8, "actual_weight_kg": 0.0}, {"actual_reps": 8, "actual_weight_kg": 0.0}],
            f"test:bw_{key}",
        )
        assert calibrated is True, f"{key} powinien kalibrować się na powtórzeniach"
        assert weight == 0.0, f"{key} nie powinien tworzyć progresji obciążenia (waga 0.0)"


def test_bands_calibrate_on_reps_only():
    """Gumy oporowe (brak liczbowego kg) kalibrują się na powtórzeniach."""
    calibrated, weight = _calibration_for(
        "band_row", [{"actual_reps": 12, "actual_weight_kg": 0.0}, {"actual_reps": 12, "actual_weight_kg": 0.0}],
        "test:bands_row",
    )
    assert calibrated is True, "band_row powinien kalibrować się na powtórzeniach"
    assert weight == 0.0, "gumy nie tworzą progresji kg"


def test_hanging_leg_raise_core_calibrates_on_reps_only():
    """Ćwiczenie core (wisące unoszenie nóg) kalibruje się na powtórzeniach."""
    calibrated, weight = _calibration_for(
        "hanging_leg_raise", [{"actual_reps": 10, "actual_weight_kg": 0.0}, {"actual_reps": 10, "actual_weight_kg": 0.0}],
        "test:core_raise",
    )
    assert calibrated is True, "core ćwiczenie powinno kalibrować się na powtórzeniach"
    assert weight == 0.0


def test_weighted_variation_requires_external_load():
    """Wariacja obciążona (weight_plate) NIE kalibruje się bez obciążenia kg."""
    calibrated, weight = _calibration_for(
        "weighted_wide_pushups",
        [{"actual_reps": 12, "actual_weight_kg": 0.0}, {"actual_reps": 12, "actual_weight_kg": 0.0}],
        "test:weighted_pushups",
    )
    assert calibrated is False, "obciążona wariacja bez kg nie powinna kalibrować"
    assert weight == 0.0


def test_loaded_exercise_requires_meaningful_weight():
    """Ładowane ćwiczenie (sztanga/maszyna/kabel) bez obciążenia kg nie kalibruje."""
    for key in ("barbell_bench_press", "leg_press", "lat_pulldown"):
        calibrated, weight = _calibration_for(
            key,
            [{"actual_reps": 10, "actual_weight_kg": 0.0}, {"actual_reps": 10, "actual_weight_kg": 0.0}],
            f"test:loaded_{key}",
        )
        assert calibrated is False, f"{key} bez obciążenia kg nie powinien kalibrować"
        assert weight == 0.0


def test_invalid_session_does_not_calibrate_new_record():
    """Pusta/nieprawidłowa sesja nie kalibruje nowego rekordu (gumy, bez powtórzeń)."""
    from sqlmodel import create_engine, SQLModel
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        user = _make_d2_user(session, "test:no_cal_bands")
        _make_prog(session, user.id, exercise_key="band_row", working_weight_kg=0.0, current_reps=0, calibrated=False)
        ts = _make_completed_session(session, user.id, "band_row", [
            {"actual_reps": 0, "actual_weight_kg": 0.0},
            {"actual_reps": 0, "actual_weight_kg": 0.0},
        ])
        sets = list(
            session.exec(
                select(TrainingSetResultDB)
                .where(TrainingSetResultDB.session_id == ts.id)
                .where(TrainingSetResultDB.user_id == user.id)
            ).all()
        )
        _update_exercise_progressions(
            user_id=user.id, db_session=session, training_session=ts,
            completed_sets=sets, user=user,
        )
        session.commit()
        db_prog = session.exec(
            select(ExerciseProgressionDB)
            .where(ExerciseProgressionDB.user_id == user.id)
            .where(ExerciseProgressionDB.exercise_key == "band_row")
        ).first()
        assert db_prog.calibrated is False, "nieprawidłowa sesja nie kalibruje nowego rekordu"


def test_calibrated_record_stays_calibrated_after_invalid_session():
    """Już skalibrowany rekord nie traci kalibracji po późniejszej nieprawidłowej sesji."""
    from sqlmodel import create_engine, SQLModel
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        user = _make_d2_user(session, "test:cal_persist")
        # Pierwsza sesja z poprawnymi danymi kalibruje rekord (sztanga).
        _make_prog(session, user.id, working_weight_kg=30.0, current_reps=10, calibrated=False)
        ts = _make_completed_session(session, user.id, "barbell_bench_press", [
            {"actual_reps": 10, "actual_weight_kg": 30.0, "actual_rpe": 7},
            {"actual_reps": 10, "actual_weight_kg": 30.0, "actual_rpe": 7},
            {"actual_reps": 10, "actual_weight_kg": 30.0, "actual_rpe": 7},
        ])
        sets = list(
            session.exec(
                select(TrainingSetResultDB)
                .where(TrainingSetResultDB.session_id == ts.id)
                .where(TrainingSetResultDB.user_id == user.id)
            ).all()
        )
        _update_exercise_progressions(
            user_id=user.id, db_session=session, training_session=ts,
            completed_sets=sets, user=user,
        )
        session.commit()
        db_prog = session.exec(
            select(ExerciseProgressionDB)
            .where(ExerciseProgressionDB.user_id == user.id)
            .where(ExerciseProgressionDB.exercise_key == "barbell_bench_press")
        ).first()
        assert db_prog.calibrated is True
        # Późniejsza sesja bez ważnych danych nie może cofnąć kalibracji.
        ts2 = _make_completed_session(session, user.id, "barbell_bench_press", [
            {"actual_reps": 0, "actual_weight_kg": 0.0},
            {"actual_reps": 0, "actual_weight_kg": 0.0},
        ])
        sets2 = list(
            session.exec(
                select(TrainingSetResultDB)
                .where(TrainingSetResultDB.session_id == ts2.id)
                .where(TrainingSetResultDB.user_id == user.id)
            ).all()
        )
        _update_exercise_progressions(
            user_id=user.id, db_session=session, training_session=ts2,
            completed_sets=sets2, user=user,
        )
        session.commit()
        db_prog = session.exec(
            select(ExerciseProgressionDB)
            .where(ExerciseProgressionDB.user_id == user.id)
            .where(ExerciseProgressionDB.exercise_key == "barbell_bench_press")
        ).first()
        assert db_prog.calibrated is True, "skalibrowany rekord nie może stać się nieskalibrowany"


# ── 10. Unknown dumbbell capacity through the real enrichment flow ────────────

def _enrich_session() -> Session:
    from sqlmodel import create_engine, SQLModel
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_unknown_dumbbell_capacity_enrich_returns_zero_and_instruction():
    """Nieznana pojemność hantli: brak None, brak zweryfikowanej recepty, instrukcja obecna."""
    session = _enrich_session()
    user = UserDB(
        user_key="test:dumbbell_unknown",
        name="Tester", weight=80.0, gender="mężczyzna",
        training_experience="intermediate", strength_training_experience="intermediate",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    raw = [{"exercise_key": "dumbbell_bench_press", "exercise_name": "dumbbell_bench_press",
            "sets": 3, "reps": "8-12", "weight_kg": 0.0}]
    enriched = _enrich_plan_with_progressions(raw, user.id, session, user)
    assert len(enriched) == 1
    assert enriched[0]["weight_kg"] == 0.0
    assert enriched[0].get("weight_instruction"), "oczekiwana instrukcja doboru obciążenia"
    # Wynik musi być serializowalny do JSON (brak None → brak TypeError).
    import json
    json.dumps(enriched[0])


def test_known_dumbbell_capacity_and_increment_enrich():
    """Znana pojemność i przyrost: ograniczony, zaokrąglony ciężar, brak None."""
    session = _enrich_session()
    user = UserDB(
        user_key="test:dumbbell_known",
        name="Tester", weight=80.0, gender="mężczyzna",
        training_experience="intermediate", strength_training_experience="intermediate",
        dumbbell_max_kg_per_dumbbell=10.0, dumbbell_increment_kg=2.5,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    raw = [{"exercise_key": "dumbbell_bench_press", "exercise_name": "dumbbell_bench_press",
            "sets": 3, "reps": "8-12", "weight_kg": 0.0}]
    enriched = _enrich_plan_with_progressions(raw, user.id, session, user)
    assert len(enriched) == 1
    w = enriched[0]["weight_kg"]
    assert w > 0.0, "oczekiwano konkretnego ciężaru gdy pojemność znana"
    assert w <= 10.0, f"ciężar nie może przekraczać potwierdzonego maksimum: {w}"
    assert abs(w / 2.5 - round(w / 2.5)) < 1e-9, f"nie jest wielokrotnością 2.5: {w}"
    assert "weight_instruction" not in enriched[0] or not enriched[0].get("weight_instruction")
    import json
    json.dumps(enriched[0])


# ── 11. weight_kg = 0.0 sentinel safety ──────────────────────────────────────

def test_zero_weight_sentinel_does_not_calibrate_loaded_exercise():
    """0.0 (brak obciążenia) dla ćwiczenia obciążonego nie kalibruje — wymagany actual_weight_kg > 0."""
    from sqlmodel import create_engine, SQLModel
    test_engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        user = _make_d2_user(session, "test:zero_sentinel_loaded")
        _make_prog(session, user.id, exercise_key="barbell_bench_press",
                   working_weight_kg=0.0, current_reps=0, calibrated=False)
        ts = _make_completed_session(session, user.id, "barbell_bench_press", [
            {"actual_reps": 10, "actual_weight_kg": 0.0},   # reps OK, brak obciążenia kg
            {"actual_reps": 10, "actual_weight_kg": 0.0},
            {"actual_reps": 10, "actual_weight_kg": 0.0},
        ])
        sets = list(
            session.exec(
                select(TrainingSetResultDB)
                .where(TrainingSetResultDB.session_id == ts.id)
                .where(TrainingSetResultDB.user_id == user.id)
            ).all()
        )
        _update_exercise_progressions(
            user_id=user.id, db_session=session, training_session=ts,
            completed_sets=sets, user=user,
        )
        session.commit()
        db_prog = session.exec(
            select(ExerciseProgressionDB)
            .where(ExerciseProgressionDB.user_id == user.id)
            .where(ExerciseProgressionDB.exercise_key == "barbell_bench_press")
        ).first()
        assert db_prog.calibrated is False, "0.0 kg nie kalibruje ćwiczenia obciążonego"


def test_zero_weight_sentinel_does_not_clobber_calibrated_weight():
    """0.0 sentinel nie nadpisuje już skalibrowanego working_weight_kg > 0."""
    session = _enrich_session()
    user = UserDB(
        user_key="test:zero_sentinel_cal",
        name="Tester", weight=80.0, gender="mężczyzna",
        training_experience="intermediate", strength_training_experience="intermediate",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    # Ustaw ręcznie skalibrowany rekord z working_weight_kg > 0.
    prog = ExerciseProgressionDB(
        user_id=user.id, exercise_key="dumbbell_bench_press",
        exercise_name="dumbbell_bench_press", working_weight_kg=12.0,
        current_reps=8, target_reps_min=6, target_reps_max=12,
        target_rir=2, calibrated=True,
    )
    session.add(prog)
    session.commit()
    session.refresh(user)
    # V2 daje 0.0 (brak pojemności hantli) — skalibrowany 12.0 musi wygrać.
    raw = [{"exercise_key": "dumbbell_bench_press", "exercise_name": "dumbbell_bench_press",
            "sets": 3, "reps": "8-12", "weight_kg": 0.0}]
    user.dumbbell_max_kg_per_dumbbell = None  # wymusza ścieżkę 0.0 + instrukcja
    enriched = _enrich_plan_with_progressions(raw, user.id, session, user)
    assert len(enriched) == 1
    assert enriched[0]["weight_kg"] == 12.0, (
        f"skalibrowany ciężar 12.0 musi zachować się nad 0.0 sentinela, got {enriched[0]['weight_kg']}"
    )


# ── 12. Complete end-to-end backend flow: plan → session → completion → next workout ────

def _full_flow(
    exercise_key: str,
    sets_payload: list[dict],
    user_key: str,
    dumbbell_max: float | None = None,
    dumbbell_increment: float | None = None,
    age: int | None = 28,
) -> dict:
    """Pełny cykl backend: enrich → completed session → progression update → re-enrich.
    Zwraca dict z wagami przed i po oraz flagą kalibracji."""
    from sqlmodel import create_engine, SQLModel
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        user = UserDB(
            user_key=user_key, name="Flow Tester", weight=80.0, gender="mężczyzna",
            training_experience="intermediate", strength_training_experience="intermediate",
            age=age,
            dumbbell_max_kg_per_dumbbell=dumbbell_max,
            dumbbell_increment_kg=dumbbell_increment,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        # 1. Plan → enrichment (pierwszy trening, brak rekordu progresji)
        raw = [{"exercise_key": exercise_key, "exercise_name": exercise_key,
                "sets": 3, "reps": "8-12", "weight_kg": 0.0}]
        enriched_before = _enrich_plan_with_progressions(raw, user.id, session, user)
        weight_before = enriched_before[0]["weight_kg"]

        # 2. Ukończona sesja z wynikami
        ts = _make_completed_session(session, user.id, exercise_key, sets_payload)
        sets = list(
            session.exec(
                select(TrainingSetResultDB)
                .where(TrainingSetResultDB.session_id == ts.id)
                .where(TrainingSetResultDB.user_id == user.id)
            ).all()
        )
        _update_exercise_progressions(
            user_id=user.id, db_session=session, training_session=ts,
            completed_sets=sets, user=user,
        )
        session.commit()

        db_prog = session.exec(
            select(ExerciseProgressionDB)
            .where(ExerciseProgressionDB.user_id == user.id)
            .where(ExerciseProgressionDB.exercise_key == exercise_key)
        ).first()
        assert db_prog is not None

        # 3. Następny trening → re-enrichment (uwzględnia kalibrację i progresję)
        enriched_after = _enrich_plan_with_progressions(raw, user.id, session, user)
        weight_after = enriched_after[0]["weight_kg"]

        return {
            "weight_before": weight_before,
            "weight_after": weight_after,
            "calibrated": db_prog.calibrated,
            "working_weight_kg": db_prog.working_weight_kg,
            "current_reps": db_prog.current_reps,
            "target_rir": db_prog.target_rir,
        }


def test_e2e_loaded_exercise_full_flow_calibrates_and_carries_forward():
    """Sztanga: enrichment → sesja z obciążeniem → kalibracja → kolejny trening używa wagi kalibracji."""
    result = _full_flow(
        "barbell_bench_press",
        [{"actual_reps": 10, "actual_weight_kg": 30.0, "actual_rpe": 7},
         {"actual_reps": 10, "actual_weight_kg": 30.0, "actual_rpe": 7},
         {"actual_reps": 10, "actual_weight_kg": 30.0, "actual_rpe": 7}],
        "test:flow_barbell",
    )
    assert result["calibrated"] is True, "ćwiczenie obciążone powinno się kalibrować"
    assert result["weight_after"] == result["working_weight_kg"], (
        "kolejny trening powinien użyć wagi z kalibracji"
    )
    assert result["weight_after"] > 0.0


def test_e2e_bodyweight_pullups_full_flow_calibrates_on_reps():
    """Podciąganie (pullup_bar, brak kg): enrichment → sesja reps-only → kalibracja → kolejny trening."""
    result = _full_flow(
        "pullup_wide",
        [{"actual_reps": 8, "actual_weight_kg": 0.0}, {"actual_reps": 8, "actual_weight_kg": 0.0}],
        "test:flow_pullups",
    )
    assert result["calibrated"] is True, "podciąganie bez kg powinno się kalibrować na reps"
    assert result["working_weight_kg"] == 0.0, "podciąganie nie tworzy progresji kg"
    assert result["weight_after"] == 0.0


def test_e2e_bands_full_flow_calibrates_on_reps():
    """Gumy (bands, brak kg): enrichment → sesja reps-only → kalibracja → kolejny trening."""
    result = _full_flow(
        "band_row",
        [{"actual_reps": 12, "actual_weight_kg": 0.0}, {"actual_reps": 12, "actual_weight_kg": 0.0}],
        "test:flow_bands",
    )
    assert result["calibrated"] is True, "gumy bez kg powinny się kalibrować na reps"
    assert result["working_weight_kg"] == 0.0


def test_e2e_invalid_session_no_calibration_no_progression():
    """Nieprawidłowa sesja (brak powtórzeń i obciążenia) nie kalibruje ani nie tworzy progresji obciążenia."""
    result = _full_flow(
        "barbell_bench_press",
        [{"actual_reps": 0, "actual_weight_kg": 0.0}, {"actual_reps": 0, "actual_weight_kg": 0.0}],
        "test:flow_invalid",
    )
    assert result["calibrated"] is False, "nieprawidłowa sesja nie kalibruje"


def test_e2e_known_dumbbell_capacity_full_flow_respects_cap_and_increment():
    """Hantle z pojemnością i przyrostem: ograniczony, zaokrąglony ciężar, kalibracja po sesji."""
    result = _full_flow(
        "dumbbell_bench_press",
        [{"actual_reps": 10, "actual_weight_kg": 8.0, "actual_rpe": 7},
         {"actual_reps": 10, "actual_weight_kg": 8.0, "actual_rpe": 7}],
        "test:flow_dumbbell",
        dumbbell_max=10.0,
        dumbbell_increment=2.5,
    )
    assert result["weight_before"] > 0.0, "oczekiwano konkretnego ciężaru"
    assert result["weight_before"] <= 10.0, f"nie przekracza pojemności: {result['weight_before']}"
    assert abs(result["weight_before"] / 2.5 - round(result["weight_before"] / 2.5)) < 1e-9, (
        f"wielokrotność 2.5 kg: {result['weight_before']}"
    )
    assert result["calibrated"] is True


def test_e2e_minor_user_gets_submaximal_rir():
    """Użytkownik niepełnoletni (wiek < 18) otrzymuje target_rir=3 (submaksymalny wysiłek)."""
    result = _full_flow(
        "barbell_bench_press",
        [{"actual_reps": 10, "actual_weight_kg": 30.0}],
        "test:flow_minor",
        age=16,
    )
    assert result["target_rir"] == 3, f"niepełnoletni powinien mieć target_rir=3, ma {result['target_rir']}"


def test_e2e_adult_user_gets_standard_rir():
    """Użytkownik dorosły (wiek >= 18) otrzymuje target_rir=2."""
    result = _full_flow(
        "barbell_bench_press",
        [{"actual_reps": 10, "actual_weight_kg": 30.0}],
        "test:flow_adult",
        age=28,
    )
    assert result["target_rir"] == 2, f"dorosły powinien mieć target_rir=2, ma {result['target_rir']}"
