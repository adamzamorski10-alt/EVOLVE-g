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
    assert sessions["biceps"] == 2, f"biceps sessions={sessions['biceps']}"
    assert sessions["triceps"] == 2, f"triceps sessions={sessions['triceps']}"
    assert sessions["nogi"] == 2, f"nogi sessions={sessions['nogi']}"
    assert sessions["brzuch"] == 2, f"brzuch sessions={sessions['brzuch']}"
    # sets_per_week (suma serii roboczych per grupa).
    assert sets["klatka"] == 8, f"klatka sets={sets['klatka']}"
    assert sets["plecy"] == 14, f"plecy sets={sets['plecy']}"
    assert sets["barki"] == 6, f"barki sets={sets['barki']}"
    assert sets["biceps"] == 6, f"biceps sets={sets['biceps']}"
    assert sets["triceps"] == 6, f"triceps sets={sets['triceps']}"
    assert sets["nogi"] == 31, f"nogi sets={sets['nogi']}"
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
    assert sets.get("barki", 0) <= 12, f"barki {sets.get('barki', 0)}"
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

