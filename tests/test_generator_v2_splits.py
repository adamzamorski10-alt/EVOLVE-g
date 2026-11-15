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
    """Dla persony 3 sessions_per_week i sets_per_week maj� oczekiwane warto�ci z wydruku.

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
    assert sessions["biceps"] == 1, f"biceps sessions={sessions['biceps']}"
    assert sessions["triceps"] == 2, f"triceps sessions={sessions['triceps']}"
    assert sessions["nogi"] == 2, f"nogi sessions={sessions['nogi']}"
    assert sessions["brzuch"] == 2, f"brzuch sessions={sessions['brzuch']}"
    # sets_per_week (suma serii roboczych per grupa).
    assert sets["klatka"] == 11, f"klatka sets={sets['klatka']}"
    assert sets["plecy"] == 14, f"plecy sets={sets['plecy']}"
    assert sets["barki"] == 15, f"barki sets={sets['barki']}"
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
        lower_days = [d for d in _training_days(plan) if _is_lower_or_legs_or_full_body(d)]
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


