"""
Regression tests for Stage B1: Dumbbell Load Capability and Prescription Safety.

Covers the STORED -> READ -> USED -> CHANGES BEHAVIOR -> TESTED chain:
- dumbbell capability persisted on UserDB / exposed via profile
- estimate_starting_weight caps per-dumbbell load at confirmed max
- available load increments are respected
- unknown capacity yields a conservative estimate, never a falsely precise verified load
- per-dumbbell convention (weight per single dumbbell, not per pair)
- existing users without capability data remain compatible
- persisted profile values affect the real enrichment path (_enrich_plan_with_progressions)
"""

from __future__ import annotations

from sqlmodel import Session, create_engine, SQLModel

from app.models import UserDB
from app.plan.progression_engine import estimate_starting_weight
from app.training.routes import _enrich_plan_with_progressions


def _make_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def _make_user(
    session: Session,
    *,
    dumbbell_type: str | None = None,
    dumbbell_max_kg_per_dumbbell: float | None = None,
    dumbbell_increment_kg: float | None = None,
    weight: float = 80.0,
) -> UserDB:
    user = UserDB(
        user_key="test:dumbbell_user",
        name="Tester",
        weight=weight,
        gender="mężczyzna",
        training_experience="intermediate",
        dumbbell_type=dumbbell_type,
        dumbbell_max_kg_per_dumbbell=dumbbell_max_kg_per_dumbbell,
        dumbbell_increment_kg=dumbbell_increment_kg,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _enrich(session: Session, user: UserDB, exercises: list[dict]) -> list[dict]:
    return _enrich_plan_with_progressions(exercises, user.id, session, user)


def _dumbbell_exercise(key: str) -> dict:
    return {"exercise_key": key, "name": key, "sets": 3, "reps": "8-12"}


# ── 1. Unit: estimate_starting_weight with dumbbell capability ──────────────


def test_estimate_starting_weight_dumbbell_below_max_unchanged():
    # 80 kg male intermediate, horizontal_push compound: 80*0.55*0.8*1.0*0.45 = 15.84 -> 16.0 kg
    weight = estimate_starting_weight(
        user_weight_kg=80.0,
        exercise_type="compound",
        movement_pattern="horizontal_push",
        gender="mężczyzna",
        training_level="intermediate",
        equipment=["dumbbell", "bench"],
        dumbbell_max_kg_per_dumbbell=20.0,
    )
    assert weight == 16.0


def test_estimate_starting_weight_dumbbell_above_max_capped():
    # Estimate 16.0 kg but confirmed max is 10 kg per dumbbell -> capped at 10.0
    weight = estimate_starting_weight(
        user_weight_kg=80.0,
        exercise_type="compound",
        movement_pattern="horizontal_push",
        gender="mężczyzna",
        training_level="intermediate",
        equipment=["dumbbell", "bench"],
        dumbbell_max_kg_per_dumbbell=10.0,
    )
    assert weight == 10.0


def test_estimate_starting_weight_dumbbell_increment_respected():
    # Increment 2.5 kg: 15.84 -> round to 15.0 (nearest 2.5), not 16.0
    weight = estimate_starting_weight(
        user_weight_kg=80.0,
        exercise_type="compound",
        movement_pattern="horizontal_push",
        gender="mężczyzna",
        training_level="intermediate",
        equipment=["dumbbell", "bench"],
        dumbbell_max_kg_per_dumbbell=20.0,
        dumbbell_increment_kg=2.5,
    )
    assert weight == 15.0


def test_estimate_starting_weight_dumbbell_increment_rounds_up_then_caps():
    # Estimate 15.84, increment 2.5 -> rounds to 15.0, but max 14.0 caps it back to 14.0.
    # Rounding to an increment must never push the prescription over the confirmed max.
    weight = estimate_starting_weight(
        user_weight_kg=80.0,
        exercise_type="compound",
        movement_pattern="horizontal_push",
        gender="mężczyzna",
        training_level="intermediate",
        equipment=["dumbbell", "bench"],
        dumbbell_max_kg_per_dumbbell=14.0,
        dumbbell_increment_kg=2.5,
    )
    assert weight == 14.0


def test_estimate_starting_weight_dumbbell_unknown_capacity_no_cap():
    # No max/increment: conservative bodyweight estimate, no equipment-imposed ceiling
    weight = estimate_starting_weight(
        user_weight_kg=80.0,
        exercise_type="compound",
        movement_pattern="horizontal_push",
        gender="mężczyzna",
        training_level="intermediate",
        equipment=["dumbbell", "bench"],
    )
    assert weight == 16.0
    assert weight > 0.0


def test_estimate_starting_weight_per_dumbbell_not_pair():
    # The returned value is per single dumbbell (~16 kg each), not the pair total (~32 kg).
    weight = estimate_starting_weight(
        user_weight_kg=80.0,
        exercise_type="compound",
        movement_pattern="horizontal_push",
        gender="mężczyzna",
        training_level="intermediate",
        equipment=["dumbbell", "bench"],
        dumbbell_max_kg_per_dumbbell=20.0,
    )
    assert weight == 16.0
    assert weight < 32.0  # not the pair total


def test_estimate_starting_weight_barbell_unaffected_by_dumbbell_params():
    # Barbell bench press: dumbbell max/increment must not influence non-dumbbell lifts.
    weight = estimate_starting_weight(
        user_weight_kg=80.0,
        exercise_type="compound",
        movement_pattern="horizontal_push",
        gender="mężczyzna",
        training_level="intermediate",
        equipment=["barbell", "bench"],
        dumbbell_max_kg_per_dumbbell=10.0,  # irrelevant for barbell
        dumbbell_increment_kg=2.5,          # irrelevant for barbell
    )
    assert weight == 35.0


def test_estimate_starting_weight_beginner_dumbbell_capped():
    # Beginner (0.60 multiplier): 80*0.55*0.60*1.0*0.45 = 11.88 -> 12.0 kg; max 8 kg caps it.
    weight = estimate_starting_weight(
        user_weight_kg=80.0,
        exercise_type="compound",
        movement_pattern="horizontal_push",
        gender="mężczyzna",
        training_level="beginner",
        equipment=["dumbbell", "bench"],
        dumbbell_max_kg_per_dumbbell=8.0,
    )
    assert weight == 8.0


# ── 2. Integration: real enrichment path (_enrich_plan_with_progressions) ──


def test_enrich_caps_dumbbell_at_user_max():
    session = _make_session()
    user = _make_user(session, dumbbell_max_kg_per_dumbbell=10.0)
    exercises = [_dumbbell_exercise("dumbbell_bench_press")]
    enriched = _enrich(session, user, exercises)
    assert len(enriched) == 1
    assert enriched[0]["weight_kg"] <= 10.0, f"exceeded per-dumbbell max: {enriched[0]['weight_kg']}"
    assert enriched[0]["weight_kg"] > 0.0


def test_enrich_respects_increment():
    session = _make_session()
    user = _make_user(session, dumbbell_max_kg_per_dumbbell=20.0, dumbbell_increment_kg=2.5)
    exercises = [_dumbbell_exercise("dumbbell_bench_press")]
    enriched = _enrich(session, user, exercises)
    weight = enriched[0]["weight_kg"]
    assert abs(weight / 2.5 - round(weight / 2.5)) < 1e-9, f"not a multiple of 2.5: {weight}"
    assert weight <= 20.0


def test_enrich_unknown_capacity_conservative_estimate():
    session = _make_session()
    user = _make_user(session)  # all dumbbell fields None -> unknown capacity
    exercises = [_dumbbell_exercise("dumbbell_bench_press")]
    enriched = _enrich(session, user, exercises)
    weight = enriched[0]["weight_kg"]
    # A concrete starting weight is still provided (usable plan), but it is an
    # estimate derived from bodyweight, not a verified prescription against a max.
    assert weight > 0.0
    assert weight == 16.0  # bodyweight-based, no equipment cap applied


def test_enrich_existing_user_missing_capability_compatible():
    # Existing users have dumbbell_* columns as None; enrichment must not crash.
    session = _make_session()
    user = _make_user(session)  # defaults: all None
    exercises = [
        _dumbbell_exercise("dumbbell_bench_press"),
        _dumbbell_exercise("goblet_squat"),
    ]
    enriched = _enrich(session, user, exercises)
    assert len(enriched) == 2
    for item in enriched:
        assert "weight_kg" in item
        assert item["weight_kg"] >= 0.0


def test_enrich_barbell_not_capped_by_dumbbell_max():
    session = _make_session()
    user = _make_user(session, dumbbell_max_kg_per_dumbbell=10.0)  # low dumbbell max
    exercises = [
        {"exercise_key": "barbell_bench_press", "name": "barbell_bench_press", "sets": 3, "reps": "6-8"}
    ]
    enriched = _enrich(session, user, exercises)
    assert enriched[0]["weight_kg"] == 35.0  # barbell estimate, dumbbell max ignored


def test_enrich_dumbbell_below_max_unchanged():
    session = _make_session()
    user = _make_user(session, dumbbell_max_kg_per_dumbbell=20.0)
    exercises = [_dumbbell_exercise("dumbbell_bench_press")]
    enriched = _enrich(session, user, exercises)
    # 16.0 kg estimate is below the 20 kg max, so it stays 16.0.
    assert enriched[0]["weight_kg"] == 16.0
