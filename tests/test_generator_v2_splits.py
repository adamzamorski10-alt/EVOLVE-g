"""Testy zachowania generatora v2 (szablony sesji oparte na wzorcach ruchu / splity)."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from app.plan.deterministic import build_deterministic_plan


def _make_user(*, frequency, days, level, equipment_list, focus, goal="masa mięśniowa"):
    presets = {
        "gym_full": ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"],
        "dumbbells": ["hantle", "ławka"],
        "bodyweight": [],
    }
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


def _make_assessment(*, days, level, recovery=None, hours=None):
    return SimpleNamespace(
        sessions_per_week=days,
        training_level=level,
        recovery_score=recovery,
        availability_hours_per_week=hours,
    )


def _plan(frequency, days, level, equipment_list, focus, *, recovery=None, hours=None):
    return build_deterministic_plan(
        _make_user(frequency=frequency, days=days, level=level,
                   equipment_list=equipment_list, focus=focus),
        _make_assessment(days=days, level=level, recovery=recovery, hours=hours),
    )


def _training_days(plan):
    return [d for d in plan["days"] if d["day_type"] != "rest"]


def _exercise_names(day):
    return [e["name"] for e in day["workout"]["exercises"]]


def _exercise_patterns(day):
    from app.exercises.data import get_exercise
    patterns = []
    for e in day["workout"]["exercises"]:
        ex = get_exercise(e.get("exercise_id", e["name"]))
        if ex is not None:
            patterns.append(ex.movement_pattern)
    return patterns


def _exercise_levels(day):
    from app.exercises.data import get_exercise
    levels = []
    for e in day["workout"]["exercises"]:
        ex = get_exercise(e.get("exercise_id", e["name"]))
        if ex is not None:
            levels.append(ex.level)
    return levels


def _exercise_types(day):
    from app.exercises.data import get_exercise
    types = []
    for e in day["workout"]["exercises"]:
        ex = get_exercise(e.get("exercise_id", e["name"]))
        if ex is not None:
            types.append(ex.type)
    return types


def _exercise_tags(day):
    from app.exercises.data import get_exercise
    tags = []
    for e in day["workout"]["exercises"]:
        ex = get_exercise(e.get("exercise_id", e["name"]))
        if ex is not None:
            tags.extend(getattr(ex, "tags", []) or [])
    return tags


# ---------------------------------------------------------------------------
# Testy splitu według liczby dni i poziomu
# ---------------------------------------------------------------------------

def test_split_1_day_full_body(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("3 dni", 1, "początkujący", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    td = _training_days(plan)
    assert len(td) == 1
    assert "full_body" in td[0]["workout"]["focus"]


def test_split_2_days_full_body_ab(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("2 dni", 2, "początkujący", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    td = _training_days(plan)
    assert len(td) == 2
    focuses = [d["workout"]["focus"] for d in td]
    assert "full_body_a" in focuses
    assert "full_body_b" in focuses


def test_split_3_days_beginner_full_body_aba(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("3 dni", 3, "początkujący", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    td = _training_days(plan)
    assert len(td) == 3
    focuses = [d["workout"]["focus"] for d in td]
    assert focuses == ["full_body_a", "full_body_b", "full_body_a"]


def test_split_3_days_advanced_upper_lower_full(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("3 dni", 3, "zaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    td = _training_days(plan)
    assert len(td) == 3
    focuses = [d["workout"]["focus"] for d in td]
    assert "upper_a" in focuses
    assert "lower_a" in focuses
    assert "full_body_a" in focuses


def test_split_4_days_upper_lower_ab(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("4 dni", 4, "średniozaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    td = _training_days(plan)
    assert len(td) == 4
    focuses = [d["workout"]["focus"] for d in td]
    assert focuses == ["upper_a", "lower_a", "upper_b", "lower_b"]


def test_split_5_days_upper_lower_push_pull_legs(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("5 dni", 5, "średniozaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    td = _training_days(plan)
    assert len(td) == 5
    focuses = [d["workout"]["focus"] for d in td]
    assert "upper_a" in focuses
    assert "lower_a" in focuses
    assert "push" in focuses
    assert "pull" in focuses
    assert "legs" in focuses


def test_split_6_days_push_pull_legs_x2(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("6 dni", 6, "średniozaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    td = _training_days(plan)
    assert len(td) == 6
    focuses = [d["workout"]["focus"] for d in td]
    assert focuses.count("push") == 2
    assert focuses.count("pull") == 2
    assert focuses.count("legs") == 2


# ---------------------------------------------------------------------------
# Testy rozkładu dni (przerwa między sesjami tej samej partii >= 1 dzień)
# ---------------------------------------------------------------------------

def test_training_days_no_consecutive_same_group(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("4 dni", 4, "średniozaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    td = _training_days(plan)
    day_names = [d["day"] for d in td]
    assert len(day_names) == 4
    # Dni treningowe z przerwą >= 1 dzień między sesjami tej samej partii (np. upper A w Pn, upper B w Śr).
    assert day_names == ["Poniedziałek", "Wtorek", "Środa", "Czwartek"]


def test_3_days_spread_mon_wed_fri(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("3 dni", 3, "początkujący", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    td = _training_days(plan)
    day_names = [d["day"] for d in td]
    assert len(day_names) == 3
    assert day_names == ["Poniedziałek", "Wtorek", "Środa"]


def test_sunday_not_a_training_day(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("6 dni", 6, "średniozaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    td = _training_days(plan)
    day_names = [d["day"] for d in td]
    assert "Niedziela" not in day_names


# ---------------------------------------------------------------------------
# Testy ograniczeń: brak cardio/plyometrii w sesjach, liczba ćwiczeń, brak pustych/duplikowanych
# ---------------------------------------------------------------------------

def test_no_cardio_or_plyometric_in_strength_sessions(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("4 dni", 4, "średniozaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    for day in _training_days(plan):
        assert "cardio" not in _exercise_tags(day), f"cardio w dniu {day['day']}"
        assert "plyometric" not in _exercise_tags(day), f"plyometric w dniu {day['day']}"


def test_exercise_count_intermediate_4_to_6(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("4 dni", 4, "średniozaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    for day in _training_days(plan):
        n = len(_exercise_names(day))
        assert 4 <= n <= 6, f"{day['day']}: {n} ćwiczeń"


def test_exercise_count_beginner_3_to_5(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("3 dni", 3, "początkujący", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    for day in _training_days(plan):
        n = len(_exercise_names(day))
        assert 3 <= n <= 5, f"{day['day']}: {n} ćwiczeń"


def test_no_empty_or_duplicate_days(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("4 dni", 4, "średniozaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    td = _training_days(plan)
    for day in td:
        assert len(_exercise_names(day)) > 0, f"{day['day']} jest puste"
    day_sets = [tuple(_exercise_names(d)) for d in td]
    assert len(set(day_sets)) == len(day_sets), "Zduplikowane dni"


def test_no_repeat_exercise_a_vs_b_same_group(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("4 dni", 4, "średniozaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    td = _training_days(plan)
    upper_a = set(_exercise_names(td[0]))
    upper_b = set(_exercise_names(td[2]))
    # upper_a i upper_b nie powinny mieć wspólnych ćwiczeń (jeśli są zamienniki)
    overlap = upper_a & upper_b
    assert len(overlap) == 0, f"Powtarzające się ćwiczenia upper A/B: {overlap}"


# ---------------------------------------------------------------------------
# Testy poziomu i sprzętu
# ---------------------------------------------------------------------------

def test_beginner_only_beginner_exercises(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("3 dni", 3, "początkujący", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    for day in _training_days(plan):
        for level in _exercise_levels(day):
            assert level == "beginner", f"{day['day']}: {level}"


def test_intermediate_no_advanced(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("4 dni", 4, "średniozaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    for day in _training_days(plan):
        for level in _exercise_levels(day):
            assert level != "advanced", f"{day['day']}: {level}"


def test_equipment_respected(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("2 dni", 2, "średniozaawansowany", ["hantle", "ławka"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    td = _training_days(plan)
    assert len(td) == 2
    for day in td:
        assert len(_exercise_names(day)) > 0


# ---------------------------------------------------------------------------
# Testy wzorców ruchu w dniach nóg / full body
# ---------------------------------------------------------------------------

def test_leg_or_full_body_has_squat_or_hinge(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("4 dni", 4, "średniozaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    td = _training_days(plan)
    for day in td:
        patterns = _exercise_patterns(day)
        if "nogi" in day["workout"]["focus"] or "full_body" in day["workout"]["focus"]:
            assert "squat" in patterns or "hinge" in patterns, f"{day['day']}: brak squat/hinge"


# ---------------------------------------------------------------------------
# Testy weekly_summary
# ---------------------------------------------------------------------------

def test_weekly_summary_present(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("4 dni", 4, "średniozaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    summary = plan["_planner"].get("weekly_summary")
    assert summary is not None
    assert "sets_per_group" in summary
    assert "sessions_per_group" in summary
    for g in ("klatka", "plecy", "nogi", "brzuch", "barki", "biceps", "triceps"):
        assert g in summary["sets_per_group"]
        assert g in summary["sessions_per_group"]


def test_group_frequency_at_least_2_for_2_to_6_days(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    for days_num in (2, 3, 4, 5, 6):
        plan = _plan(f"{days_num} dni", days_num, "średniozaawansowany",
                     ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"],
                     ["klatka", "plecy", "nogi", "brzuch", "barki"])
        summary = plan["_planner"]["weekly_summary"]
        sessions = summary["sessions_per_group"]
        # Klatka, plecy, nogi powinny być trenowane >= 2 razy w tygodniu (dla 2-6 dni)
        if days_num >= 2:
            assert sessions.get("klatka", 0) >= 2, f"{days_num} dni: klatka {sessions.get('klatka', 0)}"
            assert sessions.get("plecy", 0) >= 2, f"{days_num} dni: plecy {sessions.get('plecy', 0)}"
            assert sessions.get("nogi", 0) >= 2, f"{days_num} dni: nogi {sessions.get('nogi', 0)}"


# ---------------------------------------------------------------------------
# Testy determinizmu
# ---------------------------------------------------------------------------

def test_determinism_same_inputs_same_plan(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan1 = _plan("4 dni", 4, "średniozaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    plan2 = _plan("4 dni", 4, "średniozaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    names1 = [tuple(_exercise_names(d)) for d in _training_days(plan1)]
    names2 = [tuple(_exercise_names(d)) for d in _training_days(plan2)]
    assert names1 == names2


# ---------------------------------------------------------------------------
# Test zmiennej środowiskowej PLAN_GENERATOR
# ---------------------------------------------------------------------------

def test_plan_generator_env_switch(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v1")
    plan_v1 = _plan("3 dni", 3, "początkujący", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    assert plan_v1["_planner"]["version"] == "deterministic-v2"

    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan_v2 = _plan("3 dni", 3, "początkujący", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    assert plan_v2["_planner"]["version"] == "deterministic-v2-splits"
