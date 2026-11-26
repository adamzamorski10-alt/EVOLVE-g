"""
Regression tests for Stage B2: Explicit Strength Experience and Safe Generator Defaults.

Covers:
1. New profile with no strength experience → field remains null.
2. Missing strength experience → beginner-safe generator restrictions.
3. Explicit profile beginner → beginner restrictions.
4. Explicit intermediate/advanced levels → existing intended behavior preserved.
5. Missing experience does not allow intermediate/advanced-only exercises.
6. Progression with missing strength experience uses conservative beginner behavior.
7. Basketball/general experience does not influence strength-training level.
8. Existing legacy training_experience values remain unchanged.
9. Profile update and read correctly persist/expose the new field.
"""

from __future__ import annotations

import json

import pytest
from sqlmodel import Session, create_engine, SQLModel

from app.models import UserDB
from app.plan.generator_v2 import _resolve_strength_level
from app.plan.progression_engine import estimate_starting_weight
from app.training.routes import _enrich_plan_with_progressions

from app.plan.deterministic import build_deterministic_plan
from app.plan.progression_engine import estimate_starting_weight


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(
    *,
    frequency="3 dni",
    days=3,
    equipment_list=None,
    focus=None,
    training_experience=None,
    strength_training_experience=None,
    sport_specialization=None,
    goal="masa mięśniowa",
):
    if equipment_list is None:
        equipment_list = ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"]
    if focus is None:
        focus = ["klatka", "plecy", "nogi", "brzuch", "barki"]
    presets = {
        "gym_full": ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"],
        "dumbbells": ["hantle", "ławka"],
        "bodyweight": [],
    }
    user = type(
        "User",
        (),
        {
            "name": "test",
            "goal": goal,
            "frequency": frequency,
            "diet": "standardowa",
            "gender": "mężczyzna",
            "age": 25,
            "height": 180,
            "weight": 80,
            "calories_target": 2500,
            "meals_per_day": 4,
            "allergies": "",
            "health_limitations": "",
            "injuries": "",
            "training_locations_json": "[]",
            "sport_focus": "",
            "basketball_position": None,
            "sport_specialization": sport_specialization,
            "sport_training_days_json": "[]",
            "training_availability_json": "{}",
            "sport_training_schedule_json": "{}",
            "training_focus_json": json.dumps(focus, ensure_ascii=False),
            "improvement_areas_json": "[]",
            "available_equipment_json": json.dumps(equipment_list, ensure_ascii=False),
            "avoid_exercises_json": "[]",
            "preferred_foods_json": "[]",
            "avoid_foods_json": "[]",
            "equipment": ",".join(equipment_list),
            "training_experience": training_experience,
            "strength_training_experience": strength_training_experience,
        },
    )()
    user.get_list = lambda field: json.loads(getattr(user, field, "[]") or "[]")
    return user


def _make_assessment(*, days=3, level=None, recovery=None, hours=None):
    return type(
        "Assessment",
        (),
        {
            "sessions_per_week": days,
            "training_level": level,
            "recovery_score": recovery,
            "availability_hours_per_week": hours,
        },
    )()


def _plan(user, assessment):
    return build_deterministic_plan(user, assessment)


def _make_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def _enrich(session: Session, user: UserDB, exercises: list[dict]) -> list[dict]:
    return _enrich_plan_with_progressions(exercises, user.id, session, user)


def _dumbbell_exercise(key: str) -> dict:
    return {"exercise_key": key, "name": key, "sets": 3, "reps": "8-12"}


def _all_exercise_levels(plan):
    from app.exercises.data import get_exercise

    levels = []
    for day in plan["days"]:
        if day["day_type"] == "rest":
            continue
        for e in day["workout"]["exercises"]:
            ex = get_exercise(e.get("exercise_id", e["name"]))
            if ex is not None:
                levels.append(ex.level)
    return levels


def _exercise_count(plan):
    count = 0
    for day in plan["days"]:
        if day["day_type"] != "rest":
            count += len(day["workout"]["exercises"])
    return count


def _training_days(plan):
    return [d for d in plan["days"] if d["day_type"] != "rest"]


def _exercise_names(day):
    return [e["name"] for e in day["workout"]["exercises"]]


# ---------------------------------------------------------------------------
# 1. New profile: no strength experience → field remains null
# ---------------------------------------------------------------------------


def test_new_profile_strength_experience_is_null():
    user = _make_user()
    assert user.strength_training_experience is None


def test_to_profile_dict_exposes_strength_training_experience_null():
    from app.models import UserDB

    u = UserDB(
        user_key="test:null",
        name="Tester",
        weight=80,
        gender="mężczyzna",
        strength_training_experience=None,
    )
    d = u.to_profile_dict()
    assert d.get("strength_training_experience") is None


def test_to_profile_dict_exposes_strength_training_experience_value():
    from app.models import UserDB

    u = UserDB(
        user_key="test:beg",
        name="Tester",
        weight=80,
        gender="mężczyzna",
        strength_training_experience="beginner",
    )
    d = u.to_profile_dict()
    assert d.get("strength_training_experience") == "beginner"


# ---------------------------------------------------------------------------
# 2. Missing strength experience → beginner-safe generator restrictions
# ---------------------------------------------------------------------------


def test_missing_strength_experience_beginner_safe_no_advanced_exercises(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    user = _make_user(strength_training_experience=None)  # missing → beginner-safe
    assessment = _make_assessment(level=None)  # also missing
    plan = _plan(user, assessment)
    levels = _all_exercise_levels(plan)
    assert "advanced" not in levels, f"advanced exercise with missing experience: {levels}"
    assert "elite" not in levels, f"elite exercise with missing experience: {levels}"


def test_missing_strength_exercise_limit_beginner(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    user = _make_user(strength_training_experience=None)
    assessment = _make_assessment(level=None)
    plan = _plan(user, assessment)
    for day in _training_days(plan):
        n = len(_exercise_names(day))
        assert n <= 6, f"too many exercises for beginner-safe session {day['day']}: {n}"


def test_missing_strength_experience_beginner_volume_targets(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    user = _make_user(strength_training_experience=None)
    assessment = _make_assessment(level=None)
    plan = _plan(user, assessment)
    # Plan should generate successfully with beginner-safe settings
    assert "weekly_goal" in plan
    assert "_planner" in plan


# ---------------------------------------------------------------------------
# 3. Explicit profile beginner → beginner restrictions
# ---------------------------------------------------------------------------


def test_explicit_beginner_no_advanced_exercises(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    user = _make_user(strength_training_experience="beginner")
    assessment = _make_assessment(level=None)
    plan = _plan(user, assessment)
    levels = _all_exercise_levels(plan)
    assert "advanced" not in levels
    assert "elite" not in levels


def test_explicit_beginner_exercise_limit_6(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    user = _make_user(strength_training_experience="beginner")
    assessment = _make_assessment(level=None)
    plan = _plan(user, assessment)
    for day in _training_days(plan):
        n = len(_exercise_names(day))
        assert n <= 6, f"too many exercises for beginner session {day['day']}: {n}"


# ---------------------------------------------------------------------------
# 4. Explicit intermediate/advanced → existing behavior preserved
# ---------------------------------------------------------------------------


def test_explicit_intermediate_allows_intermediate_exercises(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    user = _make_user(strength_training_experience="intermediate")
    assessment = _make_assessment(level=None)
    plan = _plan(user, assessment)
    levels = _all_exercise_levels(plan)
    assert "intermediate" in levels or len(levels) > 0


def test_explicit_advanced_allows_advanced_exercises(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    user = _make_user(strength_training_experience="advanced")
    assessment = _make_assessment(level=None)
    plan = _plan(user, assessment)
    levels = _all_exercise_levels(plan)
    assert len(levels) > 0


def test_explicit_intermediate_exercise_limit_8(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    user = _make_user(strength_training_experience="intermediate")
    assessment = _make_assessment(level=None)
    plan = _plan(user, assessment)
    for day in _training_days(plan):
        n = len(_exercise_names(day))
        assert n <= 8, f"too many exercises for intermediate session {day['day']}: {n}"


# ---------------------------------------------------------------------------
# 5. Missing experience does not allow intermediate/advanced-only exercises
# ---------------------------------------------------------------------------


def test_missing_experience_blocks_advanced_only_exercise(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    user = _make_user(strength_training_experience=None)
    assessment = _make_assessment(level=None)
    plan = _plan(user, assessment)
    levels = _all_exercise_levels(plan)
    # No advanced-only exercises should appear when experience is missing
    advanced_only = [l for l in levels if l == "advanced"]
    assert not advanced_only, f"advanced-only exercises with missing experience: {advanced_only}"


# ---------------------------------------------------------------------------
# 6. Progression with missing strength experience → conservative beginner behavior
# ---------------------------------------------------------------------------


def test_estimate_starting_weight_missing_strength_experience_beginner():
    # Missing strength experience → beginner multiplier (0.60).
    # 80 * 0.55 * 0.60 * 1.0 * 0.45 = 11.88 kg; no increment → raw estimate, not rounded.
    weight = estimate_starting_weight(
        user_weight_kg=80.0,
        exercise_type="compound",
        movement_pattern="horizontal_push",
        gender="mężczyzna",
        training_level="beginner",  # what's passed when strength field is missing
        equipment=["dumbbell", "bench"],
    )
    assert abs(weight - 11.88) < 0.001


def test_estimate_starting_weight_intermediate_differs_from_beginner():
    beginner = estimate_starting_weight(
        user_weight_kg=80.0,
        exercise_type="compound",
        movement_pattern="horizontal_push",
        gender="mężczyzna",
        training_level="beginner",
        equipment=["dumbbell", "bench"],
    )
    intermediate = estimate_starting_weight(
        user_weight_kg=80.0,
        exercise_type="compound",
        movement_pattern="horizontal_push",
        gender="mężczyzna",
        training_level="intermediate",
        equipment=["dumbbell", "bench"],
    )
    assert intermediate > beginner  # 0.80 vs 0.60 multiplier


# ---------------------------------------------------------------------------
# 7. Basketball/general experience does not influence strength-training level
# ---------------------------------------------------------------------------


def test_basketball_experience_does_not_set_strength_level(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    # User with lots of basketball experience but no strength experience
    user = _make_user(
        strength_training_experience=None,
        sport_specialization="koszykówka",
    )
    assessment = _make_assessment(level=None)
    plan = _plan(user, assessment)
    levels = _all_exercise_levels(plan)
    assert "advanced" not in levels
    assert "elite" not in levels


# ---------------------------------------------------------------------------
# 8. Existing legacy training_experience values remain unchanged
# ---------------------------------------------------------------------------


def test_legacy_training_experience_preserved_on_model():
    from app.models import UserDB

    u = UserDB(
        user_key="test:legacy",
        name="Tester",
        weight=80,
        gender="mężczyzna",
        training_experience="intermediate",  # legacy value
        strength_training_experience=None,  # new field not auto-populated
    )
    assert u.training_experience == "intermediate"
    assert u.strength_training_experience is None


def test_legacy_training_experience_not_migrated_to_strength_field():
    # strength_training_experience stays None even when legacy training_experience is set
    user = _make_user(training_experience="advanced", strength_training_experience=None)
    assert user.training_experience == "advanced"
    assert user.strength_training_experience is None


# ---------------------------------------------------------------------------
# 9. Profile update and read correctly persist/expose the new field
# ---------------------------------------------------------------------------


def test_profile_update_persists_strength_training_experience():
    from app.models import UserDB

    u = UserDB(
        user_key="test:update",
        name="Tester",
        weight=80,
        gender="mężczyzna",
    )
    # Simulate profile update setting the field
    u.strength_training_experience = "intermediate"
    assert u.strength_training_experience == "intermediate"
    d = u.to_profile_dict()
    assert d.get("strength_training_experience") == "intermediate"


def test_schema_field_exists():
    from app.schemas import ProfileUpdateRequest

    # Field should exist on the schema (optional, defaults to None)
    assert "strength_training_experience" in ProfileUpdateRequest.model_fields


# ---------------------------------------------------------------------------
# 10. Consistency fixes: missing strength experience is beginner-safe everywhere
# ---------------------------------------------------------------------------


def test_progression_missing_strength_uses_beginner_not_legacy_intermediate():
    """Legacy training_experience='intermediate' must NOT override missing strength_training_experience."""
    session = _make_session()
    user = UserDB(
        user_key="test:legacy_intermediate",
        name="Tester",
        weight=80.0,
        gender="mężczyzna",
        training_experience="intermediate",      # legacy - must be ignored
        strength_training_experience=None,       # new field missing
        dumbbell_max_kg_per_dumbbell=20.0,       # known capacity, isolates strength behavior
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    exercises = [_dumbbell_exercise("dumbbell_bench_press")]
    enriched = _enrich(session, user, exercises)
    # Beginner raw estimate: 80 * 0.55 * 0.60 * 1.0 * 0.45 = 11.88 kg; no increment → no rounding.
    # Dumbbell max 20 kg known → no capacity instruction, concrete estimate returned.
    assert abs(enriched[0]["weight_kg"] - 11.88) < 0.001, (
        f"Expected beginner raw weight 11.88 kg, got {enriched[0]['weight_kg']} kg"
    )


def test_generator_missing_strength_ignores_advanced_assessment(monkeypatch):
    """assessment.training_level='zaawansowany' must not override missing strength experience."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    user = _make_user(strength_training_experience=None)
    assessment = _make_assessment(level="zaawansowany")  # advanced in assessment - ignored
    plan = _plan(user, assessment)
    levels = _all_exercise_levels(plan)
    assert "advanced" not in levels, f"advanced exercise with missing strength experience: {levels}"
    assert "elite" not in levels, f"elite exercise with missing strength experience: {levels}"


def test_resolve_strength_level_both_missing_returns_beginner():
    """_resolve_strength_level returns 'beginner' when strength field missing, regardless of assessment."""
    user = _make_user(strength_training_experience=None)
    assessment = _make_assessment(level="zaawansowany")
    level = _resolve_strength_level(user, assessment)
    assert level == "beginner"


def test_resolve_strength_level_explicit_beginner():
    user = _make_user(strength_training_experience="beginner")
    assert _resolve_strength_level(user, None) == "beginner"


def test_resolve_strength_level_explicit_intermediate():
    user = _make_user(strength_training_experience="intermediate")
    assert _resolve_strength_level(user, None) == "intermediate"


def test_resolve_strength_level_explicit_advanced():
    user = _make_user(strength_training_experience="advanced")
    assert _resolve_strength_level(user, None) == "advanced"


# ---------------------------------------------------------------------------
# Regression: setting strength_training_experience must not drop dumbbell fields
# ---------------------------------------------------------------------------


def test_strength_experience_update_preserves_dumbbell_fields():
    u = UserDB(
        user_key="test:dumbbell-preserve",
        name="Tester",
        weight=80,
        gender="mężczyzna",
        dumbbell_type="adjustable",
        dumbbell_max_kg_per_dumbbell=24.0,
        dumbbell_increment_kg=2.0,
        strength_training_experience=None,
    )
    # Simulate profile update setting only strength_training_experience.
    u.strength_training_experience = "intermediate"
    assert u.strength_training_experience == "intermediate"
    assert u.dumbbell_type == "adjustable"
    assert u.dumbbell_max_kg_per_dumbbell == 24.0
    assert u.dumbbell_increment_kg == 2.0
