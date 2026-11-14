"""Testy zachowania generatora planu treningowego (exercise selection)."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from app.plan.deterministic import build_deterministic_plan


def _make_user(*, frequency, days, level, equipment_list, focus, goal="masa mięśniowa"):
    user = SimpleNamespace(
        name="test",
        goal=goal,
        frequency=frequency,
        diet="standardowa",
        gender="mężczyzna",
        age=25,
        height=180,
        weight=80,
        calories_target=2500,
        meals_per_day=4,
        allergies="",
        health_limitations="",
        injuries="",
        training_locations_json="[]",
        sport_focus="",
        basketball_position=None,
        sport_specialization="",
        sport_training_days_json="[]",
        training_availability_json="{}",
        sport_training_schedule_json="{}",
        training_focus_json=json.dumps(focus, ensure_ascii=False),
        improvement_areas_json="[]",
        available_equipment_json=json.dumps(equipment_list, ensure_ascii=False),
        avoid_exercises_json="[]",
        preferred_foods_json="[]",
        avoid_foods_json="[]",
        equipment=",".join(equipment_list),
    )
    user.get_list = lambda field: json.loads(getattr(user, field, "[]") or "[]")
    return user


def _plan(frequency, days, level, equipment_list, focus):
    return build_deterministic_plan(
        _make_user(frequency=frequency, days=days, level=level,
                   equipment_list=equipment_list, focus=focus),
        _make_assessment(days=days, level=level),
    )
    user.get_list = lambda field: json.loads(getattr(user, field, "[]") or "[]")
    return user


def _make_assessment(*, days, level):
    return SimpleNamespace(
        sessions_per_week=days,
        training_level=level,
        recovery_score=None,
        availability_hours_per_week=None,
    )


def _plan(frequency, days, level, equipment_list, focus):
    return build_deterministic_plan(
        _make_user(frequency=frequency, days=days, level=level,
                   equipment_list=equipment_list, focus=focus),
        _make_assessment(days=days, level=level),
    )


def _exercise_objects(day):
    from app.exercises.data import get_exercise
    out = []
    for item in day["workout"]["exercises"]:
        ex = get_exercise(item.get("exercise_id", item["name"]))
        out.append((item, ex))
    return out


def _training_days(plan):
    return [d for d in plan["days"] if d["day_type"] != "rest"]


# ---------------------------------------------------------------------------
# persona 1: początkujący, pełna siłownia, 3 dni
# ---------------------------------------------------------------------------

def test_persona1_beginner_gym_chest_day_has_horizontal_push_with_equipment():
    plan = _plan("3 dni", 3, "początkujący", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    chest_day = next(d for d in _training_days(plan) if d["workout"]["focus"] == "klatka")
    found = False
    for item, ex in _exercise_objects(chest_day):
        if ex is None:
            continue
        if ex.movement_pattern == "horizontal_push" and (
            "barbell" in ex.equipment or "dumbbell" in ex.equipment or "machine" in ex.equipment
        ):
            found = True
    assert found


def test_persona1_beginner_gym_leg_day_has_squat_and_hinge():
    plan = _plan("3 dni", 3, "początkujący", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    leg_day = next(d for d in _training_days(plan) if d["workout"]["focus"] == "nogi")
    patterns = set()
    for item, ex in _exercise_objects(leg_day):
        if ex is not None:
            patterns.add(ex.movement_pattern)
    assert "squat" in patterns
    assert "hinge" in patterns


def test_persona1_beginner_gym_no_intermediate_or_advanced():
    plan = _plan("3 dni", 3, "początkujący", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    for day in _training_days(plan):
        for item, ex in _exercise_objects(day):
            if ex is not None:
                assert ex.level == "beginner", f"{ex.id} level={ex.level}"


def test_persona1_beginner_gym_no_plyometric_box_jumps():
    plan = _plan("3 dni", 3, "początkujący", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    for day in _training_days(plan):
        for item, ex in _exercise_objects(day):
            if ex is not None:
                assert "box" not in ex.name_pl.lower()


# ---------------------------------------------------------------------------
# persona 3: średniozaawansowany, pełna siłownia, 4 dni
# ---------------------------------------------------------------------------

def test_persona3_intermediate_gym_differs_from_persona1_and_has_arms_or_shoulders_day():
    plan1 = _plan("3 dni", 3, "początkujący", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    plan3 = _plan("4 dni", 4, "średniozaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"],
                  ["klatka", "plecy", "nogi", "barki"])

    names1 = set()
    for day in _training_days(plan1):
        for item, ex in _exercise_objects(day):
            if ex is not None:
                names1.add(ex.name_pl)

    names3 = set()
    for day in _training_days(plan3):
        for item, ex in _exercise_objects(day):
            if ex is not None:
                names3.add(ex.name_pl)

    if names3:
        new_names = names3 - names1
        assert len(new_names) >= len(names3) / 2, f"nowe: {new_names}, wszystkie3: {names3}"

    has_arms_or_shoulders = any(
        d["workout"]["focus"] in {"barki", "biceps", "triceps"}
        for d in _training_days(plan3)
    )
    assert has_arms_or_shoulders


# ---------------------------------------------------------------------------
# persona 7: masa własna, 3 dni
# ---------------------------------------------------------------------------

def test_persona7_bodyweight_every_day_at_least_three_exercises():
    plan = _plan("3 dni", 3, "początkujący", [], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    for day in _training_days(plan):
        assert len(day["workout"]["exercises"]) >= 3, f"{day['day']}: {len(day['workout']['exercises'])}"
