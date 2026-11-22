"""Testy jakości bazy ćwiczeń (app/exercises/data.py)."""

from __future__ import annotations

import re

import pytest

from app.exercises.data import EXERCISES, MUSCLE_GROUPS


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _exercise_has_complete_description(ex) -> bool:
    """Ćwiczenie ma kompletny opis: summary, setup, conajmniej 1 krok execution,
    conajmniej 1 cue, conajmniej 1 błąd, breathing."""
    desc = ex.description
    if not desc or not desc.summary.strip():
        return False
    if not desc.setup.strip():
        return False
    if not desc.execution or len(desc.execution) < 1:
        return False
    if not desc.cues or len(desc.cues) < 1:
        return False
    if not desc.common_mistakes or len(desc.common_mistakes) < 1:
        return False
    if not desc.breathing.strip():
        return False
    return True


# ---------------------------------------------------------------------------
# TESTY
# ---------------------------------------------------------------------------

def test_reviewed_exercises_have_complete_descriptions():
    """Każde ćwiczenie z description_status='reviewed' musi mieć kompletny opis."""
    incomplete = []
    for eid, ex in EXERCISES.items():
        if ex.description_status == "reviewed" and not _exercise_has_complete_description(ex):
            incomplete.append(eid)
    assert not incomplete, (
        f"Ćwiczenia ze statusem 'reviewed' mają niekompletne opisy: {incomplete}"
    )


def test_isometric_exercises_use_seconds():
    """Ćwiczenia izometryczne (core, isolation bez ruchu dynamicznego) powinny
    określać czas w reps_range (zawiera 's'), a nie liczbę powtórzeń."""
    isometric_ids = {"plank", "side_plank", "hollow_body_hold", "wall_sit"}
    for eid in isometric_ids:
        ex = EXERCISES.get(eid)
        assert ex is not None, f"Brak ćwiczenia {eid} w bazie"
        assert "s" in ex.reps_range, (
            f"{eid}: reps_range={ex.reps_range!r} nie zawiera czasu (s) dla ćwiczenia izometrycznego"
        )


def test_reps_range_is_valid_format():
    """Zakres powtórzeń ma poprawny format: 'X-Y', 'X/strona', 'X s', 'X-Y s',
    'X runda', 'X min', '20 s sprint / 10 s odpocz.' itp."""
    valid_patterns = [
        r"^\d+-\d+$",                       # 8-12
        r"^\d+-\d+/strona$",                # 12-15/strona
        r"^\d+/strona$",                    # 10/strona
        r"^\d+ s$",                         # 45 s
        r"^\d+-\d+ s$",                     # 30-45 s
        r"^\d+-\d+s$",                      # 20-30s
        r"^\d+ runda$",                     # 1 runda
        r"^\d+ min$",                       # 20 min
        r"^\d+$",                           # 15 (pojedyncza liczba)
        r"^\d+ s sprint / \d+ s odpocz\.$", # 20 s sprint / 10 s odpocz.
    ]
    compiled = [re.compile(p) for p in valid_patterns]
    invalid = []
    for eid, ex in EXERCISES.items():
        rr = ex.reps_range.strip()
        if not any(p.match(rr) for p in compiled):
            invalid.append((eid, rr))
    assert not invalid, f"Nieprawidłowe reps_range: {invalid}"


def test_secondary_muscles_are_valid():
    """secondary_muscles zawierają wyłącznie wartości z MUSCLE_GROUPS."""
    invalid = []
    for eid, ex in EXERCISES.items():
        for m in ex.secondary_muscles:
            if m not in MUSCLE_GROUPS:
                invalid.append((eid, m))
    assert not invalid, f"Nieprawidłowe secondary_muscles: {invalid}"


def test_secondary_muscles_not_duplicate_primary():
    """secondary_muscles nie powinny zawierać tego samego mięśnia co primary_muscles[0]."""
    invalid = []
    for eid, ex in EXERCISES.items():
        if not ex.primary_muscles:
            continue
        primary = ex.primary_muscles[0]
        if primary in ex.secondary_muscles:
            invalid.append((eid, primary))
    assert not invalid, f"secondary_muscles duplikuje primary: {invalid}"


def test_equipment_matches_declared():
    """Każde ćwiczenie ma zadeklarowane equipment (walidacja Pydantic już to robi,
    ale test potwierdza, że nie ma pustych list equipment)."""
    missing = []
    for eid, ex in EXERCISES.items():
        if not ex.equipment:
            missing.append(eid)
    assert not missing, f"Ćwiczenia bez equipment: {missing}"


def test_description_status_matches_completeness():
    """Ćwiczenia ze statusem 'needs_review' mogą mieć puste opisy, ale
    'reviewed' musi mieć kompletne dane. Sprawdzamy odwrotnie: jeśli opis
    jest kompletny, status powinien być 'reviewed' (lub co najmniej nie
    powinniśmy mieć 'reviewed' z pustym opisem - już testowane wyżej)."""
    # Ćwiczenia z pustym summary powinny mieć needs_review
    for eid, ex in EXERCISES.items():
        if ex.description_status == "reviewed":
            assert ex.description.summary.strip(), (
                f"{eid}: status 'reviewed' ale pusty summary"
            )
            assert ex.description.setup.strip(), (
                f"{eid}: status 'reviewed' ale pusty setup"
            )


def test_critical_home_exercises_have_complete_descriptions():
    """Cztery kluczowe ćwiczenia domowe muszą mieć kompletne opisy po uzupełnieniu."""
    critical_ids = [
        "dumbbell_bench_press",
        "incline_dumbbell_press",
        "plank",
        "dead_bug",
    ]
    for eid in critical_ids:
        ex = EXERCISES.get(eid)
        assert ex is not None, f"{eid} nie znajduje się w bazie ćwiczeń"
        assert ex.description_status == "reviewed", (
            f"{eid}: oczekiwano statusu 'reviewed', otrzymano '{ex.description_status}'"
        )
        d = ex.description
        assert d.summary.strip(), f"{eid}: pusty summary"
        assert d.setup.strip(), f"{eid}: pusty setup"
        assert d.execution and len(d.execution) >= 1, f"{eid}: brak kroków execution"
        assert d.cues and len(d.cues) >= 1, f"{eid}: brak cues"
        assert d.common_mistakes and len(d.common_mistakes) >= 1, f"{eid}: brak common_mistakes"
        assert d.breathing.strip(), f"{eid}: pusty breathing"

