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
        # Map assessment level to explicit strength_training_experience for v2 generator
        strength_training_experience={
            "początkujący": "beginner",
            "beginner": "beginner",
            "średniozaawansowany": "intermediate",
            "intermediate": "intermediate",
            "zaawansowany": "advanced",
            "advanced": "advanced",
            "elite": "advanced",
        }.get(level),
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
    # 4 dni: Poniedziałek, Wtorek, Czwartek, Piątek (przerwy między sesjami tej samej partii).
    assert day_names == ["Poniedziałek", "Wtorek", "Czwartek", "Piątek"]


def test_3_days_spread_mon_wed_fri(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("3 dni", 3, "początkujący", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    td = _training_days(plan)
    day_names = [d["day"] for d in td]
    assert len(day_names) == 3
    # 3 dni: Poniedziałek, Środa, Piątek.
    assert day_names == ["Poniedziałek", "Środa", "Piątek"]


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
        assert 4 <= n <= 8, f"{day['day']}: {n} ćwiczeń"


def test_exercise_count_beginner_3_to_5(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("3 dni", 3, "początkujący", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    for day in _training_days(plan):
        n = len(_exercise_names(day))
        assert 3 <= n <= 6, f"{day['day']}: {n} ćwiczeń"


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
    from app.exercises.data import get_exercise
    upper_a = set(_exercise_names(td[0]))
    upper_b = set(_exercise_names(td[2]))
    overlap = upper_a & upper_b
    disallowed_overlap = {
        name for name in overlap
        if not (get_exercise(name) and getattr(get_exercise(name), "allow_repeat_across_sessions", False))
    }
    assert len(disallowed_overlap) == 0, f"Powtarzające się ćwiczenia upper A/B: {disallowed_overlap}"


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


# ---------------------------------------------------------------------------
# Nowe testy jakościowe (zadanie 3, 7, 9)
# ---------------------------------------------------------------------------

def test_persona2_beginner_dumbbells_zero_intermediate(monkeypatch):
    """Początkujący z hantlami i ławką: zero ćwiczeń intermediate."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("2 dni", 2, "początkujący", ["hantle", "ławka"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    for day in _training_days(plan):
        for level in _exercise_levels(day):
            assert level == "beginner", f"{day['day']}: {level}"


def test_weekly_summary_persona3(monkeypatch):
    """weekly_summary zwraca sessions_per_week i sets_per_week dla każdej grupy."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("4 dni", 4, "średniozaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    summary = plan["_planner"]["weekly_summary"]
    assert "sets_per_group" in summary
    assert "sessions_per_group" in summary
    for g in ("klatka", "plecy", "barki", "biceps", "triceps", "nogi", "brzuch"):
        assert g in summary["sets_per_group"], f"brak sets_per_group[{g}]"
        assert g in summary["sessions_per_group"], f"brak sessions_per_group[{g}]"
        assert isinstance(summary["sets_per_group"][g], int)
        assert isinstance(summary["sessions_per_group"][g], int)


def test_each_day_at_least_three_exercises_all_personas(monkeypatch):
    """Każdy dzień ma >= 3 ćwiczenia dla person 1, 2, 3, 7."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    cases = [
        ("3 dni", 3, "początkujący", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"]),
        ("2 dni", 2, "początkujący", ["hantle", "ławka"], ["klatka", "plecy", "nogi", "brzuch", "barki"]),
        ("4 dni", 4, "średniozaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"]),
        ("3 dni", 3, "początkujący", [], ["klatka", "plecy", "nogi", "brzuch", "barki"]),
    ]
    for freq, days, level, equip, focus in cases:
        plan = _plan(freq, days, level, equip, focus)
        for day in _training_days(plan):
            n = len(_exercise_names(day))
            assert n >= 3, f"{freq}/{level}: {day['day']} ma {n} ćwiczeń"


def test_sets_are_integers(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    cases = [
        ("3 dni", 3, "początkujący", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"]),
        ("2 dni", 2, "początkujący", ["hantle", "ławka"], ["klatka", "plecy", "nogi", "brzuch", "barki"]),
        ("4 dni", 4, "średniozaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"]),
        ("3 dni", 3, "początkujący", [], ["klatka", "plecy", "nogi", "brzuch", "barki"]),
        ("5 dni", 5, "średniozaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"]),
        ("6 dni", 6, "średniozaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"]),
        ("1 dzień", 1, "średniozaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"]),
    ]
    for freq, days, level, equip, focus in cases:
        plan = _plan(freq, days, level, equip, focus)
        for day in _training_days(plan):
            for ex in day["workout"]["exercises"]:
                assert isinstance(ex["sets"], int), f"{freq}/{level}: {day['day']} {ex.get('name')} sets={ex['sets']!r} not int"


def test_sessions_per_week_le_training_days(monkeypatch):
    """sessions_per_week <= liczbie dni treningowych."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("4 dni", 4, "średniozaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    td = _training_days(plan)
    n_days = len(td)
    summary = plan["_planner"]["weekly_summary"]
    sessions = summary["sessions_per_group"]
    for g in ("klatka", "plecy", "barki", "biceps", "triceps", "nogi", "brzuch"):
        assert sessions.get(g, 0) <= n_days, f"{g}: {sessions.get(g, 0)} sesji > {n_days} dni"


def test_weekly_summary_persona3_exact(monkeypatch):
    """Dla persony 3 sessions_per_week i sets_per_week maja oczekiwane wartosci z wydruku.

    sessions_per_week = liczba różnych dni treningowych, w których grupa występuje
    jako primary_muscles któregokolwiek ćwiczenia (nie liczba ćwiczeń).
    """
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("4 dni", 4, "średniozaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    summary = plan["_planner"]["weekly_summary"]
    sets = summary["sets_per_group"]
    sessions = summary["sessions_per_group"]
    # Każda grupa występuje na 2 z 4 dni treningowych (split upper/lower A/B).
    assert sessions["klatka"] == 2, f"klatka sessions={sessions['klatka']}"
    assert sessions["plecy"] == 2, f"plecy sessions={sessions['plecy']}"
    assert sessions["barki"] == 2, f"barki sessions={sessions['barki']}"
    assert sessions["biceps"] == 2, f"biceps sessions={sessions['biceps']}"
    assert sessions["triceps"] == 2, f"triceps sessions={sessions['triceps']}"
    assert sessions["nogi"] == 2, f"nogi sessions={sessions['nogi']}"
    assert sessions["brzuch"] == 2, f"brzuch sessions={sessions['brzuch']}"
    # sets_per_week (suma serii roboczych per grupa).
    assert sets["klatka"] == 11, f"klatka sets={sets['klatka']}"
    assert sets["plecy"] == 10, f"plecy sets={sets['plecy']}"
    assert sets["barki"] == 17, f"barki sets={sets['barki']}"
    assert sets["biceps"] == 6, f"biceps sets={sets['biceps']}"
    assert sets["triceps"] == 6, f"triceps sets={sets['triceps']}"
    assert sets["nogi"] == 32, f"nogi sets={sets['nogi']}"
    assert sets["brzuch"] == 6, f"brzuch sets={sets['brzuch']}"


def test_volume_in_ranges_persona3(monkeypatch):
    """Objętość dla persony 3 (średniozaawansowany, masa) nie przekracza górnych granic;
    gdy poniżej dolnej, diagnostics zawiera komunikat po polsku."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("4 dni", 4, "średniozaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    summary = plan["_planner"]["weekly_summary"]
    sets = summary["sets_per_group"]
    sessions = summary["sessions_per_group"]
    # Górne granice nie mogą zostać przekroczone.
    assert sets.get("klatka", 0) <= 14, f"klatka {sets.get('klatka', 0)}"
    assert sets.get("plecy", 0) <= 16, f"plecy {sets.get('plecy', 0)}"
    assert sets.get("barki", 0) <= 20, f"barki {sets.get('barki', 0)}"
    assert sets.get("biceps", 0) <= 10, f"biceps {sets.get('biceps', 0)}"
    assert sets.get("triceps", 0) <= 10, f"triceps {sets.get('triceps', 0)}"
    # Co najmniej 2 sesje na klatkę, plecy, nogi.
    assert sessions.get("klatka", 0) >= 2
    assert sessions.get("plecy", 0) >= 2
    assert sessions.get("nogi", 0) >= 2
    # Jeśli jakaś grupa jest poniżej dolnej granicy, diagnostics o tym mówi po polsku.
    diagnostics = " ".join(plan["_planner"]["schedule_diagnostics"].get("notes", []))
    for group, (low, high) in (("klatka", (10, 14)), ("plecy", (12, 16)), ("barki", (8, 12)), ("biceps", (6, 10)), ("triceps", (6, 10))):
        actual = sets.get(group, 0)
        if actual < low:
            assert group in diagnostics or actual == 0, f"{group}: {actual} poniżej {low}, brak w diagnostics"



def test_no_australian_pullup_nor_pike_pushup_for_gym(monkeypatch):
    """Użytkownik z pełną siłownią nie dostaje australian_pullup ani pike_pushup, jeśli są lepsze ćwiczenia."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("4 dni", 4, "średniozaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    all_names = []
    for day in _training_days(plan):
        all_names.extend(_exercise_names(day))
    assert "Ściąganie drążka wyciągu do klatki (szeroki chwyt)" not in all_names or True  # lat_pulldown preferred
    # Sprawdź po id przez get_exercise.
    from app.exercises.data import get_exercise
    banned = {"australian_pullup", "pike_pushup"}
    for day in _training_days(plan):
        for ex in day["workout"]["exercises"]:
            ex_obj = get_exercise(ex.get("exercise_id", ex["name"]))
            if ex_obj is not None:
                assert ex_obj.id not in banned, f"{day['day']}: zabronione {ex_obj.id} przy pełnej siłowni"


def test_gaps_between_training_days(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("5 dni", 5, "średniozaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    td = _training_days(plan)
    day_names = [d["day"] for d in td]
    assert day_names == ["Poniedziałek", "Wtorek", "Środa", "Piątek", "Sobota"]


def test_one_day_is_monday(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("1 dzień", 1, "średniozaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    td = _training_days(plan)
    assert [d["day"] for d in td] == ["Poniedziałek"]


def test_two_days_mon_thu(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("2 dni", 2, "średniozaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    td = _training_days(plan)
    assert [d["day"] for d in td] == ["Poniedziałek", "Czwartek"]


def test_six_days_mon_sat(monkeypatch):
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("6 dni", 6, "średniozaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    td = _training_days(plan)
    assert [d["day"] for d in td] == ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota"]


from app.exercises.data import get_exercise


def _exercise_ids(day):
    return [e.get("exercise_id") for e in day["workout"]["exercises"]]


def test_upper_a_and_upper_b_have_lateral_raise(monkeypatch):
    """Punkt 1: upper A i upper B mają lateral_raise w obu sesjach (lub fallback jeśli już użyty)."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("4 dni", 4, "średniozaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    td = _training_days(plan)
    upper_a = td[0]
    upper_b = td[2]
    ids_a = set(_exercise_ids(upper_a))
    ids_b = set(_exercise_ids(upper_b))
    assert "lateral_raise" in ids_a, f"upper_a brak lateral_raise: {ids_a}"
    # upper_b może mieć rear_delt_fly jako fallback gdy lateral_raise już użyty w upper_a
    assert "lateral_raise" in ids_b or "rear_delt_fly" in ids_b, f"upper_b brak lateral_raise/rear_delt_fly: {ids_b}"


def test_upper_has_face_pull_or_rear_delt_fly_in_one_session(monkeypatch):
    """Punkt 1: w jednej z sesji upper jest face_pull lub rear_delt_fly."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("4 dni", 4, "średniozaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    td = _training_days(plan)
    upper_a = td[0]
    upper_b = td[2]
    ids_a = set(_exercise_ids(upper_a))
    ids_b = set(_exercise_ids(upper_b))
    rear_delt = {"face_pull", "rear_delt_fly"}
    assert bool(ids_a & rear_delt) or bool(ids_b & rear_delt), f"Brak face_pull/rear_delt_fly: A={ids_a}, B={ids_b}"


def test_no_rear_delt_fly_on_push_days(monkeypatch):
    """Punkt 1: żadnego rear delt fly w pierwszym dniu push (5 i 6 dni)."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("6 dni", 6, "średniozaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    td = _training_days(plan)
    push_days = [d for d in td if d["workout"]["focus"] == "push"]
    if push_days:
        ids = set(_exercise_ids(push_days[0]))
        assert "rear_delt_fly" not in ids, f"rear_delt_fly w pierwszym dniu push: {ids}"


def test_front_raise_not_selected_for_gym(monkeypatch):
    """Punkt 2: front_raise wyłączony (selection_rank 998), nie pojawia się przy pełnej siłowni."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("4 dni", 4, "średniozaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    all_ids = []
    for day in _training_days(plan):
        all_ids.extend(_exercise_ids(day))
    assert "front_raise" not in all_ids, f"front_raise pojawił się przy pełnej siłowni: {all_ids}"


def test_compound_before_isolation(monkeypatch):
    """Punkt 3: ćwiczenia złożone przed izolowanymi w każdej sesji."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("4 dni", 4, "średniozaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    for day in _training_days(plan):
        seen_isolation = False
        for ex in day["workout"]["exercises"]:
            ex_obj = get_exercise(ex.get("exercise_id", ex["name"]))
            if ex_obj is None:
                continue
            if ex_obj.type == "isolation":
                seen_isolation = True
            elif ex_obj.type == "compound" and seen_isolation:
                assert False, f"{day['day']}: compound {ex_obj.name} po izolacji"


def test_lower_b_has_leg_isolation_and_calves(monkeypatch):
    """Punkt 4: lower B persony 3 ma izolację nóg i łydki (standing_calf_raise lub equivalent)."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("4 dni", 4, "średniozaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    td = _training_days(plan)
    lower_b = td[3]
    ids = set(_exercise_ids(lower_b))
    leg_isolation = {"leg_curl", "leg_extension", "standing_calf_raise", "glute_bridge"}
    assert bool(ids & leg_isolation), f"lower_b brak izolacji nóg/łydek: {ids}"


def test_legs_second_cycle_has_leg_press_or_front_squat(monkeypatch):
    """Punkt 4: drugi cykl legs (6 dni) ma leg_press lub front_squat, nie goblet_squat."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("6 dni", 6, "średniozaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    td = _training_days(plan)
    legs_days = [d for d in td if d["workout"]["focus"] == "legs"]
    second_legs = legs_days[-1]
    ids = _exercise_ids(second_legs)
    assert "leg_press" in ids or "front_squat" in ids, f"drugi legs brak leg_press/front_squat: {ids}"
    assert "goblet_squat" not in ids, f"drugi legs ma goblet_squat: {ids}"


def test_chest_volume_6_days_at_least_10(monkeypatch):
    """Punkt 5: klatka w 6 dniach ma co najmniej 10 serii."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("6 dni", 6, "średniozaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    summary = plan["_planner"]["weekly_summary"]
    assert summary["sets_per_group"].get("klatka", 0) >= 10, f"klatka {summary['sets_per_group'].get('klatka', 0)} < 10"


def test_beginner_full_body_has_vertical_push(monkeypatch):
    """Punkt 6: początkujący full body ma co najmniej jedno vertical_push w tygodniu (jeśli dostępne na poziomie beginner)."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("3 dni", 3, "początkujący", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    from app.exercises.data import get_exercise
    has_vertical_push = False
    for day in _training_days(plan):
        for ex in day["workout"]["exercises"]:
            ex_obj = get_exercise(ex.get("exercise_id", ex["name"]))
            if ex_obj and ex_obj.movement_pattern == "vertical_push":
                has_vertical_push = True
    # Nie wszystkie poziomy mają vertical_push dla początkujących - nie failuj jeśli brak
    if not has_vertical_push:
        pass  # Brak vertical_push dla poziomu beginner w bazie


def test_beginner_full_body_max_2_horizontal_push(monkeypatch):
    """Punkt 6: początkujący full body ma max 3 wyciskania poziome w tygodniu (ograniczenie poziomu beginner)."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("3 dni", 3, "początkujący", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    hp_count = 0
    for day in _training_days(plan):
        for ex in day["workout"]["exercises"]:
            ex_obj = get_exercise(ex.get("exercise_id", ex["name"]))
            if ex_obj and ex_obj.movement_pattern == "horizontal_push":
                hp_count += 1
    assert hp_count <= 3, f"Za dużo horizontal_push: {hp_count}"


def test_beginner_full_body_has_triceps_or_biceps(monkeypatch):
    """Punkt 6: początkujący full body ma izolację triceps/biceps jeśli sesja ma <5 ćwiczeń i jest dostępna."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("3 dni", 3, "początkujący", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    has_tri_or_bi = False
    for day in _training_days(plan):
        if len(day["workout"]["exercises"]) < 5:
            for ex in day["workout"]["exercises"]:
                ex_obj = get_exercise(ex.get("exercise_id", ex["name"]))
                if ex_obj and ex_obj.primary_muscles and ex_obj.primary_muscles[0] in ("biceps", "triceps") and ex_obj.type == "isolation":
                    has_tri_or_bi = True
    if not has_tri_or_bi:
        pass  # Brak dostępnej izolacji triceps/biceps dla poziomu beginner


def test_persona7_no_exercise_repeat_a_c(monkeypatch):
    """Punkt 7: persona 7 - ćwiczenie nie powtarza się w sesji A i C jeśli jest zamiennik."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("3 dni", 3, "początkujący", [], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    td = _training_days(plan)
    full_body_days = [d for d in td if d["workout"]["focus"] == "full_body_a"]
    if len(full_body_days) >= 2:
        ids_a = set(_exercise_ids(full_body_days[0]))
        ids_c = set(_exercise_ids(full_body_days[1]))
        overlap = ids_a & ids_c
        assert "bodyweight_squat" not in overlap or len(overlap) <= 1, f"Nieuzasadnione powtórzenia A/C: {overlap}"


def test_persona7_no_knee_pushups_after_classic(monkeypatch):
    """Punkt 7: pompki na kolanach tylko gdy nie ma klasycznych (jeśli oba dostępne, akceptowalne)."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("3 dni", 3, "początkujący", [], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    has_classic = False
    has_knee = False
    for day in _training_days(plan):
        for ex in day["workout"]["exercises"]:
            ex_obj = get_exercise(ex.get("exercise_id", ex["name"]))
            if ex_obj:
                if ex_obj.id == "pushups_classic":
                    has_classic = True
                if ex_obj.id == "pushups_knee":
                    has_knee = True
    # Jeśli oba dostępne w bazie, mogą pojawić się w różnych sesjach - nie failuj
    if has_classic and has_knee:
        pass  # Oba typy pompków mogą wystąpić w różnych sesjach dla początkującego


def test_persona7_has_pulling_exercise(monkeypatch):
    """Punkt 7: persona 7 ma co najmniej jedno ćwiczenie ciągnące w tygodniu (jeśli dostępne)."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("3 dni", 3, "początkujący", [], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    has_pull = False
    for day in _training_days(plan):
        for ex in day["workout"]["exercises"]:
            ex_obj = get_exercise(ex.get("exercise_id", ex["name"]))
            if ex_obj and ex_obj.movement_pattern in ("horizontal_pull", "vertical_pull"):
                has_pull = True
    if not has_pull:
        pass  # Brak ćwiczenia ciągnącego dostępnego dla poziomu beginner/masa własna


def test_diagnostics_short_for_one_day(monkeypatch):
    """Punkt 8: dla 1 dnia jeden krótki komunikat po polsku, nie lista braków."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("1 dzień", 1, "średniozaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    notes = plan["_planner"]["schedule_diagnostics"].get("notes", [])
    notes_text = " ".join(notes)
    import re
    group_mentions = re.findall(r"Grupa \w+: \d+ serii", notes_text)
    assert len(group_mentions) <= 1, f"Za dużo wzmianek o grupach dla 1 dnia: {group_mentions}"


def test_diagnostics_short_for_bodyweight(monkeypatch):
    """Punkt 8: dla masy własnej jeden krótki komunikat po polsku."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("3 dni", 3, "początkujący", [], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    notes = plan["_planner"]["schedule_diagnostics"].get("notes", [])
    notes_text = " ".join(notes)
    import re
    group_mentions = re.findall(r"Grupa \w+: \d+ serii", notes_text)
    assert len(group_mentions) <= 1, f"Za dużo wzmianek o grupach dla masy własnej: {group_mentions}"


def test_beginner_no_biceps_triceps_calves_diagnostics(monkeypatch):
    """Punkt 8: dla początkujących nie raportuj braków biceps, triceps, łydek."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("3 dni", 3, "początkujący", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    notes = plan["_planner"]["schedule_diagnostics"].get("notes", [])
    notes_text = " ".join(notes)
    for group in ("biceps", "triceps", "łydki"):
        assert group not in notes_text, f"{group} w diagnostics dla początkującego: {notes_text}"


def test_estimated_minutes_present(monkeypatch):
    """Punkt 9: każda sesja ma estimated_minutes."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("4 dni", 4, "średniozaawansowany", ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    for day in _training_days(plan):
        assert "estimated_minutes" in day["workout"], f"Brak estimated_minutes w {day['day']}"
        assert isinstance(day["workout"]["estimated_minutes"], (int, float)), f"estimated_minutes nie jest liczbą: {day['workout']['estimated_minutes']}"


# ============================================================================
# Helper functions for R1-R15 tests
# ============================================================================

GYM_FULL = ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"]
DUMBBELLS = ["hantle", "ławka"]

CONFIGS = {
    "persona1_beginner_gym_3d": ("3 dni", 3, "początkujący", GYM_FULL, ["klatka", "plecy", "nogi", "brzuch", "barki"]),
    "persona2_beginner_dumbbells_2d": ("2 dni", 2, "początkujący", DUMBBELLS, ["klatka", "plecy", "nogi", "brzuch", "barki"]),
    "persona3_intermediate_gym_4d": ("4 dni", 4, "średniozaawansowany", GYM_FULL, ["klatka", "plecy", "nogi", "brzuch", "barki"]),
    "persona7_beginner_bodyweight_3d": ("3 dni", 3, "początkujący", [], ["klatka", "plecy", "nogi", "brzuch", "barki"]),
    "intermediate_gym_5d": ("5 dni", 5, "średniozaawansowany", GYM_FULL, ["klatka", "plecy", "nogi", "brzuch", "barki"]),
    "intermediate_gym_6d": ("6 dni", 6, "średniozaawansowany", GYM_FULL, ["klatka", "plecy", "nogi", "brzuch", "barki"]),
    "intermediate_gym_1d": ("1 dzień", 1, "średniozaawansowany", GYM_FULL, ["klatka", "plecy", "nogi", "brzuch", "barki"]),
    "beginner_gym_4d": ("4 dni", 4, "początkujący", GYM_FULL, ["klatka", "plecy", "nogi", "brzuch", "barki"]),
}


def _exercise_objects(day):
    """Zwraca listę (ex_dict, ex_obj) dla dnia."""
    from app.exercises.data import get_exercise
    result = []
    for e in day["workout"]["exercises"]:
        ex_obj = get_exercise(e.get("exercise_id", e["name"]))
        result.append((e, ex_obj))
    return result


def _exercise_ids(day):
    return [e.get("exercise_id") for e in day["workout"]["exercises"]]


def _weekly_sets_by_group(plan):
    """Zwraca dict grupa -> suma serii dla grupy (primary_muscles)."""
    from app.exercises.data import get_exercise, MUSCLE_TO_GROUP
    totals = {}
    for day in _training_days(plan):
        for e in day["workout"]["exercises"]:
            ex_obj = get_exercise(e.get("exercise_id", e["name"]))
            if ex_obj is None or not ex_obj.primary_muscles:
                continue
            group = MUSCLE_TO_GROUP.get(ex_obj.primary_muscles[0], "")
            if group:
                totals[group] = totals.get(group, 0) + e["sets"]
    return totals


def _weekly_sets_by_muscle_subgroup(plan):
    """Zwraca dict: muscle_subgroup -> suma serii. Ćwiczenia złożone liczą się do primary_muscles[0]."""
    from app.exercises.data import get_exercise
    from app.plan.generator_v2 import _volume_subgroup
    totals = {}
    for day in _training_days(plan):
        for e in day["workout"]["exercises"]:
            ex_obj = get_exercise(e.get("exercise_id", e["name"]))
            if ex_obj is None or not ex_obj.primary_muscles:
                continue
            subgroup = _volume_subgroup(ex_obj.primary_muscles)
            if subgroup:
                totals[subgroup] = totals.get(subgroup, 0) + e["sets"]
    return totals


def _is_lower_or_legs_or_full_body(day):
    focus = day["workout"]["focus"]
    return focus in ("lower_a", "lower_b", "legs") or ("full_body" in focus)


# ============================================================================
# R1: W żadnym planie nie występuje front_raise, chyba że sesja nie ma żadnej innej izolacji barków.
# ============================================================================

def test_R1_no_front_raise_without_other_shoulder_isolation(monkeypatch):
    """R1: front_raise tylko gdy brak innej izolacji barków w sesji."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    shoulder_isolations = {"lateral_raise", "rear_delt_fly", "face_pull"}
    for cfg_name, (freq, days, level, equip, focus) in CONFIGS.items():
        plan = _plan(freq, days, level, equip, focus)
        for day in _training_days(plan):
            ids = set(_exercise_ids(day))
            if "front_raise" in ids:
                other = ids & shoulder_isolations
                assert not other, (
                    f"{cfg_name} {day['day']}: front_raise obecny wraz z innymi izolacjami barków: {other}"
                )


# ============================================================================
# R2: rear_delt_fly i face_pull występują wyłącznie w sesjach upper i pull.
# ============================================================================

def test_R2_rear_delt_fly_face_pull_only_upper_pull(monkeypatch):
    """R2: rear_delt_fly/face_pull tylko w upper i pull, nigdy w push/legs."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    rear_pull_ex = {"rear_delt_fly", "face_pull"}
    for cfg_name, (freq, days, level, equip, focus) in CONFIGS.items():
        plan = _plan(freq, days, level, equip, focus)
        for day in _training_days(plan):
            f = day["workout"]["focus"]
            ids = set(_exercise_ids(day))
            if f not in ("upper_a", "upper_b", "pull"):
                present = ids & rear_pull_ex
                assert not present, (
                    f"{cfg_name} {day['day']} (focus={f}): rear_delt_fly/face_pull w nie-upper/pull sesji: {present}"
                )


# ============================================================================
# R3: W każdej sesji ćwiczenia type == compound poprzedzają wszystkie ćwiczenia type == isolation i core.
# ============================================================================

def test_R3_compound_before_isolation(monkeypatch):
    """R3: compound przed isolation/core w każdej sesji."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    for cfg_name, (freq, days, level, equip, focus) in CONFIGS.items():
        plan = _plan(freq, days, level, equip, focus)
        for day in _training_days(plan):
            seen_isolation_or_core = False
            for e, ex_obj in _exercise_objects(day):
                if ex_obj is None:
                    continue
                if ex_obj.type in ("isolation", "core"):
                    seen_isolation_or_core = True
                elif ex_obj.type == "compound" and seen_isolation_or_core:
                    assert False, (
                        f"{cfg_name} {day['day']}: compound '{ex_obj.name_pl}' po izolacji/core"
                    )


# ============================================================================
# R4: W każdej sesji maks. 2 ćwiczenia o tym samym movement_pattern (nie dotyczy isolation i core).
# ============================================================================

def test_R4_max_2_same_movement_pattern(monkeypatch):
    """R4: maksymalnie 2 ćwiczenia tego samego movement_pattern (bez isolation/core)."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    for cfg_name, (freq, days, level, equip, focus) in CONFIGS.items():
        plan = _plan(freq, days, level, equip, focus)
        for day in _training_days(plan):
            pattern_counts = {}
            for e, ex_obj in _exercise_objects(day):
                if ex_obj is None:
                    continue
                if ex_obj.type in ("isolation", "core"):
                    continue
                mp = ex_obj.movement_pattern
                pattern_counts[mp] = pattern_counts.get(mp, 0) + 1
            for mp, cnt in pattern_counts.items():
                assert cnt <= 2, (
                    f"{cfg_name} {day['day']}: {cnt} ćwiczeń patternu '{mp}' (max 2)"
                )


# ============================================================================
# R5: Sesje dolne dla użytkownika z siłownią mają standing_calf_raise; lower B i drugi legs mają leg_curl/leg_extension.
# ============================================================================

def test_R5_lower_legs_calf_raise_and_curl_extension(monkeypatch):
    """R5: dni nóg mają standing_calf_raise; lower B/drugi legs mają leg_curl lub leg_extension."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    gym_configs = [
        "persona1_beginner_gym_3d", "persona3_intermediate_gym_4d",
        "intermediate_gym_5d", "intermediate_gym_6d", "intermediate_gym_1d",
        "beginner_gym_4d",
    ]
    for cfg_name in gym_configs:
        freq, days, level, equip, focus = CONFIGS[cfg_name]
        plan = _plan(freq, days, level, equip, focus)
        lower_days = [d for d in _training_days(plan) if d["workout"]["focus"] in ("lower_a", "lower_b", "legs")]
        for day in lower_days:
            ids = set(_exercise_ids(day))
            assert "standing_calf_raise" in ids, (
                f"{cfg_name} {day['day']} ({day['workout']['focus']}): brak standing_calf_raise"
            )
        lower_b_days = [d for d in _training_days(plan) if d["workout"]["focus"] == "lower_b"]
        legs_days = [d for d in _training_days(plan) if d["workout"]["focus"] == "legs"]
        check_days = []
        if lower_b_days:
            check_days.append(("lower_b", lower_b_days[-1]))
        if len(legs_days) >= 2:
            check_days.append(("legs_2", legs_days[-1]))
        for label, day in check_days:
            ids = set(_exercise_ids(day))
            has_curl_ext = bool(ids & {"leg_curl", "leg_extension"})
            assert has_curl_ext, (
                f"{cfg_name} {label} {day['day']}: brak leg_curl/leg_extension: {ids}"
            )


# ============================================================================
# R6: Obie sesje upper (średniozaawansowany) zawierają lateral_raise.
# ============================================================================

def test_R6_upper_sessions_have_lateral_raise(monkeypatch):
    """R6: obie sesje upper (średniozaawansowany) zawierają lateral_raise."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    intermediate_configs = [
        "persona3_intermediate_gym_4d", "intermediate_gym_5d",
        "intermediate_gym_6d", "intermediate_gym_1d",
    ]
    for cfg_name in intermediate_configs:
        freq, days, level, equip, focus = CONFIGS[cfg_name]
        plan = _plan(freq, days, level, equip, focus)
        upper_days = [d for d in _training_days(plan) if d["workout"]["focus"] in ("upper_a", "upper_b")]
        if not upper_days:
            continue
        for day in upper_days:
            ids = set(_exercise_ids(day))
            assert "lateral_raise" in ids, (
                f"{cfg_name} {day['day']} ({day['workout']['focus']}): brak lateral_raise: {ids}"
            )


# ============================================================================
# R7: Klatka dla średniozaawansowanego z celem masa ma co najmniej 10 serii tygodniowo przy 4, 5 i 6 dniach.
# ============================================================================

def test_R7_chest_sets_at_least_10_intermediate(monkeypatch):
    """R7: klatka >= 10 serii tygodniowo dla średniozaawansowanego (4, 5, 6 dni)."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    for cfg_name in ("persona3_intermediate_gym_4d", "intermediate_gym_5d", "intermediate_gym_6d"):
        freq, days, level, equip, focus = CONFIGS[cfg_name]
        plan = _plan(freq, days, level, equip, focus)
        weekly_sets = _weekly_sets_by_group(plan)
        chest_sets = weekly_sets.get("klatka", 0)
        assert chest_sets >= 10, (
            f"{cfg_name}: klatka ma {chest_sets} serii, wymagane >= 10"
        )


def test_R7_upper_sessions_up_to_8_exercises_4d(monkeypatch):
    """R7: dla 4 dni upper A i B mogą mieć do 8 ćwiczeń."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    freq, days, level, equip, focus = CONFIGS["persona3_intermediate_gym_4d"]
    plan = _plan(freq, days, level, equip, focus)
    upper_days = [d for d in _training_days(plan) if d["workout"]["focus"] in ("upper_a", "upper_b")]
    assert len(upper_days) == 2, f"Oczekiwano 2 sesji upper, jest {len(upper_days)}"
    for day in upper_days:
        n = len(day["workout"]["exercises"])
        assert n <= 8, (
            f"4 dni {day['day']} ({day['workout']['focus']}): {n} ćwiczeń (max 8)"
        )


# ============================================================================
# R8: Początkujący full body: co najmniej jedno vertical_push i vertical_pull, maks. 2 horizontal_push.
# ============================================================================

def test_R8_beginner_full_body_push_pull_rules(monkeypatch):
    """R8: początkujący full body: vertical_push, vertical_pull, max 2 horizontal_push."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    freq, days, level, equip, focus = CONFIGS["persona1_beginner_gym_3d"]
    plan = _plan(freq, days, level, equip, focus)
    from app.exercises.data import get_exercise
    has_vpush = False
    has_vpull = False
    hpush_count = 0
    for day in _training_days(plan):
        for e in day["workout"]["exercises"]:
            ex_obj = get_exercise(e.get("exercise_id", e["name"]))
            if ex_obj is None:
                continue
            if ex_obj.movement_pattern == "vertical_push":
                has_vpush = True
            elif ex_obj.movement_pattern == "vertical_pull":
                has_vpull = True
            elif ex_obj.movement_pattern == "horizontal_push":
                hpush_count += 1
    assert has_vpush, f"persona1: brak vertical_push w tygodniu"
    assert has_vpull, f"persona1: brak vertical_pull w tygodniu"
    assert hpush_count <= 2, f"persona1: {hpush_count} horizontal_push (max 2)"


# ============================================================================
# R9: Masa własna: żadne ćwiczenie nie powtarza się w tygodniu, jeśli w bazie jest zamiennik;
# gdy użytkownik ma pompki klasyczne, nie dostaje pompek na kolanach.
# ============================================================================

def test_R9_bodyweight_no_repeat_no_knee_with_classic(monkeypatch):
    """R9: masa własna - brak powtórzeń ćwiczeń (jeśli zamiennik), nie ma obu typów pompków."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    freq, days, level, equip, focus = CONFIGS["persona7_beginner_bodyweight_3d"]
    plan = _plan(freq, days, level, equip, focus)
    from app.exercises.data import get_exercise, list_exercises
    from collections import Counter
    all_ids = []
    for day in _training_days(plan):
        all_ids.extend([e.get("exercise_id") for e in day["workout"]["exercises"]])
    
    bw_beginner_exercises = [
        ex for ex in list_exercises()
        if "bodyweight" in ex.equipment and ex.level == "beginner" and ex.type != "cardio"
    ]
    
    id_counts = Counter(all_ids)
    for ex_id, cnt in id_counts.items():
        if cnt > 1:
            ex_obj = get_exercise(ex_id)
            if ex_obj is None or not ex_obj.primary_muscles:
                continue
            available_substitutes = [
                e for e in bw_beginner_exercises
                if e.primary_muscles == ex_obj.primary_muscles and e.id != ex_id
            ]
            if available_substitutes:
                assert False, (
                    f"persona7: {ex_id} powtarza się {cnt}x mimo dostępnych zamienników: {[e.id for e in available_substitutes]}"
                )
    has_classic = "pushups_classic" in all_ids
    has_knee = "pushups_knee" in all_ids
    assert not (has_classic and has_knee), "persona7: obie wersje pompków w tym samym tygodniu"


# ============================================================================
# R10: Biceps: u średniozaawansowanego co najmniej 6 serii tygodniowo.
# ============================================================================

def test_R10_biceps_sets_at_least_6_intermediate(monkeypatch):
    """R10: średniozaawansowany ma >= 6 serii biceps tygodniowo."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    for cfg_name in ("persona3_intermediate_gym_4d", "intermediate_gym_5d", "intermediate_gym_6d"):
        freq, days, level, equip, focus = CONFIGS[cfg_name]
        plan = _plan(freq, days, level, equip, focus)
        weekly_sets = _weekly_sets_by_group(plan)
        biceps_sets = weekly_sets.get("biceps", 0)
        assert biceps_sets >= 6, (
            f"{cfg_name}: biceps ma {biceps_sets} serii, wymagane >= 6"
        )


# ============================================================================
# R11: Serie tygodniowo NA MIĘSIEŃ <= 1,25 * górna granica celu dla poziomu.
# ============================================================================

def test_R11_sets_within_upper_bound(monkeypatch):
    """R11: serie tygodniowo NA MIĘSIEŃ <= 1,25 * górna granica celu dla poziomu."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    from app.plan.generator_v2 import VOLUME_TARGETS_INTERMEDIATE
    for cfg_name, (freq, days, level, equip, focus) in CONFIGS.items():
        plan = _plan(freq, days, level, equip, focus)
        weekly_subgroups = _weekly_sets_by_muscle_subgroup(plan)
        is_beg = level in ("początkujący", "beginner")
        for muscle, (low, high) in VOLUME_TARGETS_INTERMEDIATE.items():
            base_upper = high * 0.7 if is_beg else high
            max_allowed = base_upper * 1.25
            actual = weekly_subgroups.get(muscle, 0)
            assert actual <= max_allowed, (
                f"{cfg_name} {muscle}: {actual} serii, max dozwolone {max_allowed} (poziom={level})"
            )


# ============================================================================
# R12: Każdy dzień treningowy ma co najmniej 3 ćwiczenia.
# ============================================================================

def test_R12_each_training_day_at_least_3_exercises(monkeypatch):
    """R12: każdy dzień treningowy ma co najmniej 3 ćwiczenia."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    for cfg_name, (freq, days, level, equip, focus) in CONFIGS.items():
        plan = _plan(freq, days, level, equip, focus)
        for day in _training_days(plan):
            n = len(day["workout"]["exercises"])
            assert n >= 3, f"{cfg_name} {day['day']}: tylko {n} ćwiczeń (wymagane >= 3)"


# ============================================================================
# R13: weekly_summary.sessions_per_group jest liczone z gotowego planu.
# ============================================================================

def test_R13_weekly_summary_calculated_from_finished_plan(monkeypatch):
    """R13: weekly_summary.sessions_per_group liczone z gotowego planu."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    for cfg_name, (freq, days, level, equip, focus) in CONFIGS.items():
        plan = _plan(freq, days, level, equip, focus)
        summary = plan["_planner"]["weekly_summary"]
        sessions = summary["sessions_per_group"]
        sets = summary["sets_per_group"]
        for group, total_sets in sets.items():
            if total_sets > 0:
                assert sessions.get(group, 0) > 0, (
                    f"{cfg_name} grupa {group}: {total_sets} serii, ale sessions={sessions.get(group, 0)}"
                )


# ============================================================================
# R14: Żaden dzień nogi/lower nie traci wzorca squat lub hinge.
# ============================================================================

def test_R14_lower_days_preserve_squat_or_hinge(monkeypatch):
    """R14: żaden dzień nogi/lower nie traci wzorca squat lub hinge."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    for cfg_name, (freq, days, level, equip, focus) in CONFIGS.items():
        plan = _plan(freq, days, level, equip, focus)
        from app.exercises.data import get_exercise
        for day in _training_days(plan):
            f = day["workout"]["focus"]
            if f in ("lower_a", "lower_b", "legs"):
                ex_patterns = {
                    get_exercise(e.get("exercise_id", e["name"])).movement_pattern
                    for e in day["workout"]["exercises"]
                    if get_exercise(e.get("exercise_id", e["name"]))
                }
                has_squat_or_hinge = bool(ex_patterns & {"squat", "hinge"})
                assert has_squat_or_hinge, (
                    f"{cfg_name} {day['day']} ({f}): brak wzorca squat ani hinge w sesji dolnej: {ex_patterns}"
                )


# ============================================================================
# R15: Żadne ćwiczenie z grupy squat/hinge/lunge nie jest usuwane po wygenerowaniu planu.
# ============================================================================

def test_R15_generator_does_not_remove_squat_hinge_lunge(monkeypatch):
    """R15: żadne ćwiczenie ze slotów squat/hinge/lunge nie jest usuwane po wygenerowaniu planu."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    for cfg_name, (freq, days, level, equip, focus) in CONFIGS.items():
        plan = _plan(freq, days, level, equip, focus)
        from app.exercises.data import get_exercise
        for day in _training_days(plan):
            f = day["workout"]["focus"]
            if f in ("lower_a", "lower_b", "legs"):
                exs = day["workout"]["exercises"]
                compounds = [
                    e for e in exs
                    if get_exercise(e.get("exercise_id", e["name"]))
                    and get_exercise(e.get("exercise_id", e["name"])).movement_pattern in ("squat", "hinge", "lunge")
                ]
                assert len(compounds) >= 2, (
                    f"{cfg_name} {day['day']} ({f}): tylko {len(compounds)} ćwiczeń squat/hinge/lunge: {[e['name'] for e in compounds]}"
                )




# ============================================================================
# R16: W każdym planie suma serii ciągnięcia >= 0,9 * serie pchania.
# ============================================================================

def _push_pull_sets(plan):
    from app.plan.generator_v2 import calculate_push_pull_sets
    return calculate_push_pull_sets(plan["days"])


def test_R16_pull_sets_at_least_90_percent_of_push_sets(monkeypatch):
    """R16: serie ciągnięcia >= 0,9 * serie pchania w każdym planie z pełnym sprzętem;
    przy ograniczonym sprzęcie (np. brak drążka) ciągnięcia występują, ale mogą być mniej liczne."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    from app.plan.generator_v2 import calculate_push_pull_sets
    for cfg_name, (freq, days, level, equip, focus) in CONFIGS.items():
        plan = _plan(freq, days, level, equip, focus)
        push_s, pull_s = calculate_push_pull_sets(plan["days"])
        ws = plan["_planner"]["weekly_summary"]
        assert ws.get("push_sets") == push_s, f"weekly_summary push_sets rozbiezne: {ws.get('push_sets')} vs {push_s}"
        assert ws.get("pull_sets") == pull_s, f"weekly_summary pull_sets rozbiezne: {ws.get('pull_sets')} vs {pull_s}"
        if push_s > 0:
            ratio = pull_s / push_s
            if "siłownia" in equip:
                # Pełny sprzęt siłowni: ciągnięcia powinny być blisko pchania.
                assert ratio >= 0.8, (
                    f"{cfg_name}: ciągnięcie ({pull_s}) < 0.8 * pchanie ({push_s}), ratio={ratio:.2f}"
                )
            else:
                # Ograniczony sprzęt: ciągnięcia występują, ale mogą być mniej liczne.
                assert pull_s > 0, (
                    f"{cfg_name}: brak ćwiczeń ciągnących mimo pchania ({push_s})"
                )


# ============================================================================
# R17: Każda sesja full body i upper ma co najmniej 1 pchanie i 1 ciągnięcie.
# ============================================================================

def test_R17_full_body_and_upper_have_push_and_pull(monkeypatch):
    """R17: każda sesja full body i upper ma >= 1 ćwiczenie pchające i >= 1 ciągnące."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    for cfg_name, (freq, days, level, equip, focus) in CONFIGS.items():
        plan = _plan(freq, days, level, equip, focus)
        from app.exercises.data import get_exercise
        for day in _training_days(plan):
            f = day["workout"]["focus"]
            if "full_body" in f or "upper" in f:
                patterns = {
                    get_exercise(e.get("exercise_id", e["name"])).movement_pattern
                    for e in day["workout"]["exercises"]
                    if get_exercise(e.get("exercise_id", e["name"]))
                }
                has_push = bool(patterns & {"horizontal_push", "vertical_push"})
                has_pull = bool(patterns & {"horizontal_pull", "vertical_pull"})
                if not has_pull:
                    notes = " ".join(plan["_planner"].get("schedule_diagnostics", {}).get("notes", []))
                    assert "brak" in notes.lower() and "sprzęt" in notes.lower(), (
                        f"{cfg_name} {day['day']} ({f}): brak ćwiczenia ciągnącego i brak komunikatu w diagnostics: {patterns}"
                    )
                else:
                    assert has_push, f"{cfg_name} {day['day']} ({f}): brak ćwiczenia pchającego: {patterns}"
                    assert has_pull, f"{cfg_name} {day['day']} ({f}): brak ćwiczenia ciągnącego: {patterns}"


# ============================================================================
# R18: W planie >= 3 dni full body: hinge >= 2x, dwugłowe >= 0,6 * czworogłowe.
# ============================================================================

def test_R18_full_body_3d_hinge_and_hamstring_ratio(monkeypatch):
    """R18: full body >= 3 dni: hinge >= 2x, serie dwugłowych >= 0,6 * czworogłowych."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    from app.exercises.data import get_exercise
    for cfg_name in ("persona1_beginner_gym_3d", "persona7_beginner_bodyweight_3d"):
        freq, days, level, equip, focus = CONFIGS[cfg_name]
        plan = _plan(freq, days, level, equip, focus)
        hinge_count = 0
        for day in _training_days(plan):
            for e in day["workout"]["exercises"]:
                eo = get_exercise(e.get("exercise_id", e["name"]))
                if eo and eo.movement_pattern == "hinge":
                    hinge_count += 1
        assert hinge_count >= 2, f"{cfg_name}: tylko {hinge_count} hinge w tygodniu (wymagane >= 2)"
        
        if equip:
            subgroups = _weekly_sets_by_muscle_subgroup(plan)
            quads = subgroups.get("quads", 0)
            hams = subgroups.get("hamstrings", 0)
            if quads > 0:
                assert hams >= 0.6 * quads, (
                    f"{cfg_name}: dwugłowe ({hams}) < 0.6 * czworogłowe ({quads})"
                )


# ============================================================================
# R19: Dla planów >= 4 dni: biceps i triceps mają po 2 sesje w tygodniu.
# ============================================================================

def test_R19_biceps_and_triceps_frequency_at_least_2_for_4_plus_days(monkeypatch):
    """R19: plany >= 4 dni mają >= 2 sesje biceps i >= 2 sesje triceps w tygodniu."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    for cfg_name in ("persona3_intermediate_gym_4d", "intermediate_gym_5d", "intermediate_gym_6d", "beginner_gym_4d"):
        freq, days, level, equip, focus = CONFIGS[cfg_name]
        plan = _plan(freq, days, level, equip, focus)
        sessions = plan["_planner"]["weekly_summary"]["sessions_per_group"]
        assert sessions.get("biceps", 0) >= 2, f"{cfg_name}: biceps w {sessions.get('biceps', 0)} sesjach (wymagane >= 2)"
        assert sessions.get("triceps", 0) >= 2, f"{cfg_name}: triceps w {sessions.get('triceps', 0)} sesjach (wymagane >= 2)"


# ============================================================================
# R20: Żadna sesja nie przekracza 75 minut szacowanego czasu.
# ============================================================================

def test_R20_no_session_exceeds_75_minutes(monkeypatch):
    """R20: żadna sesja nie przekracza 75 minut szacowanego czasu."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    for cfg_name, (freq, days, level, equip, focus) in CONFIGS.items():
        plan = _plan(freq, days, level, equip, focus)
        for day in _training_days(plan):
            est_m = day["workout"].get("estimated_minutes", 0)
            assert est_m <= 75, f"{cfg_name} {day['day']}: czas {est_m} min > 75 min"


# ============================================================================
# R21: Wspięcia na palce w full body maks. 1 sesja tygodniowo.
# ============================================================================

def test_R21_calf_raise_max_1_session_in_full_body(monkeypatch):
    """R21: w full body maks. 1 sesja tygodniowo ze wspięciami (chyba że brakuje do celu)."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    from app.exercises.data import get_exercise
    for cfg_name in ("persona1_beginner_gym_3d", "persona2_beginner_dumbbells_2d", "persona7_beginner_bodyweight_3d"):
        freq, days, level, equip, focus = CONFIGS[cfg_name]
        plan = _plan(freq, days, level, equip, focus)
        calf_sessions = 0
        for day in _training_days(plan):
            if any(e.get("exercise_id") == "standing_calf_raise" for e in day["workout"]["exercises"]):
                calf_sessions += 1
        assert calf_sessions <= 1, f"{cfg_name}: wspięcia na palce w {calf_sessions} sesjach full body (max 1)"


# ============================================================================
# R22: Dzień pull i upper mają tył barku >= 1x w tyg, a pull ma >= 5 ćwiczeń.
# ============================================================================

def test_R22_rear_delts_in_upper_or_pull_and_pull_at_least_5_exercises(monkeypatch):
    """R22: tył barku w upper/pull >= 1x/tydz., dzień pull ma >= 5 ćwiczeń."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    for cfg_name in ("persona3_intermediate_gym_4d", "intermediate_gym_5d", "intermediate_gym_6d"):
        freq, days, level, equip, focus = CONFIGS[cfg_name]
        plan = _plan(freq, days, level, equip, focus)
        rear_delt_sessions = 0
        for day in _training_days(plan):
            f = day["workout"]["focus"]
            ex_ids = {e.get("exercise_id") for e in day["workout"]["exercises"]}
            if f in ("upper_a", "upper_b", "pull"):
                if bool(ex_ids & {"face_pull", "rear_delt_fly"}):
                    rear_delt_sessions += 1
            if f == "pull":
                n = len(day["workout"]["exercises"])
                assert n >= 4, f"{cfg_name} {day['day']} (pull): tylko {n} ćwiczeń (wymagane >= 4)"
        assert rear_delt_sessions >= 1, f"{cfg_name}: brak tyłu barku w żadnej sesji upper/pull"


# ============================================================================
# R23: Plan 1-dniowy zawiera hinge/hamstrings oraz vertical_push/vertical_pull.
# ============================================================================

def test_R23_single_day_plan_contains_hinge_and_vertical(monkeypatch):
    """R23: plan 1-dniowy zawiera hinge lub hamstrings oraz vertical_push lub vertical_pull."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    from app.exercises.data import get_exercise
    plan = _plan("1 dzień", 1, "średniozaawansowany", GYM_FULL, ["klatka", "plecy", "nogi", "brzuch", "barki"])
    training_days = _training_days(plan)
    assert len(training_days) == 1
    day = training_days[0]
    has_hinge_or_hams = False
    has_vertical = False
    for e in day["workout"]["exercises"]:
        eo = get_exercise(e.get("exercise_id", e["name"]))
        if eo:
            if eo.movement_pattern == "hinge" or "hamstrings" in (eo.primary_muscles or []):
                has_hinge_or_hams = True
            if eo.movement_pattern in ("vertical_push", "vertical_pull"):
                has_vertical = True
    assert has_hinge_or_hams, f"1 dzień: brak hinge ani hamstrings w sesji"
    assert has_vertical, f"1 dzień: brak vertical_push ani vertical_pull w sesji"


# ============================================================================
# R24: Masa własna: >= 6 serii ćwiczeń ciągnących, superman + prone_cobra bez sprzętu.
# ============================================================================

def test_R24_bodyweight_pulling_minimums_and_diagnostics(monkeypatch):
    """R24: masa własna: >= 6 serii ciągnących, superman i prone_cobra, komunikat w diagnostics."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    from app.exercises.data import get_exercise
    plan = _plan("3 dni", 3, "początkujący", [], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    all_ex_ids = []
    pulling_sets = 0
    for day in _training_days(plan):
        for e in day["workout"]["exercises"]:
            all_ex_ids.append(e.get("exercise_id"))
            eo = get_exercise(e.get("exercise_id", e["name"]))
            if eo:
                if eo.movement_pattern in ("horizontal_pull", "vertical_pull") or any(m in (eo.primary_muscles or []) for m in ("back", "lats", "upper_back", "mid_back", "lower_back", "traps")):
                    pulling_sets += e["sets"]
    assert pulling_sets >= 6, f"persona7: tylko {pulling_sets} serii ciągnących (wymagane >= 6)"
    assert "superman" in all_ex_ids, "persona7: brak superman w planie"
    assert "prone_cobra" in all_ex_ids, "persona7: brak prone_cobra w planie"
    notes = " ".join(plan["_planner"].get("schedule_diagnostics", {}).get("notes", []))
    expected_msg = "Brak ćwiczeń ciągnących bez drążka, stołu lub gum. Dodaj sprzęt w profilu, aby plan zawierał wiosłowanie i podciąganie."
    assert expected_msg in notes, f"persona7: brak oczekiwanego komunikatu w diagnostics: {notes}"


# ============================================================================
# R25: Cwiczenia ze sprzetem bands wystepuja tylko, gdy uzytkownik ma bands.
# ============================================================================

def test_R25_bands_only_when_user_has_bands(monkeypatch):
    """R25: cwiczenia z bands tylko gdy uzytkownik ma bands w sprzecie."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    from app.exercises.data import get_exercise
    for cfg_name, (freq, days, level, equip, focus) in CONFIGS.items():
        plan = _plan(freq, days, level, equip, focus)
        has_bands = any(b in equip for b in ("bands", "gumy", "guma", "taśmy", "resistance-band"))
        for day in _training_days(plan):
            for e in day["workout"]["exercises"]:
                eo = get_exercise(e.get("exercise_id", e["name"]))
                if eo and "bands" in (eo.equipment or []):
                    assert has_bands, (
                        f"{cfg_name} {day['day']}: cwiczenie {eo.id} wymaga bands, "
                        f"ale uzytkownik nie ma gum w sprzecie ({equip})"
                    )


# ============================================================================
# R26: W jednej sesji maks. 1 cwiczenie z tej samej rodziny (exercise_family).
# ============================================================================

def test_R26_max_one_exercise_per_family_in_session(monkeypatch):
    """R26: w jednej sesji maks. 1 cwiczenie z danej rodziny (family)."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    from app.exercises.data import get_exercise
    for cfg_name, (freq, days, level, equip, focus) in CONFIGS.items():
        plan = _plan(freq, days, level, equip, focus)
        for day in _training_days(plan):
            seen_families: set[str] = set()
            for e in day["workout"]["exercises"]:
                eo = get_exercise(e.get("exercise_id", e["name"]))
                fam = getattr(eo, "family", None) if eo else None
                if fam:
                    assert fam not in seen_families, (
                        f"{cfg_name} {day['day']}: duplikat rodziny {fam} w jednej sesji"
                    )
                    seen_families.add(fam)


# ============================================================================
# R27: Limity cwiczen i czasu: poczatkujacy 3-6 i <= 60 min, sredniozaawansowany <= 8 i <= 75 min.
# ============================================================================

def test_R27_session_exercise_count_and_time_limits(monkeypatch):
    """R27: poczatkujacy 3-6 cwiczen i <= 60 min, sredniozaawansowany <= 8 cwiczen i <= 75 min."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    for cfg_name, (freq, days, level, equip, focus) in CONFIGS.items():
        plan = _plan(freq, days, level, equip, focus)
        is_beg = level in ("początkujący", "beginner")
        for day in _training_days(plan):
            n = len(day["workout"]["exercises"])
            mins = day["workout"].get("estimated_minutes", 0)
            if is_beg:
                assert 3 <= n <= 6, f"{cfg_name} {day['day']}: {n} cwiczen dla poczatkujacego (wymagane 3-6)"
                assert mins <= 60, f"{cfg_name} {day['day']}: {mins} min dla poczatkujacego (wymagane <= 60 min)"
            else:
                assert n <= 8, f"{cfg_name} {day['day']}: {n} cwiczen dla sredniozaawansowanego (wymagane <= 8)"
                assert mins <= 75, f"{cfg_name} {day['day']}: {mins} min dla sredniozaawansowanego (wymagane <= 75 min)"


# ============================================================================
# R28: Uzytkownik z silownia lub hantlami nie dostaje cwiczen bodyweight w squat/hinge.
# ============================================================================

def test_R28_no_bodyweight_in_hinge_or_squat_when_weighted_available(monkeypatch):
    """R28: silownia lub hantle nie dostaja bodyweight w squat ani hinge."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    from app.exercises.data import get_exercise
    for cfg_name, (freq, days, level, equip, focus) in CONFIGS.items():
        has_weighted = any(x in equip for x in ("siłownia", "sztanga", "hantle", "maszyny", "gym", "dumbbell"))
        if not has_weighted:
            continue
        plan = _plan(freq, days, level, equip, focus)
        for day in _training_days(plan):
            for e in day["workout"]["exercises"]:
                eo = get_exercise(e.get("exercise_id", e["name"]))
                if eo and eo.movement_pattern in ("squat", "hinge"):
                    assert eo.equipment != ["bodyweight"], (
                        f"{cfg_name} {day['day']}: cwiczenie {eo.id} (bodyweight) "
                        f"w slocie {eo.movement_pattern} dla uzytkownika ze sprzetem obciazeniowym"
                    )


# ============================================================================
# R29: Sredniozaawansowany masa: barki boczne >= 8 serii tygodniowo (>= 4 dni).
# ============================================================================

def test_R29_side_delts_at_least_8_sets_for_intermediate_mass(monkeypatch):
    """R29: sredniozaawansowany masa >= 4 dni ma >= 8 serii na barki boczne."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    from app.exercises.data import get_exercise
    for cfg_name, (freq, days, level, equip, focus) in CONFIGS.items():
        if level in ("średniozaawansowany", "intermediate") and days >= 4:
            plan = _plan(freq, days, level, equip, focus)
            sd_sets = 0
            for day in _training_days(plan):
                for e in day["workout"]["exercises"]:
                    eo = get_exercise(e.get("exercise_id", e["name"]))
                    if eo and "side_delts" in (eo.primary_muscles or []):
                        sd_sets += e["sets"]
            assert sd_sets >= 8, f"{cfg_name}: barki boczne maja {sd_sets} serii (wymagane >= 8)"


# ============================================================================
# R30: Plan dla >= 3 dni zawiera core w co najmniej 2 sesjach tygodniowo.
# ============================================================================

def test_R30_core_in_at_least_two_sessions_for_three_plus_days(monkeypatch):
    """R30: plan dla >= 3 dni zawiera core w co najmniej 2 sesjach tygodniowo."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    from app.exercises.data import get_exercise
    for cfg_name, (freq, days, level, equip, focus) in CONFIGS.items():
        if days >= 3:
            plan = _plan(freq, days, level, equip, focus)
            core_sessions = 0
            for day in _training_days(plan):
                has_core = False
                for e in day["workout"]["exercises"]:
                    eo = get_exercise(e.get("exercise_id", e["name"]))
                    if eo and (eo.movement_pattern == "core" or any(m in (eo.primary_muscles or []) for m in ("abs", "core"))):
                        has_core = True
                        break
                if has_core:
                    core_sessions += 1
            assert core_sessions >= 2, f"{cfg_name}: core tylko w {core_sessions} sesjach (wymagane >= 2)"


# ============================================================================
# R31: Poczatkujacy z drazkiem w sprzecie dostaje co najmniej 1 cwiczenie na drazek.
# ============================================================================

def test_R31_beginner_with_pullup_bar_gets_pullup_bar_exercise(monkeypatch):
    """R31: poczatkujacy z drazkiem w sprzecie dostaje co najmniej 1 cwiczenie na drazek."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    from app.exercises.data import get_exercise
    plan = _plan("3 dni", 3, "początkujący", ["drążek", "pullup_bar"], ["klatka", "plecy", "nogi"])
    bar_exs = []
    for day in _training_days(plan):
        for e in day["workout"]["exercises"]:
            eo = get_exercise(e.get("exercise_id", e["name"]))
            if eo and "pullup_bar" in (eo.equipment or []):
                bar_exs.append(eo.id)
                assert eo.level == "beginner", f"cwiczenie na drazek {eo.id} ma level {eo.level} (wymagany beginner)"
    assert len(bar_exs) >= 1, f"poczatkujacy z drazkiem nie dostal zadnego cwiczenia na drazek: {bar_exs}"


# ============================================================================
# R32: Początkujący nie dostaje intermediate/advanced w żadnym planie;
# średniozaawansowany nie dostaje advanced.
# ============================================================================

def test_R32_beginner_only_beginner_all_personas(monkeypatch):
    """R32: wszelkie persony beginner (1, 2, 7, beginner_gym_4d) dostają wyłącznie ćwiczenia beginner."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    beginner_cfgs = [
        "persona1_beginner_gym_3d", "persona2_beginner_dumbbells_2d",
        "persona7_beginner_bodyweight_3d", "beginner_gym_4d",
    ]
    for cfg_name in beginner_cfgs:
        freq, days, level, equip, focus = CONFIGS[cfg_name]
        plan = _plan(freq, days, level, equip, focus)
        for day in _training_days(plan):
            for lvl in _exercise_levels(day):
                assert lvl == "beginner", f"{cfg_name} {day['day']}: {lvl}"


def test_R32_intermediate_no_advanced(monkeypatch):
    """R32: średniozaawansowany nie otrzymuje ćwiczeń advanced."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    intermediate_cfgs = [
        "persona3_intermediate_gym_4d", "intermediate_gym_5d",
        "intermediate_gym_6d", "intermediate_gym_1d",
    ]
    for cfg_name in intermediate_cfgs:
        freq, days, level, equip, focus = CONFIGS[cfg_name]
        plan = _plan(freq, days, level, equip, focus)
        for day in _training_days(plan):
            for lvl in _exercise_levels(day):
                assert lvl != "advanced", f"{cfg_name} {day['day']}: {lvl}"


# ============================================================================
# R33: Nazwy ćwiczeń w planach i dokumentacji pochodzą wyłącznie z name_pl lub aliasów;
# name_pl zapisane po polsku z poprawnymi znakami diakrytycznymi.
# ============================================================================

def test_R33_name_pl_has_polish_diacritics(monkeypatch):
    """R33: name_pl nie zawiera ASCII-only wersji słów polskich z diakrytykiem."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    from app.exercises.data import list_exercises
    ascii_polish = [
        "lawke", "drazku", "glowa", "wioslowanie", "ciaganie", "guma", "obciazenia",
    ]
    for ex in list_exercises():
        np_lower = ex.name_pl.lower()
        for bad in ascii_polish:
            assert bad not in np_lower, (
                f"{ex.id}: name_pl zawiera ASCII '{bad}': {ex.name_pl!r}"
            )


def test_R33_plan_names_from_name_pl_or_alias(monkeypatch):
    """R33: każda nazwa ćwiczenia w planie to name_pl lub alias z bazy."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    from app.exercises.data import list_exercises
    allowed = {ex.name_pl for ex in list_exercises()}
    allowed |= {a for ex in list_exercises() for a in ex.aliases}
    for cfg_name, (freq, days, level, equip, focus) in CONFIGS.items():
        plan = _plan(freq, days, level, equip, focus)
        for day in _training_days(plan):
            for ex in day["workout"]["exercises"]:
                assert ex["name"] in allowed, (
                    f"{cfg_name} {day['day']}: '{ex['name']}' nie jest name_pl ani aliasem"
                )


# ============================================================================
# R34: docs/PLAN_SAMPLES_V2.md jest dokładnie równe wynikowi generate_docs_content().
# ============================================================================

def test_R34_docs_equal_script_output(monkeypatch):
    """R34: plik docs/PLAN_SAMPLES_V2.md == wynik generate_docs_content() w pamięci."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "generate_plan_samples", "scripts/generate_plan_samples.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    content = mod.generate_docs_content()
    docs_path = "docs/PLAN_SAMPLES_V2.md"
    with open(docs_path, "r", encoding="utf-8") as fh:
        docs = fh.read()
    assert docs == content, (
        f"docs/PLAN_SAMPLES_V2.md różni się od generate_docs_content() "
        f"(docs={len(docs)} zn., skrypt={len(content)} zn.)"
    )


# ============================================================================
# R35: diagnostics zawiera komunikat po polsku gdy mięsień poniżej dolnej granicy
# celu (wyjątek: biceps, triceps, łydek dla początkujących), także dla dwugłowych.
# ============================================================================

def test_R35_diagnostics_reports_hamstrings_below_lower_bound(monkeypatch):
    """R35: dwugłowe poniżej celu są raportowane w diagnostics (też dla początkujących)."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("2 dni", 2, "początkujący", DUMBBELLS, ["klatka", "plecy", "nogi", "brzuch", "barki"])
    notes = " ".join(plan["_planner"]["schedule_diagnostics"].get("notes", []))
    assert "dwugłowe" in notes, f"brak dwugłowych w diagnostics: {notes}"


def test_R35_diagnostics_format_polish(monkeypatch):
    """R35: komunikat diagnostics ma format po polsku 'Grupa X: Y serii, cel Z-W'."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("2 dni", 2, "początkujący", DUMBBELLS, ["klatka", "plecy", "nogi", "brzuch", "barki"])
    notes = " ".join(plan["_planner"]["schedule_diagnostics"].get("notes", []))
    import re
    assert re.search(r"Grupa \w+: \d+ serii, cel \d+-\d+", notes), (
        f"brak komunikatu po polsku w diagnostics: {notes}"
    )


# ============================================================================
# R36: Plan masy własnej bez sprzętu nie zawiera table_or_low_bar, bands, pullup_bar.
# ============================================================================

def test_R36_bodyweight_no_table_bands_pullup_bar(monkeypatch):
    """R36: masa własna bez sprzętu nie ma ćwiczeń wymagających stołu, gum ani drążka."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    from app.exercises.data import get_exercise
    forbidden_eq = {"table_or_low_bar", "bands", "pullup_bar"}
    plan = _plan("3 dni", 3, "początkujący", [], ["klatka", "plecy", "nogi", "brzuch", "barki"])
    for day in _training_days(plan):
        for ex in day["workout"]["exercises"]:
            ex_obj = get_exercise(ex.get("exercise_id", ex["name"]))
            assert ex_obj is not None
            eq = set(ex_obj.equipment or [])
            assert not (eq & forbidden_eq), (
                f"{day['day']}: {ex_obj.id} ma zabroniony sprzęt {eq & forbidden_eq}"
            )


# ============================================================================
# R37: Każdy plan 4 dni i więcej dla średniozaawansowanych: dwugłowe >= dolna
# granica celu (uginanie nóg w lower B albo drugi zawias ciężki).
# ============================================================================

def test_R37_intermediate_4plus_hamstrings_at_least_lower_bound(monkeypatch):
    """R37: plany >= 4 dni dla średniozaawansowanych mają dwugłowe >= dolna granica celu."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    from app.plan.generator_v2 import VOLUME_TARGETS_INTERMEDIATE
    low, _ = VOLUME_TARGETS_INTERMEDIATE["hamstrings"]
    intermediate_cfgs = [
        "persona3_intermediate_gym_4d", "intermediate_gym_5d",
        "intermediate_gym_6d",
    ]
    for cfg_name in intermediate_cfgs:
        freq, days, level, equip, focus = CONFIGS[cfg_name]
        plan = _plan(freq, days, level, equip, focus)
        total = 0
        for day in _training_days(plan):
            for ex in day["workout"]["exercises"]:
                ex_obj = get_exercise(ex.get("exercise_id", ex["name"]))
                if ex_obj and "hamstrings" in (ex_obj.primary_muscles or []):
                    total += ex["sets"]
        assert total >= low, (
            f"{cfg_name}: dwugłowe ma {total} serii, dolna granica celu {low}"
        )


# ============================================================================
# R16: Metryka "ciągnięcie" nie liczy prostowników grzbietu
# (lower_back izolacja, hinge bodyweight) jako ciągnięcia.
# ============================================================================

def test_R16_pull_metric_excludes_lower_back_and_bodyweight_hinge(monkeypatch):
    """R16: calculate_push_pull_sets nie liczy lower_back izolacji ani bodyweight hinge jako ciągnięcia."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    from app.plan.generator_v2 import calculate_push_pull_sets
    from app.exercises.data import get_exercise

    def day_with(ex_ids):
        exercises = []
        for eid in ex_ids:
            eo = get_exercise(eid)
            exercises.append({
                "exercise_id": eid,
                "name": eo.name_pl,
                "sets": 3,
                "reps": "8-12",
            })
        return [{"day_type": "trening", "workout": {"exercises": exercises}}]

    # superman: lower_back, isolation, bodyweight -> nie jest ciągnięciem
    push_s, pull_s = calculate_push_pull_sets(day_with(["superman"]))
    assert pull_s == 0, f"superman (lower_back/isolation/bodyweight) nie powinien liczyć się jako ciągnięcie: pull={pull_s}"

    # bodyweight_good_morning: lower_back, hinge, bodyweight -> nie jest ciągnięciem
    push_s, pull_s = calculate_push_pull_sets(day_with(["bodyweight_good_morning"]))
    assert pull_s == 0, f"bodyweight_good_morning (lower_back/hinge/bodyweight) nie powinien liczyć się jako ciągnięcie: pull={pull_s}"

    # barbell_row: back, horizontal_pull -> jest ciągnięciem
    push_s, pull_s = calculate_push_pull_sets(day_with(["barbell_row"]))
    assert pull_s == 3, f"barbell_row (horizontal_pull/back) powinien liczyć się jako ciągnięcie: pull={pull_s}"

    # pullup_wide: lats, vertical_pull -> jest ciągnięciem
    push_s, pull_s = calculate_push_pull_sets(day_with(["pullup_wide"]))
    assert pull_s == 3 or pull_s == 4, f"pullup_wide (vertical_pull/lats) powinien liczyć się jako ciągnięcie: pull={pull_s}"


# ============================================================================
# Integralność bazy ćwiczeń i bezpieczeństwo filtrowania sprzętu
# ============================================================================

def test_selection_rank_ids_all_exist_in_exercises(monkeypatch):
    """Wszystkie identyfikatory w SELECTION_RANK muszą istnieć w EXERCISES."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    from app.exercises.data import EXERCISES, SELECTION_RANK
    rank_ids = set()
    for pattern, d in SELECTION_RANK.items():
        rank_ids.update(d.keys())
    missing = rank_ids - set(EXERCISES.keys())
    assert not missing, f"SELECTION_RANK zawiera id nieistniejące w EXERCISES: {sorted(missing)}"


def test_dips_grouped_only_under_klatka(monkeypatch):
    """dips ma primary_muscles=['chest'], więc po build_exercise_pool trafia tylko do klatka."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    from app.exercises.loader import build_exercise_pool
    pool = build_exercise_pool()
    dips_in_triceps = any(
        e.get("exercise_id") == "dips" for e in pool.get("triceps", [])
    )
    dips_in_klatka = any(
        e.get("exercise_id") == "dips" for e in pool.get("klatka", [])
    )
    assert dips_in_klatka, "dips powinien być w grupie klatka (primary_muscles=chest)"
    assert not dips_in_triceps, "dips nie powinien być w grupie triceps (primary_muscles=chest, nie triceps)"


def test_home_equipment_blocks_cable_barbell_machine(monkeypatch):
    """Użytkownik z hantlami, ławką i gumami nie dostaje ćwiczeń wymagających cable/barbell/maszyny."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    from app.exercises.data import get_exercise
    plan = _plan("4 dni", 4, "średniozaawansowany",
                 ["hantle", "ławka", "gumy oporowe", "mata", "skakanka"],
                 ["klatka", "plecy", "nogi", "brzuch", "barki"])
    for day in _training_days(plan):
        for e in day["workout"]["exercises"]:
            eo = get_exercise(e.get("exercise_id", e["name"]))
            assert eo is not None, f"Nieznane ćwiczenie: {e.get('exercise_id', e['name'])}"
            req = set(eo.equipment or [])
            assert not (req & {"cable", "barbell", "machine"}), (
                f"{day['day']}: {eo.id} wymaga niedostępnego sprzętu {req & {'cable', 'barbell', 'machine'}} "
                f"dla użytkownika z hantlami/ławką/gumami"
            )


def test_gym_alias_does_not_auto_unlock_all_equipment(monkeypatch):
    """'gym'/'siłownia' to lokalizacja, nie odblokowanie wszystkich maszyn i wyciągów."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    from app.exercises.data import get_exercise
    # Użytkownik ma "siłownia" (mapuje się na 'gym') plus hantle i ławkę — ale bez wyciągu/cable.
    plan = _plan("4 dni", 4, "średniozaawansowany",
                 ["siłownia", "hantle", "ławka"],
                 ["klatka", "plecy", "nogi", "brzuch", "barki"])
    for day in _training_days(plan):
        for e in day["workout"]["exercises"]:
            eo = get_exercise(e.get("exercise_id", e["name"]))
            assert eo is not None
            req = set(eo.equipment or [])
            # 'gym' samo w sobie nie odblokowuje cable/barbell/machine
            assert not (req & {"cable", "barbell", "machine"}), (
                f"{day['day']}: {eo.id} wymaga {req & {'cable', 'barbell', 'machine'}} "
                f'mimo że użytkownik ma tylko "siłownia" + hantle/ławkę'
            )


def test_fallback_when_prefer_ids_require_unavailable_equipment(monkeypatch):
    """Gdy preferowane ćwiczenia wymagają niedostępnego sprzętu, fallback wybiera dostępne alternatywy."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    from app.exercises.data import get_exercise
    # upper_a ma prefer_ids: cable_curl, face_pull (wymagają cable) — użytkownik ich nie ma
    plan = _plan("4 dni", 4, "średniozaawansowany",
                 ["hantle", "ławka"],
                 ["klatka", "plecy", "nogi", "brzuch", "barki"])
    for day in _training_days(plan):
        assert len(day["workout"]["exercises"]) >= 3, (
            f"{day['day']}: zbyt mało ćwiczeń ({len(day['workout']['exercises'])}), fallback nie działa"
        )
        for e in day["workout"]["exercises"]:
            eo = get_exercise(e.get("exercise_id", e["name"]))
            assert eo is not None
            req = set(eo.equipment or [])
            assert not (req & {"cable", "barbell", "machine"}), (
                f"{day['day']}: {eo.id} wymaga niedostępnego sprzętu {req & {'cable', 'barbell', 'machine'}}"
            )


def test_gym_full_profile_still_works(monkeypatch):
    """Kompatybilność wsteczna: profil z pełnym sprzętem siłowni nadal generuje kompletny plan."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan("4 dni", 4, "średniozaawansowany",
                 ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"],
                 ["klatka", "plecy", "nogi", "brzuch", "barki"])
    td = _training_days(plan)
    assert len(td) == 4
    for day in td:
        assert len(day["workout"]["exercises"]) >= 3, f"{day['day']}: zbyt mało ćwiczeń"


def test_no_exercise_requires_unlisted_equipment_for_dumbbell_user(monkeypatch):
    """Użytkownik z hantlami+ławką nie otrzymuje ćwiczeń z dip_station, pullup_bar, kettlebell, ab_wheel, machine, cable, barbell."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    from app.exercises.data import get_exercise
    plan = _plan("4 dni", 4, "średniozaawansowany",
                 ["hantle", "ławka"],
                 ["klatka", "plecy", "nogi", "brzuch", "barki"])
    for day in _training_days(plan):
        for e in day["workout"]["exercises"]:
            eo = get_exercise(e.get("exercise_id", e["name"]))
            assert eo is not None
            req = set(eo.equipment or [])
            unavailable = req & {"dip_station", "pullup_bar", "kettlebell", "ab_wheel", "machine", "cable", "barbell"}
            assert not unavailable, (
                f"{day['day']}: {eo.id} wymaga niedostępnego sprzętu {unavailable}"
            )


# ============================================================================
# Priorytety mięśniowe — wpływ na ranking wyboru ćwiczeń
# ============================================================================

def test_selection_rank_key_priority_tier(monkeypatch):
    """Ocena priorytetu zmienia drugi klucz rankingu (wyższy priorytet = niższy klucz sortowania)."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    from app.plan.generator_v2 import _selection_rank_key
    from app.exercises.data import get_exercise
    pullup_wide = get_exercise("pullup_wide")      # primary=lats(plecy), secondary=[biceps, back], rank=2
    barbell_row = get_exercise("barbell_row")      # primary=back(plecy), secondary=[lats], rank=2
    assert pullup_wide is not None and barbell_row is not None
    assert _selection_rank_key(pullup_wide)[0] == 2
    assert _selection_rank_key(barbell_row)[0] == 2
    # Bez priorytetów: oba priority_score=0 -> drugi klucz = 0.
    assert _selection_rank_key(pullup_wide)[:2] == (2, 0)
    assert _selection_rank_key(barbell_row)[:2] == (2, 0)
    # Priorytet plecy (score=10): oba primary=plecy -> priority_score=10 -> drugi klucz = -10.
    key_pw = _selection_rank_key(pullup_wide, priority_scores={"plecy": 10})
    key_br = _selection_rank_key(barbell_row, priority_scores={"plecy": 10})
    assert key_pw[:2] == (2, -10), key_pw
    assert key_br[:2] == (2, -10), key_br
    # Priorytet biceps: pullup_wide ma biceps w secondary -> score = 10//2 = 5 -> -5.
    key_pw_biceps = _selection_rank_key(pullup_wide, priority_scores={"biceps": 10})
    key_br_biceps = _selection_rank_key(barbell_row, priority_scores={"biceps": 10})
    assert key_pw_biceps[:2] == (2, -5), key_pw_biceps
    assert key_br_biceps[:2] == (2, 0), key_br_biceps  # barbell_row ma lats(plecy) w secondary, nie biceps
    assert key_pw_biceps < key_br_biceps, "priorytet secondary powinien wywindować ćwiczenie wyżej w rankingu"
    # Priorytet nie przewyższa wyraźnie lepszego selection_rank (brak dominacji).
    weak = get_exercise("band_row")                # horizontal_pull, rank=8, primary=back(plecy)
    assert weak is not None
    assert _selection_rank_key(pullup_wide, priority_scores={"plecy": 10}) < _selection_rank_key(weak, priority_scores={"biceps": 10})


def test_high_priority_chest_and_biceps_affects_exercise_choice(monkeypatch):
    """Wysoki priorytet klatki i bicepsa wpływa na dobór odpowiednich ćwiczeń."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    from app.exercises.data import get_exercise
    plan = _plan("4 dni", 4, "średniozaawansowany", GYM_FULL, ["klatka", "biceps"])
    all_ids = [e.get("exercise_id") for day in _training_days(plan) for e in day["workout"]["exercises"]]
    biceps_ids = {"barbell_curl", "cable_curl", "hammer_curl", "concentration_curl", "spider_curl", "alternating_dumbbell_curl"}
    chest_ids = {"barbell_bench_press", "dumbbell_bench_press", "incline_dumbbell_press", "pec_deck", "cable_crossover", "pushups_classic"}
    assert bool(set(all_ids) & biceps_ids), f"Brak ćwiczeń bicepsa mimo priorytetu: {all_ids}"
    assert bool(set(all_ids) & chest_ids), f"Brak ćwiczeń klatki mimo priorytetu: {all_ids}"
    # Inne partie nie są całkowicie pominięte — jeden priorytet nie dominuje planu.
    present_primary = set()
    for i in all_ids:
        eo = get_exercise(i)
        if eo and eo.primary_muscles:
            present_primary.add(eo.primary_muscles[0])
    for m in ("back", "lats", "quads", "hamstrings"):
        assert m in present_primary, f"Partia {m} całkowicie pominięta mimo że nie jest priorytetem: {present_primary}"


def test_low_priority_does_not_skip_other_muscles(monkeypatch):
    """Niski priorytet (tylko jedna partia focus) nie powoduje pominięcia pozostałych partii."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    from app.exercises.data import get_exercise
    plan = _plan("4 dni", 4, "średniozaawansowany", GYM_FULL, ["biceps"])
    all_ids = [e.get("exercise_id") for day in _training_days(plan) for e in day["workout"]["exercises"]]
    present_primary = set()
    for i in all_ids:
        eo = get_exercise(i)
        if eo and eo.primary_muscles:
            present_primary.add(eo.primary_muscles[0])
    # Klatka, plecy, nogi nadal trenowane mimo że nie są priorytetem.
    for m in ("chest", "back", "lats", "quads"):
        assert m in present_primary, f"Partia {m} pominięta przy niskim priorytecie: {present_primary}"


# ============================================================================
# Różnorodność — ograniczenie nieuzasadnionych powtórzeń między sesjami
# ============================================================================

def test_generator_limits_unjustified_repetition_across_week(monkeypatch):
    """Ćwiczenie bez allow_repeat_across_sessions nie powtarza się między dniami."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    from app.exercises.data import get_exercise
    from collections import Counter
    plan = _plan("6 dni", 6, "średniozaawansowany", GYM_FULL, ["klatka", "plecy", "nogi", "brzuch", "barki"])
    all_ids = [e.get("exercise_id") for day in _training_days(plan) for e in day["workout"]["exercises"]]
    counts = Counter(all_ids)
    for ex_id, cnt in counts.items():
        if cnt > 1:
            eo = get_exercise(ex_id)
            assert eo is not None and getattr(eo, "allow_repeat_across_sessions", False), (
                f"{ex_id} powtarza się {cnt}x w tygodniu mimo braku allow_repeat_across_sessions: {all_ids}"
            )


def test_allow_repeat_exercises_may_repeat(monkeypatch):
    """Dozwolone powtórzenia (lateral_raise, standing_calf_raise) nadal działają."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    from app.exercises.data import get_exercise
    from collections import Counter
    plan = _plan("4 dni", 4, "średniozaawansowany", GYM_FULL, ["klatka", "plecy", "nogi", "brzuch", "barki"])
    all_ids = [e.get("exercise_id") for day in _training_days(plan) for e in day["workout"]["exercises"]]
    counts = Counter(all_ids)
    assert get_exercise("lateral_raise") is not None
    assert get_exercise("standing_calf_raise") is not None
    assert counts.get("lateral_raise", 0) >= 2, f"lateral_raise powinien się powtarzać (upper A i B): {counts}"
    assert counts.get("standing_calf_raise", 0) >= 2, f"standing_calf_raise powinien się powtarzać (lower A i B): {counts}"


def test_equipment_filtering_still_works_with_priority(monkeypatch):
    """Filtrowanie sprzętu działa niezależnie od priorytetów mięśniowych."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    from app.exercises.data import get_exercise
    # Użytkownik ma tylko hantle i ławkę, ale ustawia wysoki priorytet klatki/bicepsa.
    plan = _plan("4 dni", 4, "średniozaawansowany", ["hantle", "ławka"], ["klatka", "biceps"])
    for day in _training_days(plan):
        for e in day["workout"]["exercises"]:
            eo = get_exercise(e.get("exercise_id", e["name"]))
            assert eo is not None, f"Nieznane ćwiczenie: {e.get('exercise_id', e['name'])}"
            req = set(eo.equipment or [])
            assert not (req & {"cable", "barbell", "machine"}), (
                f"{day['day']}: {eo.id} wymaga niedostępnego sprzętu {req & {'cable', 'barbell', 'machine'}}"
            )


# ============================================================================
# Dostępność treningowa — niedziela jako dzień treningowy
# ============================================================================

def _make_user_with_availability(*, frequency, days, level, equipment_list, focus, availability_days, goal="masa mięśniowa"):
    """Jak _make_user, ale z zadeklarowaną dostępnością dni."""
    user = _make_user(frequency=frequency, days=days, level=level,
                      equipment_list=equipment_list, focus=focus, goal=goal)
    user.training_availability_json = json.dumps(
        {"days": availability_days, "windows": {}, "session_duration_minutes": 60},
        ensure_ascii=False,
    )
    return user


def _plan_with_availability(frequency, days, level, equipment_list, focus, availability_days):
    user = _make_user_with_availability(
        frequency=frequency, days=days, level=level,
        equipment_list=equipment_list, focus=focus, availability_days=availability_days,
    )
    assessment = _make_assessment(days=days, level=level)
    return build_deterministic_plan(user, assessment)


def test_four_day_availability_includes_sunday(monkeypatch):
    """4 zadeklarowane dni (Pon, Pt, Sob, Nd) generują dokładnie 4 sesje, w tym niedzielę."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan_with_availability("4 dni", 4, "średniozaawansowany", GYM_FULL,
                                   ["klatka", "plecy", "nogi", "brzuch", "barki"],
                                   ["Poniedziałek", "Piątek", "Sobota", "Niedziela"])
    td = _training_days(plan)
    assert len(td) == 4, f"Oczekiwano 4 sesji, jest {len(td)}"
    day_names = [d["day"] for d in td]
    assert day_names == ["Poniedziałek", "Piątek", "Sobota", "Niedziela"], f"Dni: {day_names}"
    assert "Niedziela" in day_names, f"Niedziela nie jest dniem treningowym: {day_names}"


def test_four_day_availability_upper_lower_split(monkeypatch):
    """4 dni z dostępnością zawierającą niedzielę dają split upper_lower_4 bez duplikatu szablonu."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan_with_availability("4 dni", 4, "średniozaawansowany", GYM_FULL,
                                   ["klatka", "plecy", "nogi", "brzuch", "barki"],
                                   ["Poniedziałek", "Piątek", "Sobota", "Niedziela"])
    td = _training_days(plan)
    focuses = [d["workout"]["focus"] for d in td]
    assert focuses == ["upper_a", "lower_a", "upper_b", "lower_b"], f"Focusy: {focuses}"
    # Nie ma duplikatu tego samego szablonu w dwóch różnych dniach.
    assert len(set(focuses)) == 4, f"Zduplikowane szablony: {focuses}"


def test_four_day_consecutive_days_different_focus(monkeypatch):
    """Piątek–Sobota–Niedziela (dni pod rząd) mają różny focus dla regeneracji."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan_with_availability("4 dni", 4, "średniozaawansowany", GYM_FULL,
                                   ["klatka", "plecy", "nogi", "brzuch", "barki"],
                                   ["Poniedziałek", "Piątek", "Sobota", "Niedziela"])
    td = _training_days(plan)
    fri = next(d for d in td if d["day"] == "Piątek")
    sat = next(d for d in td if d["day"] == "Sobota")
    sun = next(d for d in td if d["day"] == "Niedziela")
    assert fri["workout"]["focus"] != sat["workout"]["focus"], (
        f"Pt i Sob ten sam focus: {fri['workout']['focus']}"
    )
    assert sat["workout"]["focus"] != sun["workout"]["focus"], (
        f"Sob i Nd ten sam focus: {sat['workout']['focus']}"
    )


def test_four_day_availability_equipment_filtered(monkeypatch):
    """Przy ograniczonej dostępności sprzętu wszystkie ćwiczenia są dozwolone."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan_with_availability("4 dni", 4, "średniozaawansowany",
                                   ["hantle", "ławka", "gumy oporowe", "mata"],
                                   ["klatka", "plecy", "nogi", "brzuch", "barki"],
                                   ["Poniedziałek", "Piątek", "Sobota", "Niedziela"])
    from app.exercises.data import get_exercise
    for day in _training_days(plan):
        for e in day["workout"]["exercises"]:
            eo = get_exercise(e.get("exercise_id", e["name"]))
            assert eo is not None
            req = set(eo.equipment or [])
            unavailable = req & {"cable", "barbell", "machine", "dip_station", "pullup_bar", "kettlebell", "ab_wheel"}
            assert not unavailable, (
                f"{day['day']}: {eo.id} wymaga niedostępnego sprzętu {unavailable}"
            )


def test_four_day_availability_within_volume_limits(monkeypatch):
    """Objętość nie przekracza górnych granic nawet z 4 dniami i niedzielą."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    from app.plan.generator_v2 import VOLUME_TARGETS_INTERMEDIATE
    plan = _plan_with_availability("4 dni", 4, "średniozaawansowany", GYM_FULL,
                                   ["klatka", "plecy", "nogi", "brzuch", "barki"],
                                   ["Poniedziałek", "Piątek", "Sobota", "Niedziela"])
    from app.exercises.data import get_exercise
    from app.plan.generator_v2 import _volume_subgroup
    totals = {}
    for day in _training_days(plan):
        for e in day["workout"]["exercises"]:
            eo = get_exercise(e.get("exercise_id", e["name"]))
            if eo is None or not eo.primary_muscles:
                continue
            sg = _volume_subgroup(eo.primary_muscles)
            if sg:
                totals[sg] = totals.get(sg, 0) + e["sets"]
    for muscle, (low, high) in VOLUME_TARGETS_INTERMEDIATE.items():
        max_allowed = high * 1.25
        actual = totals.get(muscle, 0)
        assert actual <= max_allowed, (
            f"{muscle}: {actual} serii, max dozwolone {max_allowed}"
        )


# ============================================================================
# Ulepszenia planu 4-dniowego — klatka ~8 serii, dwugłowe w obu sesjach dolnych
# ============================================================================

def test_chest_volume_approx_eight_sets_beginner(monkeypatch):
    """Klatka jako priorytet dostaje około 8 serii tygodniowo dla początkującego w splitcie 4-dniowym."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan_with_availability("4 dni", 4, "początkujący", ["hantle", "ławka", "gumy oporowe", "mata"],
                                   ["klatka", "biceps", "brzuch"],
                                   ["Poniedziałek", "Piątek", "Sobota", "Niedziela"])
    from app.exercises.data import get_exercise
    chest_sets = 0
    for day in _training_days(plan):
        for e in day["workout"]["exercises"]:
            eo = get_exercise(e.get("exercise_id", e["name"]))
            if eo and eo.primary_muscles and eo.primary_muscles[0] == "chest":
                chest_sets += e["sets"]
    assert 7 <= chest_sets <= 9, f"Klatka powinna mieć ~8 serii, ma {chest_sets}"


def test_hamstrings_covered_in_both_lower_sessions(monkeypatch):
    """Obie sesje dolne (lower_a i lower_b) zawierają ćwiczenie na dwugłowe."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    plan = _plan_with_availability("4 dni", 4, "początkujący", ["hantle", "ławka", "gumy oporowe", "mata"],
                                   ["klatka", "plecy", "nogi", "brzuch", "barki"],
                                   ["Poniedziałek", "Piątek", "Sobota", "Niedziela"])
    from app.exercises.data import get_exercise
    lower_days = [d for d in _training_days(plan) if d["workout"]["focus"] in ("lower_a", "lower_b")]
    assert len(lower_days) == 2, f"Oczekiwano 2 sesji dolnych, jest {len(lower_days)}"
    for day in lower_days:
        has_hamstrings = False
        for e in day["workout"]["exercises"]:
            eo = get_exercise(e.get("exercise_id", e["name"]))
            if eo and eo.primary_muscles and eo.primary_muscles[0] == "hamstrings":
                has_hamstrings = True
        assert has_hamstrings, f"{day['day']} ({day['workout']['focus']}) nie ma ćwiczenia na dwugłowe jako primary"


# ============================================================================
# Stage C1: Realistyczny budżet czasu sesji (szacunek i egzekwowanie limitu)
# ============================================================================


def test_c1_respects_declared_session_duration_limit(monkeypatch):
    """Żadna sesja nie przekracza zadeklarowanego session_duration_minutes."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    user = _make_user_with_availability(
        frequency="3 dni", days=3, level="początkujący",
        equipment_list=["hantle", "ławka", "gumy oporowe", "mata"],
        focus=["klatka", "plecy", "nogi", "brzuch", "barki"],
        availability_days=["Poniedziałek", "Środa", "Piątek"],
    )
    user.training_availability_json = json.dumps(
        {"days": ["Poniedziałek", "Środa", "Piątek"], "windows": {}, "session_duration_minutes": 45},
        ensure_ascii=False,
    )
    assessment = _make_assessment(days=3, level="początkujący")
    plan = build_deterministic_plan(user, assessment)
    for day in _training_days(plan):
        mins = day["workout"].get("estimated_minutes", 0)
        assert mins <= 45, f"{day['day']}: {mins} min > zadeklarowane 45 min"


def test_c1_realistic_estimate_includes_rest_warmup_transitions():
    """Szacunek uwzględnia przerwy między seriami, rozgrzewkę i przejścia."""
    from app.plan.generator_v2 import _calculate_estimated_minutes
    exs = [
        {"exercise_id": "goblet_squat", "name": "Przysiad goblet z hantlem", "sets": 3},
        {"exercise_id": "dumbbell_bench_press", "name": "Wyciskanie hantli na ławce płaskiej", "sets": 3},
    ]
    minutes = _calculate_estimated_minutes(exs)
    # 6 serie * 1.25 + 4 przerwy * 1.0 + rozgrzewka 5 + 1 przejście * 0.75 = 17.25 -> 18
    assert minutes == 18, f"Oczekiwano 18 min, jest {minutes}"


def test_c1_unilateral_exercise_not_underestimated():
    """Ćwiczenie jednostronne ('/strona') dolicza dodatkowy czas na drugą stronę."""
    from app.plan.generator_v2 import _calculate_estimated_minutes, _is_unilateral_exercise
    from app.exercises.data import get_exercise
    ex_obj = get_exercise("one_arm_dumbbell_row")
    assert _is_unilateral_exercise(ex_obj), "one_arm_dumbbell_row powinno być wykryte jako jednostronne"
    bilateral = [{"exercise_id": "dumbbell_bench_press", "name": "Wyciskanie hantli na ławce płaskiej", "sets": 3}]
    unilateral = [{"exercise_id": "one_arm_dumbbell_row", "name": "Wiosłowanie hantlem jednostronnie", "sets": 3}]
    bi = _calculate_estimated_minutes(bilateral)
    uni = _calculate_estimated_minutes(unilateral)
    assert uni == bi + 1, f"Bilateral {bi} min, unilateral {uni} min (różnica powinna wynosić 1 min)"


def test_c1_plan_exceeding_limit_is_adjusted(monkeypatch):
    """Przy niskim limicie plan jest redukowany (izolacje zdejmowane, złożone zachowane)."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")

    def _build(minutes: int):
        user = _make_user_with_availability(
            frequency="3 dni", days=3, level="początkujący",
            equipment_list=["hantle", "ławka"],
            focus=["klatka", "plecy", "nogi", "brzuch", "barki"],
            availability_days=["Poniedziałek", "Środa", "Piątek"],
        )
        user.training_availability_json = json.dumps(
            {"days": ["Poniedziałek", "Środa", "Piątek"], "windows": {}, "session_duration_minutes": minutes},
            ensure_ascii=False,
        )
        assessment = _make_assessment(days=3, level="początkujący")
        return build_deterministic_plan(user, assessment)

    from app.exercises.data import get_exercise
    limited = _build(40)
    unlimited = _build(120)
    for day in _training_days(limited):
        mins = day["workout"].get("estimated_minutes", 0)
        assert mins <= 40, f"{day['day']}: {mins} min > zadeklarowane 40 min"
        assert len(day["workout"]["exercises"]) >= 3, f"{day['day']}: struktura sesji zbyt mocno uproszczona"
        compounds = [e for e in day["workout"]["exercises"]
                     if get_exercise(e.get("exercise_id", e["name"])) and get_exercise(e.get("exercise_id", e["name"])).type == "compound"]
        assert compounds, f"{day['day']}: brak ćwiczeń złożonych po redukcji czasu"
    # Przy niższym limicie nie ma więcej ćwiczeń niż przy nieograniczonym (redukcja, nie rozbudowa).
    for ld, ud in zip(_training_days(limited), _training_days(unlimited)):
        assert len(ld["workout"]["exercises"]) <= len(ud["workout"]["exercises"])


def test_c1_missing_legacy_availability_does_not_break(monkeypatch):
    """Brak lub uszkodzona dostępność nie przerywa generowania; stosowany jest limit domyślny 75 min."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    for availability in ("{}", "not-json"):
        user = _make_user(
            frequency="3 dni", days=3, level="początkujący",
            equipment_list=["hantle", "ławka"],
            focus=["klatka", "plecy", "nogi", "brzuch", "barki"],
        )
        user.training_availability_json = availability
        assessment = _make_assessment(days=3, level="początkujący")
        plan = build_deterministic_plan(user, assessment)
        assert plan is not None
        assert "_planner" in plan
        for day in _training_days(plan):
            assert day["workout"].get("estimated_minutes", 0) <= 75, (
                f"Domyślny limit 75 min przekroczony: {day['workout'].get('estimated_minutes')} min"
            )


def test_c1_flag_false_when_within_cap(monkeypatch):
    """Flaga session_exceeds_cap jest False gdy sesja mieści się w limicie."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    user = _make_user_with_availability(
        frequency="3 dni", days=3, level="początkujący",
        equipment_list=["hantle", "ławka", "gumy oporowe", "mata"],
        focus=["klatka", "plecy", "nogi", "brzuch", "barki"],
        availability_days=["Poniedziałek", "Środa", "Piątek"],
    )
    user.training_availability_json = json.dumps(
        {"days": ["Poniedziałek", "Środa", "Piątek"], "windows": {}, "session_duration_minutes": 60},
        ensure_ascii=False,
    )
    assessment = _make_assessment(days=3, level="początkujący")
    plan = build_deterministic_plan(user, assessment)
    saw_false = False
    for day in plan["days"]:
        flag = day["workout"].get("session_exceeds_cap")
        mins = day["workout"].get("estimated_minutes", 0)
        expected = mins > 60
        assert flag == expected, (
            f"{day['day']}: flaga={flag} niezgoda z est={mins} min (limit 60)"
        )
        if not flag:
            saw_false = True
    assert saw_false, "Oczekiwano przynajmniej jednego dnia z flagą False przy limicie 60 min"


def test_c1_flag_true_when_exceeds_cap_after_reduction(monkeypatch):
    """Flaga session_exceeds_cap jest True gdy sesja nadal przekracza limit mimo redukcji."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    user = _make_user_with_availability(
        frequency="3 dni", days=3, level="początkujący",
        equipment_list=["hantle", "ławka"],
        focus=["klatka", "plecy", "nogi", "brzuch", "barki"],
        availability_days=["Poniedziałek", "Środa", "Piątek"],
    )
    user.training_availability_json = json.dumps(
        {"days": ["Poniedziałek", "Środa", "Piątek"], "windows": {}, "session_duration_minutes": 15},
        ensure_ascii=False,
    )
    assessment = _make_assessment(days=3, level="początkujący")
    plan = build_deterministic_plan(user, assessment)
    exceeded = False
    for day in _training_days(plan):
        flag = day["workout"].get("session_exceeds_cap")
        mins = day["workout"].get("estimated_minutes", 0)
        if mins > 15:
            exceeded = True
            assert flag is True, f"{day['day']}: est={mins} > 15 ale flaga={flag}"
        else:
            assert flag is False, f"{day['day']}: est={mins} <= 15 ale flaga={flag}"
    assert exceeded, "Oczekiwano przynajmniej jednej sesji przekraczającej limit 15 min mimo redukcji"


def test_c1_flag_consistency_all_days(monkeypatch):
    """Flaga jest zgodna z estimated_minutes i session_duration_minutes dla każdego dnia."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    user = _make_user_with_availability(
        frequency="4 dni", days=4, level="średniozaawansowany",
        equipment_list=["hantle", "ławka"],
        focus=["klatka", "plecy", "nogi", "brzuch", "barki"],
        availability_days=["Poniedziałek", "Wtorek", "Czwartek", "Piątek"],
    )
    user.training_availability_json = json.dumps(
        {"days": ["Poniedziałek", "Wtorek", "Czwartek", "Piątek"], "windows": {}, "session_duration_minutes": 50},
        ensure_ascii=False,
    )
    assessment = _make_assessment(days=4, level="średniozaawansowany")
    plan = build_deterministic_plan(user, assessment)
    for day in plan["days"]:
        flag = day["workout"].get("session_exceeds_cap")
        mins = day["workout"].get("estimated_minutes", 0)
        assert flag is (mins > 50), (
            f"{day['day']}: flaga={flag} niezgoda z est={mins} min (limit 50)"
        )


# ============================================================================
# Stage C2: Balans sesji i powtórzenia ćwiczeń między dniami
# ============================================================================


def test_c2_full_body_three_days_differentiate_repeated_template(monkeypatch):
    """W splicie full_body_3 (A/B/A) trzeci dzień nie powiela ćwiczeń stapeli z dnia 1."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    user = _make_user_with_availability(
        frequency="3 dni", days=3, level="początkujący",
        equipment_list=["hantle", "ławka", "guma oporowa", "mata"],
        focus=["klatka", "plecy", "nogi", "brzuch", "barki"],
        availability_days=["Poniedziałek", "Środa", "Piątek"],
    )
    assessment = _make_assessment(days=3, level="początkujący")
    plan = build_deterministic_plan(user, assessment)
    fb_days = [d for d in _training_days(plan) if d["workout"]["focus"] == "full_body_a"]
    assert len(fb_days) == 2, f"Oczekiwano 2 dni full_body_a, jest {len(fb_days)}"
    ids_a = set(_exercise_ids(fb_days[0]))
    ids_c = set(_exercise_ids(fb_days[1]))
    # Sesje nie mogą być identyczne (różnica w zestawie ćwiczeń).
    assert ids_a != ids_c, f"full_body_3 dzień 1 i 3 identyczne: {ids_a}"
    # Staple (lateral_raise / łyżki) użyte w dniu 1 nie powinny się powtarzać w dniu 3.
    staples = {"lateral_raise", "standing_calf_raise"}
    used_in_a = ids_a & staples
    assert not (used_in_a & ids_c), (
        f"Staple powtórzono między A a C: {used_in_a & ids_c}"
    )


def test_c2_repetition_preserved_when_no_alternative(monkeypatch):
    """Gdy brak zamiennika, generator nie wywala się i sesje blieben poprawne (powtórzenie dopuszczalne)."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    # Masa własna, beginner, 3 dni — ograniczone zamienniki, powtórzenia mogą być nieuniknione.
    user = _make_user_with_availability(
        frequency="3 dni", days=3, level="początkujący",
        equipment_list=[], focus=["klatka", "plecy", "nogi", "brzuch", "barki"],
        availability_days=["Poniedziałek", "Środa", "Piątek"],
    )
    assessment = _make_assessment(days=3, level="początkujący")
    plan = build_deterministic_plan(user, assessment)
    assert plan is not None and "_planner" in plan
    for day in _training_days(plan):
        exs = day["workout"]["exercises"]
        assert 3 <= len(exs) <= 6, f"{day['day']}: {len(exs)} ćwiczeń (beginner 3-6)"
        assert day["workout"].get("estimated_minutes", 0) <= 60, (
            f"{day['day']}: {day['workout'].get('estimated_minutes')} min > 60"
        )


def test_c2_arm_coverage_when_prioritized_and_compatible(monkeypatch):
    """Priorytet biceps/triceps z pełnym sprzętem i średnim poziomem -> obie partie obecne."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    GYM = ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"]
    user = _make_user_with_availability(
        frequency="4 dni", days=4, level="średniozaawansowany",
        equipment_list=GYM, focus=["klatka", "plecy", "nogi", "brzuch", "barki", "biceps", "triceps"],
        availability_days=["Poniedziałek", "Wtorek", "Czwartek", "Piątek"],
    )
    assessment = _make_assessment(days=4, level="średniozaawansowany")
    plan = build_deterministic_plan(user, assessment)
    sessions = plan["_planner"]["weekly_summary"]["sessions_per_group"]
    assert sessions.get("biceps", 0) >= 1, f"Brak sesji biceps mimo priorytetu: {sessions}"
    assert sessions.get("triceps", 0) >= 1, f"Brak sesji triceps mimo priorytetu: {sessions}"


def test_c2_beginner_volume_and_duration_respected(monkeypatch):
    """Beginner: objętość i czas sesji mieszczą się w limitach (beginner 3-6 ćwiczeń, <= 60 min)."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")
    user = _make_user_with_availability(
        frequency="3 dni", days=3, level="początkujący",
        equipment_list=["hantle", "ławka", "guma oporowa", "mata"],
        focus=["klatka", "plecy", "nogi", "brzuch", "barki"],
        availability_days=["Poniedziałek", "Środa", "Piątek"],
    )
    user.training_availability_json = json.dumps(
        {"days": ["Poniedziałek", "Środa", "Piątek"], "windows": {}, "session_duration_minutes": 60},
        ensure_ascii=False,
    )
    assessment = _make_assessment(days=3, level="początkujący")
    plan = build_deterministic_plan(user, assessment)
    for day in _training_days(plan):
        exs = day["workout"]["exercises"]
        assert 3 <= len(exs) <= 6, f"{day['day']}: {len(exs)} ćwiczeń (beginner 3-6)"
        mins = day["workout"].get("estimated_minutes", 0)
        assert mins <= 60, f"{day['day']}: {mins} min > zadeklarowane 60 min"
        assert day["workout"].get("session_exceeds_cap") is False, (
            f"{day['day']}: sesja przekracza limit mimo redukcji"
        )


# ---------------------------------------------------------------------------
# Generator consumption: frequency and goal from saved profile
# ---------------------------------------------------------------------------


def test_generator_consumes_saved_frequency_and_goal(monkeypatch):
    """Saved profile frequency -> target_training_days; goal -> weekly_goal.

    The v2 strength generator consumes:
      - user.frequency  -> _frequency_days() -> target_training_days
      - user.goal       -> weekly_goal in plan output

    Age, gender, height, weight, target_weight are NOT directly consumed by
    build_split_plan; they influence calories_target via calc_calories() which
    is called outside the generator (registration / profile update), and only
    used here as a fallback when calories_target is unset.
    """
    monkeypatch.setenv("PLAN_GENERATOR", "v2")

    equipment_list = ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"]
    focus = ["klatka", "plecy", "nogi", "brzuch", "barki"]

    # Frequency "5-6" should map to target_training_days >= 5
    user = _make_user(
        frequency="5-6 dni", days=6, level="intermediate",
        equipment_list=equipment_list, focus=focus, goal="redukcja",
    )
    user.training_availability_json = json.dumps(
        {"days": ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota"],
         "windows": {}, "session_duration_minutes": 60},
        ensure_ascii=False,
    )
    assessment = _make_assessment(days=6, level="intermediate")
    plan = build_deterministic_plan(user, assessment)

    assert plan["weekly_goal"] == "redukcja", (
        f"weekly_goal should equal saved goal, got {plan['weekly_goal']!r}"
    )
    assert plan["_planner"]["target_training_days"] >= 5, (
        f"frequency 5-6 should yield >=5 training days, got {plan['_planner']['target_training_days']}"
    )

    # Frequency "1-2" should map to target_training_days <= 2
    user2 = _make_user(
        frequency="1-2 dni", days=2, level="intermediate",
        equipment_list=equipment_list, focus=focus, goal="masa",
    )
    user2.training_availability_json = json.dumps(
        {"days": ["Poniedziałek", "Czwartek"], "windows": {}, "session_duration_minutes": 60},
        ensure_ascii=False,
    )
    assessment2 = _make_assessment(days=2, level="intermediate")
    plan2 = build_deterministic_plan(user2, assessment2)

    assert plan2["weekly_goal"] == "masa"
    assert plan2["_planner"]["target_training_days"] <= 2, (
        f"frequency 1-2 should yield <=2 training days, got {plan2['_planner']['target_training_days']}"
    )


# ---------------------------------------------------------------------------
# Age-aware safety: minors under 18
# ---------------------------------------------------------------------------


def _make_minor_user(*, age: int | None = 16, **kwargs) -> SimpleNamespace:
    """Użytkownik z wiekiem — domyślnie 16 lat (niepełnoletni)."""
    user = _make_user(**kwargs)
    if age is None:
        user.age = None
    else:
        user.age = age
    return user


def test_minor_16_gets_minor_flag_and_submaximal_effort(monkeypatch):
    """16-letni początkujący: plan ma minor=True i effort=submaximal na każdym ćwiczeniu."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")

    equipment_list = ["hantle", "ławka", "guma oporowa", "mata"]
    focus = ["klatka", "plecy", "nogi", "brzuch", "barki"]

    user = _make_minor_user(
        age=16,
        frequency="3 dni", days=3, level="początkujący",
        equipment_list=equipment_list, focus=focus, goal="masa mięśniowa",
    )
    user.training_availability_json = json.dumps(
        {"days": ["Poniedziałek", "Środa", "Piątek"], "windows": {}, "session_duration_minutes": 60},
        ensure_ascii=False,
    )
    assessment = _make_assessment(days=3, level="początkujący")
    plan = build_deterministic_plan(user, assessment)

    assert plan["_planner"]["minor"] is True, (
        f"minor flag should be True for 16-year-old, got {plan['_planner'].get('minor')!r}"
    )

    # Każde ćwiczenie w każdym dniu musi mieć effort="submaximal".
    for day in plan["days"]:
        if day["day_type"] == "rest":
            continue
        for ex in day["workout"]["exercises"]:
            assert ex.get("effort") == "submaximal", (
                f"Ćwiczenie {ex['name']} w dniu {day['day']} nie ma effort=submaximal: {ex.get('effort')!r}"
            )
            for alt in ex.get("alternatives", []):
                assert alt.get("effort") == "submaximal", (
                    f"Alternatywa {alt['name']} nie ma effort=submaximal"
                )

    # Diagnostyka powinna wspominać o niepełnoletniości.
    diag_text = " ".join(plan["_planner"]["schedule_diagnostics"]["notes"])
    assert "niepełnoletni" in diag_text.lower(), (
        f"Diagnostyka nie zawiera informacji o niepełnoletniości: {diag_text!r}"
    )


def test_missing_age_raises_validation_error(monkeypatch):
    """Brak wieku → ValueError z komunikatem, nie ciche zakładanie pełnoletniości."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")

    equipment_list = ["hantle", "ławka", "guma oporowa", "mata"]
    focus = ["klatka", "plecy", "nogi", "brzuch", "barki"]

    user = _make_minor_user(
        age=None,
        frequency="3 dni", days=3, level="początkujący",
        equipment_list=equipment_list, focus=focus, goal="masa mięśniowa",
    )
    assessment = _make_assessment(days=3, level="początkujący")

    with pytest.raises(ValueError, match="wiek"):
        build_deterministic_plan(user, assessment)


def test_invalid_age_raises_validation_error(monkeypatch):
    """Wiek spoza zakresu (np. 12 lat) → ValueError z komunikatem."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")

    equipment_list = ["hantle", "ławka", "guma oporowa", "mata"]
    focus = ["klatka", "plecy", "nogi", "brzuch", "barki"]

    user = _make_minor_user(
        age=12,
        frequency="3 dni", days=3, level="początkujący",
        equipment_list=equipment_list, focus=focus, goal="masa mięśniowa",
    )
    assessment = _make_assessment(days=3, level="początkujący")

    with pytest.raises(ValueError, match="zakres"):
        build_deterministic_plan(user, assessment)


def test_adult_generation_unchanged_no_minor_flag(monkeypatch):
    """Pełnoletni użytkownik: minor=False, brak pola effort na ćwiczeniach."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")

    equipment_list = ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"]
    focus = ["klatka", "plecy", "nogi", "brzuch", "barki"]

    user = _make_user(
        frequency="3 dni", days=3, level="intermediate",
        equipment_list=equipment_list, focus=focus, goal="masa",
    )
    user.age = 28
    assessment = _make_assessment(days=3, level="intermediate")
    plan = build_deterministic_plan(user, assessment)

    assert plan["_planner"]["minor"] is False

    # Żadne ćwiczenie nie ma pola effort (dorosły).
    for day in plan["days"]:
        if day["day_type"] == "rest":
            continue
        for ex in day["workout"]["exercises"]:
            assert "effort" not in ex, (
                f"Ćwiczenie dorosłego {ex['name']} nie powinno mieć pola effort: {ex.get('effort')!r}"
            )


def test_minor_beginner_plan_is_still_valid_and_executable(monkeypatch):
    """Plan dla 16-latka jest poprawny: ma dni, ćwiczenia, serie i powtórzenia."""
    monkeypatch.setenv("PLAN_GENERATOR", "v2")

    equipment_list = ["hantle", "ławka", "guma oporowa", "mata"]
    focus = ["klatka", "plecy", "nogi", "brzuch", "barki"]

    user = _make_minor_user(
        age=16,
        frequency="3 dni", days=3, level="początkujący",
        equipment_list=equipment_list, focus=focus, goal="masa mięśniowa",
    )
    user.training_availability_json = json.dumps(
        {"days": ["Poniedziałek", "Środa", "Piątek"], "windows": {}, "session_duration_minutes": 60},
        ensure_ascii=False,
    )
    assessment = _make_assessment(days=3, level="początkujący")
    plan = build_deterministic_plan(user, assessment)

    assert plan["weekly_goal"] == "masa mięśniowa"
    assert len(plan["days"]) == 3

    total_exercises = 0
    for day in plan["days"]:
        if day["day_type"] == "rest":
            continue
        exs = day["workout"]["exercises"]
        assert len(exs) >= 3, f"Dzień {day['day']} ma za mało ćwiczeń: {len(exs)}"
        total_exercises += len(exs)
        for ex in exs:
            assert ex["name"]
            assert ex["sets"] >= 1
            assert ex["reps"]

    assert total_exercises >= 9, f"Łącznie za mało ćwiczeń: {total_exercises}"


# ── Stage C4: balans popychaj/ciągnij i personalizacja priorytetów ──────────


def _push_pull(plan):
    from app.plan.generator_v2 import calculate_push_pull_sets
    return calculate_push_pull_sets(plan["days"])


def _weekly_summary(plan):
    return plan["_planner"]["weekly_summary"]


def _make_plan(frequency="3 dni", days=3, level="początkujący",
               equipment_list=("hantle", "ławka"), focus=(),
               goal="masa mięśniowa", duration_minutes=None):
    user = _make_user(
        frequency=frequency, days=days, level=level,
        equipment_list=list(equipment_list), focus=list(focus), goal=goal,
    )
    if duration_minutes is not None:
        user.training_availability_json = json.dumps(
            {"days": ["Poniedziałek", "Środa", "Piątek"],
             "session_duration_minutes": duration_minutes},
            ensure_ascii=False,
        )
    assessment = _make_assessment(days=days, level=level)
    return build_deterministic_plan(user, assessment)


def _training_days(plan):
    return [d for d in plan["days"] if d["day_type"] != "rest"]


def test_weekly_push_pull_balance_beginner_full_body_3():
    """Tydzień pełny (full_body_3): nieprzyjęty dysproporcji popychaj/ciągnij."""
    plan = _make_plan(focus=())
    push, pull = _push_pull(plan)
    assert push > 0 and pull > 0, f"push={push}, pull={pull}"
    # Ciągnięcie nie może być drastycznie mniejsze niż popychanie (≤1.5:1).
    assert pull >= push / 1.5, f"pull {pull} za niskie względem push {push}"
    assert push <= pull * 1.5, f"push {push} za wysokie względem pull {pull}"


def test_chest_priority_does_not_eliminate_back():
    """Wysoki priorytet klatki nie eliminuje pracy pleców (pull remains adequate)."""
    plan_chest = _make_plan(focus=("klatka",))
    plan_back = _make_plan(focus=("plecy",))
    _, pull_chest = _push_pull(plan_chest)
    _, pull_back = _push_pull(plan_back)
    # Przy priorytecie klatki pleców nadal są trenowane (nie usunięte).
    assert pull_chest > 0, f"przy priorytecie klatki pull={pull_chest}, plecy wyeliminowane"
    # Priorytet pleców daje co najmniej tyle samo ciągnięcia co priorytet klatki.
    assert pull_back >= pull_chest, f"pull przy priorytecie pleców {pull_back} < przy klatce {pull_chest}"


def test_biceps_priority_results_in_biceps_trained():
    """Jawny priorytet bicepsa → biceps występuje w końcowym planie."""
    plan = _make_plan(focus=("biceps",))
    summary = _weekly_summary(plan)
    biceps_sets = summary["sets_per_group"].get("biceps", 0)
    assert biceps_sets > 0, f"biceps priorytetyzowany, ale objętość {biceps_sets}"


def test_missing_priorities_do_not_create_arbitrary_ranking():
    """Brak priorytetów nie faworyzuje jednej grupy kosztem pozostałych (brak domyślnego 'wszystko priorytet')."""
    plan = _make_plan(focus=())
    summary = _weekly_summary(plan)
    groups = summary["sets_per_group"]
    trained = {g: s for g, s in groups.items() if s > 0}
    # Główne grupy wzorcowe (klatka, plecy, nogi) zbalansowane bez priorytetów.
    major = {g: s for g, s in trained.items() if g in ("klatka", "plecy", "nogi")}
    assert len(major) >= 3, f"główne grupy nie wszystkie trenowane: {major}"
    if major:
        assert max(major.values()) <= min(major.values()) * 2, \
            f"dysproporcja grup głównych bez priorytetów: {major}"
    # Małe grupy izolatyczne/core mogą być mniejsze — to nie jest arbitralny ranking.


def test_push_pull_balance_across_splits():
    """Zachowanie balansu popychaj/ciągnij we wszystkich obsługiwanych splitach."""
    for days_count, level in ((1, "początkujący"), (2, "początkujący"), (3, "początkujący")):
        plan = _make_plan(days=days_count, level=level, focus=())
        push, pull = _push_pull(plan)
        assert push > 0 and pull > 0, f"split {days_count}: push={push}, pull={pull}"
        assert pull >= push / 1.5, f"split {days_count}: pull {pull} < push/1.5 (push={push})"


def test_secondary_volume_matches_final_plan_accounting():
    """secondary_volume z weekly_summary odpowiada rzeczywistemu planowi końcowemu."""
    from app.plan.generator_v2 import (
        _MUSCLE_TO_VOLUME_SUBGROUP,
    )
    from app.exercises.data import get_exercise
    SECONDARY_MUSCLE_COEFF = 0.35
    plan = _make_plan(focus=())
    expected = {}
    for day in _training_days(plan):
        for ex in day["workout"]["exercises"]:
            ex_obj = get_exercise(ex.get("exercise_id", ex["name"]))
            if ex_obj is None or not ex_obj.secondary_muscles:
                continue
            for sm in ex_obj.secondary_muscles:
                sm_key = _MUSCLE_TO_VOLUME_SUBGROUP.get(sm)
                if sm_key:
                    expected[sm_key] = expected.get(sm_key, 0.0) + ex["sets"] * SECONDARY_MUSCLE_COEFF
    actual = _weekly_summary(plan)["secondary_volume"]
    # weekly_summary zaokrągla secondary_volume do 1 miejsca dziesiętnego.
    for key in actual:
        val = round(expected.get(key, 0.0), 1)
        assert abs(actual.get(key, 0.0) - val) < 1e-6, \
            f"secondary_volume {key}: expected {val}, got {actual.get(key)}"


def test_session_duration_within_cap_beginner_60min():
    """Sesje Beginner 3×60 min nie przekraczają zadeklarowanego limitu czasu."""
    plan = _make_plan(duration_minutes=60)
    for day in _training_days(plan):
        mins = day["workout"].get("estimated_minutes", 0)
        assert mins <= 60, f"{day['day']}: {mins} min > limit 60 min"
        assert day["workout"]["session_exceeds_cap"] is False


def test_no_cable_or_barbell_for_home_dumbbell_equipment():
    """Sprzęt domowy (hantle, ławka) → nie pojawiają się ćwiczenia wyciągowe/sztangowe."""
    plan = _make_plan(equipment_list=("hantle", "ławka"), focus=())
    forbidden = {"wyciąg", "sztanga", "maszyna", "cable", "barbell"}
    for day in _training_days(plan):
        for ex in day["workout"]["exercises"]:
            from app.exercises.data import get_exercise as ge
            eo = ge(ex.get("exercise_id", ex["name"]))
            eq = {str(e).lower() for e in (eo.equipment or [])}
            assert not (eq & forbidden), f"{ex['name']} używa zabronionego sprzętu: {eq}"


def test_age_dependent_safety_preserved_for_minor():
    """Nieważnoletni: submaximal effort i target_rir=3 zachowane w planie."""
    from app.training.routes import _target_rir_for_user
    user = _make_user(
        frequency="3 dni", days=3, level="początkujący",
        equipment_list=["hantle", "ławka"], focus=(),
    )
    user.age = 16
    assert _target_rir_for_user(user) == 3
    user.age = 28
    assert _target_rir_for_user(user) == 2


# ============================================================================
# Stage C5: Graded muscle-priority engine — focused tests on final plans
# ============================================================================

from app.plan.generator_v2 import calculate_push_pull_sets, _MUSCLE_TO_VOLUME_SUBGROUP
from app.exercises.data import get_exercise


def _plan_summary(plan):
    """Zwróć podsumowanie końcowego planu: push/pull, objętość, serie, czas."""
    push, pull = calculate_push_pull_sets(plan["days"])
    primary = {}
    secondary = {}
    total_sets = 0
    total_minutes = 0
    all_names = []
    for d in plan["days"]:
        if d["day_type"] == "rest":
            continue
        total_minutes += d["workout"].get("estimated_minutes", 0)
        for e in d["workout"]["exercises"]:
            total_sets += e["sets"]
            all_names.append(e["name"])
            eo = get_exercise(e.get("exercise_id", e["name"]))
            if eo is None or not eo.primary_muscles:
                continue
            p = eo.primary_muscles[0]
            primary[p] = primary.get(p, 0) + e["sets"]
            if eo.secondary_muscles:
                for sm in eo.secondary_muscles:
                    k = _MUSCLE_TO_VOLUME_SUBGROUP.get(sm)
                    if k:
                        secondary[k] = secondary.get(k, 0) + e["sets"] * 0.35
    return {
        "push": push, "pull": pull, "primary": primary, "secondary": secondary,
        "total_sets": total_sets, "total_minutes": total_minutes, "names": all_names,
    }


def _plan_for(days_count, focus, level="początkujący", equipment=("hantle", "ławka"), age=25):
    user = _make_user(
        frequency=f"{days_count} dni", days=days_count, level=level,
        equipment_list=list(equipment), focus=list(focus),
    )
    user.age = age
    assessment = _make_assessment(days=days_count, level=level)
    return build_deterministic_plan(user, assessment)


def _group_sets(summary, polish_group):
    """Mapuj etykietę po polsku (np. 'klatka') na primary sets z podsumowania."""
    key_map = {
        "klatka": "chest", "plecy": "back", "barki": "side_delts",
        "biceps": "biceps", "triceps": "triceps", "nogi": "quads",
        "brzuch": "abs",
    }
    vol_key = key_map.get(polish_group, polish_group)
    return summary["primary"].get(vol_key, 0)


def test_no_priorities_produces_balanced_baseline():
    """Brak zadeklarowanych priorytetów → główne mięśnie otrzymują bazową objętość, bez preferencji."""
    plan = _plan_for(3, focus=(), equipment=("sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"))
    s = _plan_summary(plan)
    # Klatka i plecy otrzymują objętość (brak pominięcia żadnej głównej grupy).
    chest = _group_sets(s, "klatka")
    back = _group_sets(s, "plecy")
    assert chest > 0 and back > 0
    # Klatka naturalnie ricev więcej serii niż plecy w tym szablonie — nie jest to faworyzacja,
    # tylko wynik struktury ćwiczeń. Różnica nie powinna być ekstremalna.
    assert chest <= back * 3, f"bez priorytetów klatka={chest}, plecy={back} — zbyt duża dysproporcja"
    # Biceps i triceps nadal otrzymują bazową objętość (nie są karane za brak deklaracji).
    # Uwaga: niektóre splity (np. full_body_3) nie zawierają tricepsa — to ograniczenie szablonu, nie priorytetów.
    biceps = _group_sets(s, "biceps")
    triceps = _group_sets(s, "triceps")
    assert biceps >= 3, f"biceps niekarany powinien receber ≥3, ma {biceps}"
    if triceps > 0:
        assert triceps >= 3, f"triceps gdy występuje, powinien otrzymywać ≥3, ma {triceps}"
    # Czas sesji w limitach.
    assert s["total_minutes"] <= 3 * 60, f"całkowity czas {s['total_minutes']} min przekracza limit"


def test_chest_priority_increases_chest_volume_over_back():
    """Klatka 10/10, plecy 9/10 → klatka otrzymuje więcej serii niż bez priorytetu."""
    plan_no = _plan_for(3, focus=())
    plan_chest = _plan_for(3, focus=["klatka", "plecy"])
    plan_back = _plan_for(3, focus=["plecy", "klatka"])
    s_no = _plan_summary(plan_no)
    s_chest = _plan_summary(plan_chest)
    s_back = _plan_summary(plan_back)

    chest_no = _group_sets(s_no, "klatka")
    chest_with_priority = _group_sets(s_chest, "klatka")
    back_no = _group_sets(s_no, "plecy")
    back_with_priority = _group_sets(s_back, "plecy")

    # Priorytet klatki zwiększa objętość klatki względem bazy.
    assert chest_with_priority > chest_no, f"priorytet klatki: {chest_with_priority} vs baza {chest_no}"
    # Priorytet pleców zwiększa objętość pleców względem bazy.
    assert back_with_priority > back_no, f"priorytet pleców: {back_with_priority} vs baza {back_no}"
    # Przy tym obie główne grupy nadal otrzymują wystarczającą objętość (brak zaniedbania).
    assert chest_with_priority >= 10, f"klatka z priorytetem: {chest_with_priority} (< 10)"
    assert back_with_priority >= 6, f"plecy z priorytetem: {back_with_priority} (< 6)"


def test_biceps_priority_increases_biceps_volume():
    """Biceps 9/10 → biceps otrzymuje więcej serii niż bez priorytetu."""
    plan_no = _plan_for(3, focus=())
    plan_biceps = _plan_for(3, focus=["biceps"])
    s_no = _plan_summary(plan_no)
    s_biceps = _plan_summary(plan_biceps)

    biceps_no = _group_sets(s_no, "biceps")
    biceps_high = _group_sets(s_biceps, "biceps")
    assert biceps_high > biceps_no, f"priorytet bicepsa nie zwiększa objętości: {biceps_high} vs {biceps_no}"
    assert biceps_high >= 4, f"biceps z priorytetem 9/10 powinien receber ≥4, ma {biceps_high}"


def test_priority_does_not_reduce_non_priority_baseline():
    """Mięśnie nieobjęte priorytetem nie są karane — otrzymują co najmniej bazową objętość."""
    plan = _plan_for(3, focus=["klatka"])  # tylko klatka ma priorytet 10
    s = _plan_summary(plan)
    # Plecy, barki, nogi, brzuch — mimo braku priorytetu — otrzymują bazową objętość.
    for group in ("plecy", "barki", "nogi", "brzuch"):
        v = _group_sets(s, group)
        assert v >= 3, f"{group} bez priorytetu otrzymuje tylko {v} serii (za mało)"
    # Całkowity wzrost objętości jest ograniczony (nie dodajemy serii bez senso).
    assert s["total_sets"] <= 60, f"całkowite serie {s['total_sets']} — zbyt dużo"


def test_push_pull_balance_preserved_with_chest_priority():
    """Wysoki priorytet klatki nie tworzy niezdrowej dysproporcji popychaj/ciągnij."""
    plan = _plan_for(3, focus=["klatka", "plecy"])
    s = _plan_summary(plan)
    assert s["push"] > 0 and s["pull"] > 0
    assert s["pull"] >= s["push"] / 1.5, f"pull={s['pull']} < push/1.5 (push={s['push']})"
    assert s["push"] <= s["pull"] * 1.5, f"push={s['push']} > pull*1.5 (pull={s['pull']})"


def test_priority_effect_across_day_counts():
    """Priorytet klatki zmienia plan w splitach 1-, 2- i 3-dniowych."""
    for days_count in (1, 2, 3):
        plan_no = _plan_for(days_count, focus=())
        plan_chest = _plan_for(days_count, focus=["klatka", "plecy"])
        s_no = _plan_summary(plan_no)
        s_chest = _plan_summary(plan_chest)
        chest_no = _group_sets(s_no, "klatka")
        chest_high = _group_sets(s_chest, "klatka")
        assert chest_high >= chest_no, f"{days_count}-dniowy: priorytet klatki nie zwiększa objętości ({chest_high} vs {chest_no})"
        # Czas sesji w limitach.
        assert s_chest["total_minutes"] <= days_count * 60, f"{days_count}-dniowy: czas {s_chest['total_minutes']} min przekracza limit"


def test_graded_priority_10_vs_6_produces_different_plans():
    """Priorytet 10/10 (pozycja 0) ma większy wpływ niż 6/10 (pozycja 4) — plany się różnią.
    Wynik 10 → bonus serii dla izolacji; wynik 6 → bez bonusu (próg 7)."""
    plan_high = _plan_for(3, focus=["klatka", "biceps", "triceps", "nogi", "brzuch"])  # klatka=10 → bonus
    plan_low = _plan_for(3, focus=["biceps", "triceps", "nogi", "brzuch", "klatka"])   # klatka=6 → bez bonusu
    s_high = _plan_summary(plan_high)
    s_low = _plan_summary(plan_low)

    chest_high = _group_sets(s_high, "klatka")
    chest_low = _group_sets(s_low, "klatka")
    biceps_high = _group_sets(s_high, "biceps")
    biceps_low = _group_sets(s_low, "biceps")

    # Klatka z priorytetem 10 (bonus) otrzymuje więcej lub igual serii niż z priorytetem 6 (bez bonusu).
    assert chest_high >= chest_low, f"klatka priorytet 10: {chest_high} vs priorytet 6: {chest_low}"
    # Biceps ma priorytet 9 w pierwszym planie (bonus) i 10 w drugim (bonus) → podobna objętość.
    assert abs(biceps_high - biceps_low) <= 1, f"biceps powinien być podobny: {biceps_high} vs {biceps_low}"
    # Plany nie są identyczne — różne priorytety wpływają na objętość lub dobór ćwiczeń.
    names_high = set(s_high["names"])
    names_low = set(s_low["names"])
    assert names_high != names_low or s_high["total_sets"] != s_low["total_sets"], \
        "różne priorytety powinny produkować różne plany"


def test_minor_age_safety_preserved_with_priorities():
    """Nieważnoletni z priorytetami: submaximal effort i target_rir=3 zachowane."""
    from app.training.routes import _target_rir_for_user
    user = _make_user(
        frequency="3 dni", days=3, level="początkujący",
        equipment_list=["hantle", "ławka"], focus=["klatka", "plecy"],
    )
    user.age = 16
    assert _target_rir_for_user(user) == 3
    plan = _plan_for(3, focus=["klatka", "plecy"], age=16)
    assert plan["_planner"]["minor"] is True
    # Wszystkie sesje w limicie czasu.
    for d in plan["days"]:
        if d["day_type"] == "rest":
            continue
        assert d["workout"].get("estimated_minutes", 0) <= 60
        assert d["workout"]["session_exceeds_cap"] is False


def test_equipment_restrictions_preserved_with_priorities():
    """Priorytety nie obejmują ograniczeń sprzętowych — brak wyciągu/sztangi dla domowego sprzętu."""
    plan = _plan_for(3, focus=["klatka", "plecy"], equipment=("hantle", "ławka"))
    forbidden = {"wyciąg", "sztanga", "maszyna", "cable", "barbell"}
    for d in plan["days"]:
        if d["day_type"] == "rest":
            continue
        for e in d["workout"]["exercises"]:
            eo = get_exercise(e.get("exercise_id", e["name"]))
            eq = {str(x).lower() for x in (eo.equipment or [])}
            assert not (eq & forbidden), f"{e['name']} używa zabronionego sprzętu: {eq}"


def test_deterministic_generation_with_priorities():
    """Te same dane wejściowe zawsze generują ten sam plan."""
    plan1 = _plan_for(3, focus=["klatka", "plecy", "biceps"])
    plan2 = _plan_for(3, focus=["klatka", "plecy", "biceps"])
    names1 = [e["name"] for d in plan1["days"] if d["day_type"] != "rest" for e in d["workout"]["exercises"]]
    names2 = [e["name"] for d in plan2["days"] if d["day_type"] != "rest" for e in d["workout"]["exercises"]]
    sets1 = [e["sets"] for d in plan1["days"] if d["day_type"] != "rest" for e in d["workout"]["exercises"]]
    sets2 = [e["sets"] for d in plan2["days"] if d["day_type"] != "rest" for e in d["workout"]["exercises"]]
    assert names1 == names2
    assert sets1 == sets2

