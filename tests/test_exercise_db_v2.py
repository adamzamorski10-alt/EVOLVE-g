"""Testy bazy ćwiczeń v2 — walidacja schematu, unikalność, pokrycie sprzętowe."""

from __future__ import annotations

import warnings

import pytest

warnings.filterwarnings("ignore")

from app.exercises.data import (
    CONTRAINDICATIONS,
    DESCRIPTION_STATUSES,
    EQUIPMENT,
    EXERCISE_TYPES,
    EXERCISES,
    LEVELS,
    MOVEMENT_PATTERNS,
    MUSCLE_GROUPS,
    MUSCLE_TO_GROUP,
    Exercise,
    get_exercise,
    list_exercises,
    muscle_group_for_exercise,
)
from app.plan.deterministic import _exercise_allowed

# ---------------------------------------------------------------------------
# 1. Walidacja schematu — wszystkie ćwiczenia przechodzą Pydantic
# ---------------------------------------------------------------------------


def test_all_exercises_pass_pydantic_validation():
    for ex in list_exercises():
        assert isinstance(ex, Exercise)
        assert ex.id
        assert ex.name_pl
        assert ex.name_en
        assert ex.movement_pattern in MOVEMENT_PATTERNS
        assert ex.level in LEVELS
        assert ex.type in EXERCISE_TYPES
        assert ex.description_status in DESCRIPTION_STATUSES
        for m in list(ex.primary_muscles) + list(ex.secondary_muscles):
            assert m in MUSCLE_GROUPS
        for e in ex.equipment:
            assert e in EQUIPMENT
        for c in ex.contraindications:
            assert c in CONTRAINDICATIONS


def test_ids_are_unique():
    ids = [ex.id for ex in list_exercises()]
    assert len(ids) == len(set(ids)), f"Duplikaty id: {[i for i in ids if ids.count(i) > 1]}"


def test_names_pl_are_unique():
    names = [ex.name_pl.strip().lower() for ex in list_exercises()]
    assert len(names) == len(set(names)), f"Duplikaty name_pl: {[n for n in names if names.count(n) > 1]}"


def test_no_empty_required_fields():
    for ex in list_exercises():
        assert ex.sets_range.strip(), f"Pusty sets_range dla {ex.id}"
        assert ex.reps_range.strip(), f"Pusty reps_range dla {ex.id}"


def test_description_status_is_valid():
    """description_status musi należeć do {needs_review, reviewed}."""
    for ex in list_exercises():
        assert ex.description_status in {"needs_review", "reviewed"}, \
            f"Nieprawidłowy description_status dla {ex.id}: {ex.description_status!r}"


def test_no_exercise_has_group_none():
    """Każde ćwiczenie musi mieć wyznaczoną grupę (nie None)."""
    for ex in list_exercises():
        group = muscle_group_for_exercise(ex)
        assert group is not None, f"Ćwiczenie {ex.id} nie ma grupy (primary_muscles={ex.primary_muscles})"


def test_rear_delts_maps_to_barki():
    """rear_delts mapuje wyłącznie na 'barki'."""
    assert MUSCLE_TO_GROUP["rear_delts"] == "barki"


def test_primary_group_is_first_muscle():
    """Grupa ćwiczenia = grupa pierwszego elementu primary_muscles."""
    for ex in list_exercises():
        if ex.primary_muscles:
            expected = MUSCLE_TO_GROUP.get(ex.primary_muscles[0])
            actual = muscle_group_for_exercise(ex)
            assert expected == actual, \
                f"{ex.id}: primary_muscles[0]={ex.primary_muscles[0]} -> {expected}, got {actual}"


def test_only_pl_en_characters():
    """Brak znaków spoza polskiego i angielskiego we wszystkich tekstach."""
    def ok(text: str) -> bool:
        if not text:
            return True
        for ch in text:
            code = ord(ch)
            if 32 <= code <= 126:
                continue
            if code in {176} | {260, 261, 262, 263, 280, 281, 321, 322, 323, 324, 243, 346, 347, 377, 378, 379, 380}:
                continue
            return False
        return True

    for ex in list_exercises():
        fields = [ex.name_pl, ex.name_en, *ex.aliases,
                  ex.description.summary, ex.description.setup, ex.description.breathing,
                  *ex.description.execution, *ex.description.cues, *ex.description.common_mistakes]
        for field in fields:
            assert ok(field), f"Niedozwolony znak w {ex.id}: {field!r}"


def test_app_plan_py_no_foreign_chars():
    """Stałe napisowe w app/plan/*.py nie zawierają znaków spoza polskiego i angielskiego."""
    import glob

    def ok(text: str) -> bool:
        if not text:
            return True
        for ch in text:
            code = ord(ch)
            if 32 <= code <= 126:
                continue
            if code in {176} | {260, 261, 262, 263, 280, 281, 321, 322, 323, 324, 243, 346, 347, 377, 378, 379, 380}:
                continue
            return False
        return True

    for path in sorted(glob.glob("app/plan/*.py")):
        with open(path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                for col, ch in enumerate(line, 1):
                    code = ord(ch)
                    if code in {9, 10, 13}:
                        continue
                    if code < 32 or code > 126:
                        if code not in {176} | {260, 261, 262, 263, 280, 281, 321, 322, 323, 324, 243, 346, 347, 377, 378, 379, 380}:
                            assert False, f"Niedozwolony znak U+{code:04X} w {path}:{line_no}:{col}"


# ---------------------------------------------------------------------------
# 2. Raport pokrycia: grupa mięśniowa x typ sprzętu
# ---------------------------------------------------------------------------

EQ_ALIASES_PL_EN = {
    "sztanga": "barbell", "sztanga olimpijska": "barbell",
    "hantle": "dumbbell", "hantle regulowane": "dumbbell",
    "kettlebell": "kettlebell",
    "maszyny": "machine", "maszyna": "machine",
    "wyciąg": "cable", "kabel": "cable",
    "ławka": "bench", "ławce": "bench",
    "drążek": "pullup_bar", "poręcz": "dip_station", "poręcze": "dip_station",
    "dip_station": "dip_station", "pullup_bar": "pullup_bar",
    "bands": "bands", "taśmy": "bands",
    "bodyweight": "bodyweight", "masa własna": "bodyweight",
    "siłownia": "gym", "gym": "gym",
    "talerz": "weight_plate", "talerze": "weight_plate",
    "koło brzuszkowe": "ab_wheel", "koło": "ab_wheel", "kółko brzuszkowe": "ab_wheel",
    "stół": "table_or_low_bar", "niski drążek": "table_or_low_bar", "drążek niski": "table_or_low_bar",
    "skakanka": "jump_rope", "skrzynia": "box",
}

# Masa własna: wymagane grupy (bez bicepsa)
BODYWEIGHT_GROUPS = ["chest", "back", "shoulders", "legs", "abs", "triceps"]
# Same hantle: wszystkie siedem grup
DUMBBELL_GROUPS = ["chest", "back", "shoulders", "biceps", "triceps", "abs", "legs"]
# Masa własna nogi: wymagane >=3 (tylko type != cardio, strict bodyweight)
BODYWEIGHT_LEGS_MIN = 3


def _primary_group(ex) -> str | None:
    g = set(ex.primary_muscles)
    if "chest" in g:
        return "chest"
    if g & {"back", "lats", "traps", "rear_delts", "lower_back"}:
        return "back"
    if g & {"front_delts", "side_delts"}:
        return "shoulders"
    if g & {"quads", "hamstrings", "glutes", "calves"}:
        return "legs"
    if "biceps" in g:
        return "biceps"
    if "triceps" in g:
        return "triceps"
    if g & {"abs", "obliques"}:
        return "abs"
    return None


def _equip_en(equip_list) -> set[str]:
    return {EQ_ALIASES_PL_EN.get(e.strip().lower(), e.strip().lower())
            for e in equip_list if e and e.strip()}


def _allowed(ex, equip_en: set[str]) -> bool:
    """Używa tej samej funkcji filtrowania co generator (_exercise_allowed)."""
    name = ex.name_pl
    equipment = set(equip_en)
    return _exercise_allowed(name, equipment, [])


def _coverage_report(equip_list, exclude_cardio: bool = False) -> dict[str, list[str]]:
    equip_en = _equip_en(equip_list)
    all_groups = sorted(set(BODYWEIGHT_GROUPS + DUMBBELL_GROUPS))
    by_group: dict[str, list[str]] = {g: [] for g in all_groups}
    for ex in list_exercises():
        if _allowed(ex, equip_en):
            if exclude_cardio and ex.type == "cardio":
                continue
            g = _primary_group(ex)
            if g:
                by_group[g].append(ex.name_pl)
    return by_group


def test_coverage_report_bodyweight():
    """Masa własna: >=2 ćwiczeń na klatkę, plecy, barki, brzuch, triceps; nogi >=3 (tylko type != cardio, strict bodyweight)."""
    report = _coverage_report(["bodyweight"], exclude_cardio=True)
    missing = {}
    for g in BODYWEIGHT_GROUPS:
        if g == "legs":
            if len(report[g]) < BODYWEIGHT_LEGS_MIN:
                missing[g] = report[g]
        elif len(report[g]) < 2:
            missing[g] = report[g]
    if missing:
        pytest.fail(
            "Niewystarczające pokrycie masą własną: "
            + "; ".join(f"{g} ma {len(v)}" for g, v in missing.items())
        )


def test_coverage_report_dumbbells():
    """Same hantle: >=2 ćwiczeń dla wszystkich siedmiu grup."""
    report = _coverage_report(["hantle"])
    missing = {g: exs for g, exs in report.items() if g in DUMBBELL_GROUPS and len(exs) < 2}
    if missing:
        pytest.fail(
            "Niewystarczające pokrycie samymi hantlami: "
            + "; ".join(f"{g} ma {len(v)}" for g, v in missing.items())
        )


def test_coverage_report_dumbbells_bench():
    """Hantle + ławka: raport pokrycia (nie failuje — to Referencja)."""
    report = _coverage_report(["hantle", "ławka"])
    low = [g for g in DUMBBELL_GROUPS if len(report[g]) < 2]
    assert not low, f"Grupy poniżej 2: {low}"


def test_coverage_report_full_gym():
    """Pełna siłownia: raport pokrycia (referencja)."""
    report = _coverage_report([
        "sztanga", "hantle", "ławka", "maszyny", "wyciąg", "drążek", "poręcz", "kettlebell",
    ])
    low = [g for g in DUMBBELL_GROUPS if len(report[g]) < 2]
    assert not low, f"Grupy poniżej 2: {low}"
