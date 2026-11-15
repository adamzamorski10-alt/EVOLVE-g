"""Generator v2: szablony sesji oparte na wzorcach ruchu (splity).

Zastępuje model "jedna partia na dzień" szablonami opartymi na wzorcach ruchu,
tak aby główne grupy mięśniowe były trenowane około 2 razy w tygodniu.
Format wyjścia jest kompatybilny z build_deterministic_plan (struktura dni,
ćwiczeń, serie, powtórzenia) aby adaptacja, historia treningów i interfejs
działały bez zmian.
"""

from __future__ import annotations

import os
import re
from typing import Any

from app.exercises.data import (
    get_exercise,
    list_exercises,
    MUSCLE_TO_GROUP,
    SELECTION_RANK,
)
from app.exercises.loader import build_exercise_pool, KNOWN_GROUPS
from app.legacy_routes import (
    _MUSCLE_MAP,
    _day_type,
    _default_meal_catalog,
    calc_daily_macros,
)

PLAN_GENERATOR = os.environ.get("PLAN_GENERATOR", "v2").strip().lower()

# ---------------------------------------------------------------------------
# Dni treningowe z przerwami (rozkład w tygodniu, Pon-Sob; Niedziela = spoczynek)
# ---------------------------------------------------------------------------
_SPLIT_DAYS: dict[int, list[str]] = {
    1: ["Poniedziałek"],
    2: ["Poniedziałek", "Czwartek"],
    3: ["Poniedziałek", "Środa", "Piątek"],
    4: ["Poniedziałek", "Wtorek", "Czwartek", "Piątek"],
    5: ["Poniedziałek", "Wtorek", "Środa", "Piątek", "Sobota"],
    6: ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota"],
}

_WEEKDAY_ORDER = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota"]

# ---------------------------------------------------------------------------
# Cele objętości (serie robocze w tygodniu) dla celu "masa", poziom intermediate.
# Klucz: primary_muscle (angielski klucz mięśnia). Wartość: (min, max).
# Początkujący: około 30 procent niższe (zaokrąglone w dół).
# ---------------------------------------------------------------------------
VOLUME_TARGETS_INTERMEDIATE: dict[str, tuple[int, int]] = {
    "chest": (10, 14),
    "back": (12, 16),
    "side_delts": (8, 12),
    "biceps": (6, 10),
    "triceps": (6, 10),
    "quads": (10, 14),
    "hamstrings": (8, 12),
    "calves": (6, 10),
}

_MUSCLE_TO_VOLUME_SUBGROUP: dict[str, str] = {
    "chest": "chest",
    "back": "back",
    "lats": "back",
    "upper_back": "back",
    "mid_back": "back",
    "lower_back": "back",
    "traps": "back",
    "front_delts": "side_delts",
    "side_delts": "side_delts",
    "rear_delts": "side_delts",
    "biceps": "biceps",
    "triceps": "triceps",
    "quads": "quads",
    "hamstrings": "hamstrings",
    "glutes": "hamstrings",
    "calves": "calves",
    "abs": "brzuch",
    "obliques": "brzuch",
}

_MUSCLE_TO_SUMMARY_GROUP: dict[str, str] = {
    "chest": "klatka",
    "back": "plecy",
    "lats": "plecy",
    "upper_back": "plecy",
    "mid_back": "plecy",
    "lower_back": "plecy",
    "traps": "plecy",
    "front_delts": "barki",
    "side_delts": "barki",
    "rear_delts": "barki",
    "biceps": "biceps",
    "triceps": "triceps",
    "quads": "nogi",
    "hamstrings": "nogi",
    "glutes": "nogi",
    "calves": "nogi",
    "abs": "brzuch",
    "obliques": "brzuch",
}

_SUMMARY_GROUPS = ["klatka", "plecy", "barki", "biceps", "triceps", "nogi", "brzuch"]

_DESCRIBED_EXERCISES: set[str] | None = None


def _described_exercise_ids() -> set[str]:
    global _DESCRIBED_EXERCISES
    if _DESCRIBED_EXERCISES is None:
        _DESCRIBED_EXERCISES = set()
        for ex in list_exercises():
            desc = ex.description
            if desc is None:
                continue
            d = desc.model_dump() if hasattr(desc, "model_dump") else dict(desc)
            summary = str(d.get("summary") or "").strip()
            execution = d.get("execution") or []
            cues = d.get("cues") or []
            mistakes = d.get("common_mistakes") or []
            if summary and execution and cues and mistakes:
                _DESCRIBED_EXERCISES.add(ex.id)
    return _DESCRIBED_EXERCISES


def _normalize_weekday(value: Any) -> str | None:
    """Normalize supported Polish weekday labels to the planner's canonical names."""
    normalized = str(value or "").strip().casefold().rstrip(".")
    aliases = {
        "pon": "Poniedziałek", "poniedzialek": "Poniedziałek", "poniedziałek": "Poniedziałek",
        "wt": "Wtorek", "wto": "Wtorek", "wtorek": "Wtorek",
        "sr": "Środa", "śr": "Środa", "sroda": "Środa", "środa": "Środa",
        "czw": "Czwartek", "czwartek": "Czwartek",
        "pt": "Piątek", "piatek": "Piątek", "piątek": "Piątek",
        "sob": "Sobota", "sobota": "Sobota",
        "nd": "Niedziela", "ndz": "Niedziela", "niedz": "Niedziela", "niedziela": "Niedziela",
    }
    return aliases.get(normalized)


def _assessment_value(assessment: Any, field: str, default: Any = None) -> Any:
    return getattr(assessment, field, default) if assessment is not None else default


def _frequency_days(value: str | None) -> int:
    numbers = [int(x) for x in re.findall(r"\d+", str(value or ""))]
    if not numbers:
        return 3
    return max(1, min(6, max(numbers)))


def _normalized_constraints(items: list[str]) -> list[str]:
    return [
        item.strip().lower()
        for item in items
        if isinstance(item, str) and item.strip()
    ]


def _meal_slots(meals_per_day: int) -> list[str]:
    slots = ["Śniadanie", "Obiad", "Kolacja"]
    if meals_per_day >= 4:
        slots.insert(1, "Przekąska 1")
    if meals_per_day >= 5:
        slots.insert(3, "Przekąska 2")
    return slots


def _parse_sets(sets_range: str | None, is_first_compound: bool) -> int:
    """Zamienia zakres serii (np. '4-6') na jedną liczbę całkowitą.

    Pierwsze ćwiczenie złożone sesji dostaje górną wartość zakresu,
    pozostałe dolną. Pojedyncza liczba jest używana bez zmian.
    Zwraca zawsze int.
    """
    if not sets_range:
        return 3
    match = re.fullmatch(r"\s*(\d+)\s*-\s*(\d+)\s*", str(sets_range))
    if match:
        low = int(match.group(1))
        high = int(match.group(2))
        return high if is_first_compound else low
    single = re.search(r"\d+", str(sets_range))
    return int(single.group()) if single else 3


def _level_allowed(level: str, training_level: str | None) -> bool:
    if not training_level:
        return True
    tl = str(training_level).strip().casefold()
    if tl in {"początkujący", "beginner"}:
        return level == "beginner"
    if tl in {"średniozaawansowany", "intermediate"}:
        return level != "advanced"
    if tl in {"zaawansowany", "advanced", "elite"}:
        return True
    return True


def _exercise_equipment_en(name: str) -> set[str] | None:
    ex = get_exercise(name)
    if ex is None:
        key = name.strip().lower()
        for candidate in list_exercises():
            if candidate.name_pl.strip().lower() == key:
                ex = candidate
                break
            if any(a.strip().lower() == key for a in candidate.aliases):
                ex = candidate
                break
    if ex is None:
        return None
    return set(ex.equipment)


def _exercise_allowed(name: str, equipment: set[str], avoid_exercises: list[str]) -> bool:
    lowered = name.lower()
    if any(term.lower() in lowered for term in avoid_exercises if term):
        return False
    if "gym" in equipment:
        return True
    if not equipment:
        req = _exercise_equipment_en(name)
        if req is not None:
            return req <= {"bodyweight"}
        return False
    req = _exercise_equipment_en(name)
    if req is not None:
        if req <= {"bodyweight"}:
            return True
        return req.issubset(equipment)
    required: set[str] = set()
    n = lowered
    if "sztang" in n:
        required.add("barbell")
    if "hantl" in n:
        required.add("dumbbell")
    if "kettlebell" in n:
        required.add("kettlebell")
    if any(token in n for token in ("maszyn", "leg press", "pec deck", "hammer")):
        required.add("machine")
    if any(token in n for token in ("kabel", "brama")):
        required.add("cable")
    if "poręcz" in n or "dip" in n:
        required.add("dip_station")
    if "drążek" in n or "pullup" in n or "podciąg" in n:
        required.add("pullup_bar")
    if "ławce" in n or "ławka" in n:
        required.add("bench")
    return required.issubset(equipment)


def _equipment_aliases(items: list[str]) -> set[str]:
    out: set[str] = set()
    _EQUIPMENT_PL_TO_EN: dict[str, str] = {
        "sztanga": "barbell", "sztanga olimpijska": "barbell",
        "hantle": "dumbbell", "hantle regulowane": "dumbbell",
        "kettlebell": "kettlebell", "maszyny": "machine", "maszyna": "machine",
        "wyciąg": "cable", "kabel": "cable", "ławka": "bench", "ławce": "bench",
        "drążek": "pullup_bar", "poręcz": "dip_station", "poręcze": "dip_station",
        "dip_station": "dip_station", "pullup_bar": "pullup_bar",
        "bands": "bands", "taśmy": "bands", "bodyweight": "bodyweight",
        "masa własna": "bodyweight", "talerz": "weight_plate", "talerze": "weight_plate",
        "koło brzuszkowe": "ab_wheel", "koło": "ab_wheel", "kółko brzuszkowe": "ab_wheel",
        "stół": "table_or_low_bar", "niski drążek": "table_or_low_bar",
        "drążek niski": "table_or_low_bar", "siłownia": "gym", "gym": "gym", "full": "gym",
    }
    for item in items:
        if not item or not item.strip():
            continue
        key = item.strip().lower()
        out.add(_EQUIPMENT_PL_TO_EN.get(key, key))
    return out


def _selection_rank_key(ex: Any) -> tuple[int, int, str]:
    """Klucz sortowania slotu: selection_rank (jawny priorytet), bonus za
    kompletny opis, potem stabilnie po id."""
    ex_id = ex.id
    rank = 999
    pattern_ranks = SELECTION_RANK.get(ex.movement_pattern, {})
    if ex_id in pattern_ranks:
        rank = pattern_ranks[ex_id]
    desc_bonus = 0 if ex_id in _described_exercise_ids() else 1
    return (rank, desc_bonus, ex_id)


def _available_weekdays(configured_availability: list[str] | None) -> list[str]:
    if configured_availability:
        available = {
            _normalize_weekday(d)
            for d in configured_availability
            if _normalize_weekday(d) in _WEEKDAY_ORDER
        }
        return [d for d in _WEEKDAY_ORDER if d in available]
    return list(_WEEKDAY_ORDER)


def _select_training_days(
    num_days: int,
    configured_availability: list[str] | None,
) -> tuple[list[str], list[str]]:
    """Wybiera dni treningowe z przerwami. Zwraca (dni, diagnostyki)."""
    diagnostics: list[str] = []
    if configured_availability:
        available = _available_weekdays(configured_availability)
        available = [d for d in available if d != "Niedziela"]
        if not available:
            available = list(_WEEKDAY_ORDER)
        selected = available[:num_days]
        if len(selected) < num_days:
            diagnostics.append(
                f"Zadeklarowana dostępność umożliwia tylko {len(selected)} z {num_days} "
                f"żądanych dni treningowych."
            )
        return selected, diagnostics
    selected = list(_SPLIT_DAYS.get(num_days, _SPLIT_DAYS[3]))
    return selected, diagnostics


def _split_key(num_days: int, training_level: str | None) -> str:
    tl = (training_level or "").strip().casefold()
    if num_days == 1:
        return "full_body_1"
    if num_days == 2:
        return "full_body_2"
    if num_days == 3:
        if tl in {"zaawansowany", "advanced", "elite"}:
            return "upper_lower_full_3"
        return "full_body_3"
    if num_days == 4:
        return "upper_lower_4"
    if num_days == 5:
        return "upper_lower_push_pull_legs_5"
    if num_days == 6:
        return "push_pull_legs_x2_6"
    return "full_body_1"


# ---------------------------------------------------------------------------
# Szablony sesji jako sloty (wzorzec ruchu, grupa mięśniowa, typ ćwiczenia).
# typ: "compound" lub "isolation".
# ---------------------------------------------------------------------------
SLOT_TEMPLATES: dict[str, list[dict[str, Any]]] = {
    "full_body_a": [
        {"pattern": "squat", "group": "nogi", "kind": "compound"},
        {"pattern": "horizontal_push", "group": "klatka", "kind": "compound"},
        {"pattern": "horizontal_pull", "group": "plecy", "kind": "compound"},
        {"pattern": "isolation", "group": "barki", "kind": "isolation", "prefer_ids": ["lateral_raise"], "sets": 3},
        {"pattern": "isolation", "group": "nogi", "kind": "isolation", "prefer_ids": ["standing_calf_raise"], "sets": 3},
        {"pattern": "core", "group": "brzuch", "kind": "isolation", "sets": 3},
    ],
    "full_body_b": [
        {"pattern": "hinge", "group": "nogi", "kind": "compound"},
        {"pattern": "vertical_push", "group": "barki", "kind": "compound"},
        {"pattern": "vertical_pull", "group": "plecy", "kind": "compound"},
        {"pattern": "core", "group": "brzuch", "kind": "isolation", "sets": 3},
        {"pattern": "isolation", "group": "nogi", "kind": "isolation", "prefer_ids": ["standing_calf_raise"], "sets": 3},
        {"pattern": "horizontal_push", "group": "klatka", "kind": "compound"},
    ],
    "upper_a": [
        {"pattern": "horizontal_push", "group": "klatka", "kind": "compound"},
        {"pattern": "horizontal_pull", "group": "plecy", "kind": "compound"},
        {"pattern": "vertical_push", "group": "barki", "kind": "compound"},
        {"pattern": "vertical_pull", "group": "plecy", "kind": "compound"},
        {"pattern": "isolation", "group": "barki", "kind": "isolation", "prefer_ids": ["lateral_raise"], "sets": 3},
        {"pattern": "isolation", "group": "barki", "kind": "isolation", "prefer_ids": ["face_pull"], "sets": 3},
        {"pattern": "isolation", "group": "klatka", "kind": "isolation", "prefer_ids": ["cable_crossover", "pec_deck"], "sets": 3},
        {"pattern": "isolation", "group": "triceps", "kind": "isolation", "sets": 3},
    ],
    "upper_b": [
        {"pattern": "horizontal_push", "group": "klatka", "kind": "compound"},
        {"pattern": "vertical_pull", "group": "plecy", "kind": "compound"},
        {"pattern": "horizontal_pull", "group": "plecy", "kind": "compound"},
        {"pattern": "isolation", "group": "barki", "kind": "isolation", "prefer_ids": ["lateral_raise"], "sets": 3},
        {"pattern": "isolation", "group": "barki", "kind": "isolation", "prefer_ids": ["rear_delt_fly"], "sets": 3},
        {"pattern": "isolation", "group": "biceps", "kind": "isolation", "prefer_ids": ["cable_curl", "barbell_curl"], "sets": 3},
        {"pattern": "isolation", "group": "biceps", "kind": "isolation", "prefer_ids": ["hammer_curl"], "sets": 3},
        {"pattern": "isolation", "group": "triceps", "kind": "isolation", "sets": 3},
    ],
    "lower_a": [
        {"pattern": "squat", "group": "nogi", "kind": "compound"},
        {"pattern": "hinge", "group": "nogi", "kind": "compound"},
        {"pattern": "lunge", "group": "nogi", "kind": "compound"},
        {"pattern": "isolation", "group": "nogi", "kind": "isolation", "prefer_ids": ["leg_curl"], "sets": 3},
        {"pattern": "isolation", "group": "nogi", "kind": "isolation", "prefer_ids": ["standing_calf_raise"], "sets": 3},
        {"pattern": "core", "group": "brzuch", "kind": "isolation", "sets": 3},
    ],
    "lower_b": [
        {"pattern": "hinge", "group": "nogi", "kind": "compound"},
        {"pattern": "squat", "group": "nogi", "kind": "compound", "prefer_ids": ["leg_press", "front_squat"]},
        {"pattern": "lunge", "group": "nogi", "kind": "compound", "prefer_ids": ["reverse_lunge"]},
        {"pattern": "isolation", "group": "nogi", "kind": "isolation", "prefer_ids": ["leg_curl", "leg_extension"], "sets": 3},
        {"pattern": "isolation", "group": "nogi", "kind": "isolation", "prefer_ids": ["standing_calf_raise"], "sets": 3},
        {"pattern": "core", "group": "brzuch", "kind": "isolation", "sets": 3},
    ],
    "push": [
        {"pattern": "horizontal_push", "group": "klatka", "kind": "compound"},
        {"pattern": "vertical_push", "group": "barki", "kind": "compound"},
        {"pattern": "isolation", "group": "klatka", "kind": "isolation", "prefer_ids": ["cable_crossover", "pec_deck"], "sets": 3},
        {"pattern": "isolation", "group": "barki", "kind": "isolation", "prefer_ids": ["lateral_raise"], "sets": 3},
        {"pattern": "isolation", "group": "triceps", "kind": "isolation", "sets": 3},
        {"pattern": "isolation", "group": "triceps", "kind": "isolation", "sets": 3},
    ],
    "pull": [
        {"pattern": "horizontal_pull", "group": "plecy", "kind": "compound"},
        {"pattern": "vertical_pull", "group": "plecy", "kind": "compound"},
        {"pattern": "isolation", "group": "barki", "kind": "isolation", "prefer_ids": ["face_pull", "rear_delt_fly"], "sets": 3},
        {"pattern": "isolation", "group": "biceps", "kind": "isolation", "prefer_ids": ["cable_curl", "barbell_curl"], "sets": 3},
        {"pattern": "isolation", "group": "biceps", "kind": "isolation", "prefer_ids": ["hammer_curl"], "sets": 3},
    ],
    "legs": [
        {"pattern": "squat", "group": "nogi", "kind": "compound", "prefer_ids": ["leg_press", "front_squat"]},
        {"pattern": "hinge", "group": "nogi", "kind": "compound"},
        {"pattern": "lunge", "group": "nogi", "kind": "compound"},
        {"pattern": "isolation", "group": "nogi", "kind": "isolation", "prefer_ids": ["leg_curl", "leg_extension"], "sets": 3},
        {"pattern": "isolation", "group": "nogi", "kind": "isolation", "prefer_ids": ["standing_calf_raise"], "sets": 3},
        {"pattern": "core", "group": "brzuch", "kind": "isolation", "sets": 3},
    ],
}

SPLIT_TEMPLATES: dict[str, list[str]] = {
    "full_body_1": ["full_body_a"],
    "full_body_2": ["full_body_a", "full_body_b"],
    "full_body_3": ["full_body_a", "full_body_b", "full_body_a"],
    "upper_lower_full_3": ["upper_a", "lower_a", "full_body_a"],
    "upper_lower_4": ["upper_a", "lower_a", "upper_b", "lower_b"],
    "upper_lower_push_pull_legs_5": ["upper_a", "lower_a", "push", "pull", "legs"],
    "push_pull_legs_x2_6": ["push", "pull", "legs", "push", "pull", "legs"],
}


def _exercise_limit(training_level: str | None, recovery: Any = None, hours: Any = None,
                    target_days: int = 0) -> int:
    tl = (training_level or "").strip().casefold()
    limit = 7 if tl in {"średniozaawansowany", "intermediate"} else 5
    if recovery is not None:
        try:
            r = int(recovery)
            if r <= 4:
                limit = min(limit, 3)
            elif r <= 6:
                limit = min(limit, 4)
        except (TypeError, ValueError):
            pass
    if hours is not None and target_days:
        try:
            if float(hours) / target_days < 0.75:
                limit = min(limit, 4)
        except (TypeError, ValueError):
            pass
    return limit


def _volume_targets(training_level: str | None) -> dict[str, tuple[int, int]]:
    tl = (training_level or "").strip().casefold()
    beginner = tl in {"początkujący", "beginner"}
    targets: dict[str, tuple[int, int]] = {}
    for muscle, (low, high) in VOLUME_TARGETS_INTERMEDIATE.items():
        if beginner:
            low = max(1, int(round(low * 0.7)))
            high = max(low, int(round(high * 0.7)))
        targets[muscle] = (low, high)
    return targets


def _summary_group(primary_muscles: list[str]) -> str:
    if not primary_muscles:
        return ""
    return _MUSCLE_TO_SUMMARY_GROUP.get(primary_muscles[0], "")


def _volume_subgroup(primary_muscles: list[str]) -> str | None:
    if not primary_muscles:
        return None
    return _MUSCLE_TO_VOLUME_SUBGROUP.get(primary_muscles[0])


def _is_bodyweight(ex: dict[str, Any]) -> bool:
    ex_obj = get_exercise(ex.get("exercise_id", ex["name"]))
    return ex_obj is not None and set(ex_obj.equipment or []) <= {"bodyweight"}


def _fill_slot(
    slot: dict[str, Any],
    pool: dict[str, list[dict[str, Any]]],
    equipment: set[str],
    avoid_exercises: list[str],
    training_level: str | None,
    used_names: set[str],
    used_patterns_in_session: dict[str, int],
    used_primary_muscles_in_session: dict[str, int],
    used_families_in_session: set[str],
    exclude_names: set[str] | None,
    has_equipment_preset: bool,
    session_isolation_ids: set[str] | None = None,
    session_focus: str | None = None,
    used_names_global: set[str] | None = None,
    volume_sets: dict[str, int] | None = None,
) -> dict[str, Any] | None:
    """Wypełnia jeden slot ćwiczeniem z puli.

    Filtruje po poziomie i sprzęcie, potem sortuje po selection_rank (jawny priorytet),
    bonusie za kompletny opis i na końcu po id. Ćwiczenie masy własnej jest wybierane
    przy sprzęcie siłownia/hantle tylko gdy nie ma dozwolonego ćwiczenia ze sprzętem
    w tym wzorcu.
    """
    prefer_ids = slot.get("prefer_ids") or []
    pattern = slot["pattern"]
    group = slot["group"]
    kind = slot.get("kind")

    # Ćwiczenia zablokowane dla tej sesji (np. rear_delt_fly/face_pull poza upper/pull).
    blocked_in_session: set[str] = set()
    if session_focus not in ("upper_a", "upper_b", "pull"):
        blocked_in_session.update({"rear_delt_fly", "face_pull"})

    candidates: list[dict[str, Any]] = []
    for ex in pool.get(group, []):
        ex_obj = get_exercise(ex.get("exercise_id", ex["name"]))
        if ex_obj is None:
            continue
        if ex["name"] in used_names or ex["name"] in exclude_names:
            continue
        if ex_obj.id in blocked_in_session:
            continue
        # R9: nie łącz pompek klasycznych z kolanymi w jednym tygodniu
        if used_names_global:
            if ex_obj.id == "pushups_knee" and any(get_exercise(n) and get_exercise(n).id == "pushups_classic" for n in used_names_global):
                continue
            if ex_obj.id == "pushups_classic" and any(get_exercise(n) and get_exercise(n).id == "pushups_knee" for n in used_names_global):
                continue
        if not _exercise_allowed(ex["name"], equipment, avoid_exercises):
            continue
        if ex_obj.type == "cardio":
            continue
        if "plyometric" in (getattr(ex_obj, "tags", None) or []):
            continue
        if not _level_allowed(ex_obj.level, training_level):
            continue
        if pattern != "isolation" and ex_obj.movement_pattern != pattern:
            continue
        if kind == "isolation" and ex_obj.type != "isolation":
            continue
        if kind == "compound" and ex_obj.type != "compound":
            continue
        # R1: front_raise tylko gdy brak innej izolacji barków w sesji.
        if ex_obj.id == "front_raise":
            shoulder_isos = {"lateral_raise", "rear_delt_fly", "face_pull"}
            if session_isolation_ids and (session_isolation_ids & shoulder_isos):
                continue
        # Max 2 ćwiczenia tego samego wzorca ruchu w sesji (poza izolacjami).
        if ex_obj.type != "isolation":
            if used_patterns_in_session.get(ex_obj.movement_pattern, 0) >= 2:
                continue
        # Max 2 ćwiczenia tego samego primary_muscles w sesji (dla compound).
        # Dla isolation podniesiony limit do 3, bo np. squat+lunge (quads x2) + leg_curl musi przejść.
        pm = ex_obj.primary_muscles[0] if ex_obj.primary_muscles else ""
        pm_limit = 3 if (kind == "isolation" or ex_obj.type == "isolation") else 2
        if used_primary_muscles_in_session.get(pm, 0) >= pm_limit:
            continue
        # Max 1 ćwiczenie z tej samej rodziny w sesji.
        fam = getattr(ex_obj, "family", None)
        if fam and fam in used_families_in_session:
            continue
        # Planer objętości: jeśli ćwiczenie izolacji przekroczy limit górny (R11), pomiń
        if ex_obj.type == "isolation" and volume_sets is not None:
            is_beg = str(training_level or "").strip().casefold() in {"początkujący", "beginner"}
            sg = _volume_subgroup(ex_obj.primary_muscles)
            if sg and sg in VOLUME_TARGETS_INTERMEDIATE:
                base_h = VOLUME_TARGETS_INTERMEDIATE[sg][1] * (0.7 if is_beg else 1.0)
                max_al = base_h * 1.25
                est_s = slot.get("sets") or 3
                if is_beg:
                    est_s = min(est_s, 3)
                    if "calves" in (ex_obj.primary_muscles or []):
                        est_s = min(est_s, 2)
                if volume_sets.get(sg, 0) + est_s > max_al:
                    continue
        candidates.append(ex)

    if not candidates:
        return None

    # Jeśli slot ma preferowane id, spróbuj najpierw znaleźć ich dopasowanie
    # (po filtrowaniu poziomu/sprzętu już dokonanym powyżej).
    if prefer_ids:
        for pid in prefer_ids:
            for ex in candidates:
                ex_obj = get_exercise(ex.get("exercise_id", ex["name"]))
                if ex_obj and ex_obj.id == pid:
                    return ex

    # Przy sprzęcie siłownia/hantle: ćwiczenia ze sprzętem mają pierwszeństwo nad
    # ćwiczeniami z masą własnej. Masa własna tylko gdy brak dozwolonego ze sprzętem.
    equipment_candidates = [ex for ex in candidates if not _is_bodyweight(ex)]
    bodyweight_candidates = [ex for ex in candidates if _is_bodyweight(ex)]

    chosen_pool = equipment_candidates if equipment_candidates else bodyweight_candidates
    if used_names_global:
        unused_in_pool = [ex for ex in chosen_pool if ex["name"] not in used_names_global]
        if unused_in_pool:
            chosen_pool = unused_in_pool
    chosen_pool.sort(key=lambda ex: _selection_rank_key(get_exercise(ex.get("exercise_id", ex["name"]))))
    return chosen_pool[0]


def _bodyweight_fallback(
    group: str,
    pool: dict[str, list[dict[str, Any]]],
    equipment: set[str],
    avoid_exercises: list[str],
    training_level: str | None,
    used_names: set[str],
    used_patterns_in_session: dict[str, int],
    used_primary_muscles_in_session: dict[str, int],
    used_families_in_session: set[str],
    exclude_names: set[str] | None,
    has_equipment_preset: bool,
    slot_pattern: str | None = None,
    used_names_global: set[str] | None = None,
) -> dict[str, Any] | None:
    """Dla masy własnej: szuka ćwiczenia tej samej grupy mięśniowej z innego
    wzorca ruchu, gdy slot nie został obsadzony."""
    exclude_names = exclude_names or set()
    for ex in pool.get(group, []):
        ex_obj = get_exercise(ex.get("exercise_id", ex["name"]))
        if ex_obj is None:
            continue
        if ex["name"] in used_names or ex["name"] in exclude_names:
            continue
        # R9: nie łącz pompek klasycznych z kolanymi w jednym tygodniu
        if used_names_global:
            if ex_obj.id == "pushups_knee" and any(get_exercise(n) and get_exercise(n).id == "pushups_classic" for n in used_names_global):
                continue
            if ex_obj.id == "pushups_classic" and any(get_exercise(n) and get_exercise(n).id == "pushups_knee" for n in used_names_global):
                continue
        # R4: respektuj wzorzec ruchu slotu.
        if slot_pattern and ex_obj.movement_pattern != slot_pattern:
            continue
        if not _exercise_allowed(ex["name"], equipment, avoid_exercises):
            continue
        if ex_obj.type == "cardio" or "plyometric" in (getattr(ex_obj, "tags", None) or []):
            continue
        if not _level_allowed(ex_obj.level, training_level):
            continue
        pm = ex_obj.primary_muscles[0] if ex_obj.primary_muscles else ""
        if used_primary_muscles_in_session.get(pm, 0) >= 2:
            continue
        fam = getattr(ex_obj, "family", None)
        if fam and fam in used_families_in_session:
            continue
        return ex
    return None


_ISOLATION_CANDIDATES: dict[str, list[str]] = {
    "chest": ["cable_crossover", "pec_deck"],
    "side_delts": ["lateral_raise"],
    "biceps": ["cable_curl", "hammer_curl", "barbell_curl"],
    "triceps": ["triceps_pushdown"],
    "quads": ["leg_extension"],
    "hamstrings": ["leg_curl"],
    "calves": ["standing_calf_raise"],
    "back": ["face_pull", "rear_delt_fly"],
}


def _add_isolation_if_needed(
    days: list[dict],
    pool: dict[str, list[dict[str, Any]]],
    equipment: set[str],
    avoid_exercises: list[str],
    training_level: str | None,
    used_names_global: set[str],
    has_equipment_preset: bool,
    volume_sets: dict[str, int],
    weekly_sets: dict[str, int],
    weekly_sessions: dict[str, int],
    diagnostics: list[str],
) -> None:
    """Jeśli objętość grupy mięśniowej poniżej minimum (tylko intermediate),
    dokup ćwiczenie izolujące do sesji upper lub push (limit 7 upper, 6 push)."""
    if training_level in (None, "początkujący", "beginner"):
        return

    for muscle, (low, high) in VOLUME_TARGETS_INTERMEDIATE.items():
        actual = volume_sets.get(muscle, 0)
        if actual >= low:
            continue
        _try_add_isolation(
            muscle, days, pool, equipment, avoid_exercises,
            training_level, used_names_global, volume_sets, weekly_sets,
        )


def _try_add_isolation(
    muscle: str,
    days: list[dict],
    pool: dict[str, list[dict[str, Any]]],
    equipment: set[str],
    avoid_exercises: list[str],
    training_level: str | None,
    used_names_global: set[str],
    volume_sets: dict[str, int],
    weekly_sets: dict[str, int],
) -> None:
    """Próbuje dodać jedno ćwiczenie izolujące dla grupy do pierwszej sesji z miejscem."""
    for ex_id in _ISOLATION_CANDIDATES.get(muscle, []):
        ex = get_exercise(ex_id)
        if ex is None:
            continue
        if not _exercise_allowed(ex.name_pl, equipment, avoid_exercises):
            continue
        if not _level_allowed(ex.level, training_level):
            continue
        if ex.name_pl in used_names_global:
            continue
        target_pm = ex.primary_muscles[0] if ex.primary_muscles else ""
        for day in days:
            if day["day_type"] == "rest":
                continue
            focus = day["workout"]["focus"]
            # Klatka dodajemy tylko do push, pozostałe grupy do upper.
            if muscle == "chest" and focus != "push":
                continue
            if muscle != "chest" and focus not in ("upper_a", "upper_b"):
                continue
            exercises = day["workout"]["exercises"]
            limit = 6 if focus == "push" else 7
            if len(exercises) >= limit:
                continue
            pm_count: dict[str, int] = {}
            fam_set: set[str] = set()
            for e in exercises:
                eo = get_exercise(e.get("exercise_id", e["name"]))
                if eo is None:
                    continue
                p = eo.primary_muscles[0] if eo.primary_muscles else ""
                pm_count[p] = pm_count.get(p, 0) + 1
                f = getattr(eo, "family", None)
                if f:
                    fam_set.add(f)
            if pm_count.get(target_pm, 0) >= 2:
                continue
            fam = getattr(ex, "family", None)
            if fam and fam in fam_set:
                continue
            exercises.append({
                "exercise_id": ex.id,
                "name": ex.name_pl,
                "sets": _parse_sets(ex.sets_range, False),
                "reps": ex.reps_range,
                "how_to": "",
                "alternatives": [],
            })
            sets_val = _parse_sets(ex.sets_range, False)
            volume_sets[muscle] += sets_val
            used_names_global.add(ex.name_pl)
            group = _summary_group(ex.primary_muscles) if ex.primary_muscles else ""
            if group in weekly_sets:
                weekly_sets[group] += sets_val
            return  # Only one exercise per muscle group


def _ensure_bodyweight_minimums(
    days: list[dict],
    pool: dict[str, list[dict[str, Any]]],
    equipment: set[str],
    avoid_exercises: list[str],
    training_level: str | None,
    used_names_global: set[str],
    has_equipment_preset: bool,
    volume_sets: dict[str, int],
    weekly_sets: dict[str, int],
    diagnostics: list[str],
) -> None:
    """Dla użytkowników masy własnej gwarantuje w tygodniu co najmniej jedno
    ćwiczenie na plecy (superman, prone_ytw_raises, reverse_snow_angel),
    barki (pike_pushup, jeśli poziom pozwala) i triceps
    (pushups_narrow lub pushups_diamond_knee). Dodaje brakujące do dni z miejscem.

    Ćwiczenie nie powtarza się w sesji A i C, jeśli w bazie jest zamiennik
    (np. reverse_lunge zamiast drugiego bodyweight_squat, wall_sit,
    single_leg_glute_bridge). Pompki na kolanach tylko gdy nie ma klasycznych,
    i nie po klasycznych w tym samym tygodniu. Dodaje tygodniowo co najmniej
    jedno ćwiczenie ciągnące (australian_pullup tylko gdy użytkownik wskazał
    stół lub niski drążek, w pozostałych przypadkach superman i prone_ytw_raises).
    """
    if has_equipment_preset:
        return

    tl = (training_level or "").strip().casefold()
    beginner = tl in {"początkujący", "beginner"}

    back_candidates = ["superman", "prone_ytw_raises", "reverse_snow_angel"]
    shoulder_candidates = ["pike_pushup"] if not beginner else []
    triceps_candidates = ["pushups_narrow", "pushups_diamond_knee"]
    pull_candidates = ["australian_pullup", "superman", "prone_ytw_raises"]

    # Sprawdź co już jest w tygodniu.
    week_groups: set[str] = set()
    week_has_classic_pushups = False
    week_has_knee_pushups = False
    for day in days:
        if day["day_type"] == "rest":
            continue
        for ex in day["workout"]["exercises"]:
            ex_obj = get_exercise(ex.get("exercise_id", ex["name"]))
            if ex_obj is None:
                continue
            if ex_obj.id == "pushups_classic":
                week_has_classic_pushups = True
            if ex_obj.id == "pushups_knee":
                week_has_knee_pushups = True
            if ex_obj.primary_muscles:
                week_groups.add(_summary_group(ex_obj.primary_muscles))

    missing_back = "plecy" not in week_groups
    missing_shoulder = "barki" not in week_groups and shoulder_candidates
    missing_triceps = "triceps" not in week_groups
    missing_pull = "plecy" not in week_groups  # ciągnące = plecy

    if not (missing_back or missing_shoulder or missing_triceps or missing_pull):
        return

    # Dodaj brakujące ćwiczenia do dni z miejscem (maksymalnie 5 ćwiczeń na sesję).
    for day in days:
        if day["day_type"] == "rest":
            continue
        exercises = day["workout"]["exercises"]
        if len(exercises) >= 5:
            continue
        # Śledź grupy i rodziny w tej sesji.
        pm_count: dict[str, int] = {}
        fam_set: set[str] = set()
        names_in_session: set[str] = set()
        for e in exercises:
            eo = get_exercise(e.get("exercise_id", e["name"]))
            if eo is None:
                continue
            p = eo.primary_muscles[0] if eo.primary_muscles else ""
            pm_count[p] = pm_count.get(p, 0) + 1
            f = getattr(eo, "family", None)
            if f:
                fam_set.add(f)
            names_in_session.add(eo.id)

        candidates: list[tuple[str, str]] = []  # (ex_id, target_group)
        if missing_back:
            for cid in back_candidates:
                candidates.append((cid, "plecy"))
        if missing_shoulder:
            for cid in shoulder_candidates:
                candidates.append((cid, "barki"))
        if missing_triceps:
            for cid in triceps_candidates:
                candidates.append((cid, "triceps"))
        if missing_pull:
            for cid in pull_candidates:
                candidates.append((cid, "plecy"))

        for ex_id, target_group in candidates:
            if len(exercises) >= 5:
                break
            ex = get_exercise(ex_id)
            if ex is None:
                continue
            if not _exercise_allowed(ex.name_pl, equipment, avoid_exercises):
                continue
            if not _level_allowed(ex.level, training_level):
                continue
            if ex.name_pl in used_names_global:
                continue
            # Nie powtarzaj ćwiczenia w A i C jeśli jest zamiennik.
            if ex_id in names_in_session:
                continue
            # Pompki na kolanach tylko gdy nie ma klasycznych w tym samym tygodniu.
            if ex.id == "pushups_knee" and week_has_classic_pushups:
                continue
            # Pompki klasyczne i na kolanach nie w tym samym tygodniu.
            if ex.id == "pushups_classic" and week_has_knee_pushups:
                continue
            if pm_count.get(target_group, 0) >= 2:
                continue
            fam = getattr(ex, "family", None)
            if fam and fam in fam_set:
                continue
            exercises.append({
                "exercise_id": ex.id,
                "name": ex.name_pl,
                "sets": _parse_sets(ex.sets_range, False),
                "reps": ex.reps_range,
                "how_to": "",
                "alternatives": [],
            })
            used_names_global.add(ex.name_pl)
            names_in_session.add(ex.id)
            pm = ex.primary_muscles[0] if ex.primary_muscles else ""
            pm_count[pm] = pm_count.get(pm, 0) + 1
            if fam:
                fam_set.add(fam)
            sets_val = _parse_sets(ex.sets_range, False)
            subgroup = _volume_subgroup(ex.primary_muscles)
            if subgroup and subgroup in volume_sets:
                volume_sets[subgroup] += sets_val
            if target_group in weekly_sets:
                weekly_sets[target_group] += sets_val
            if target_group == "plecy":
                missing_back = False
                missing_pull = False
            elif target_group == "barki":
                missing_shoulder = False
            elif target_group == "triceps":
                missing_triceps = False

    # Dla dni full_body/legs użytkownika masy własnej: upewnij się, że jest squat lub hinge.
    if not has_equipment_preset:
        for day in days:
            if day["day_type"] == "rest":
                continue
            focus = day["workout"]["focus"]
            if "full_body" not in focus and "legs" not in focus:
                continue
            exercises = day["workout"]["exercises"]
            has_squat_hinge = any(
                (get_exercise(e.get("exercise_id", e["name"])) or type("X", (), {"movement_pattern": ""})()).movement_pattern
                in ("squat", "hinge")
                for e in exercises
            )
            if has_squat_hinge or len(exercises) >= 6:
                continue
            for ex_id in ("bodyweight_squat", "bodyweight_good_morning"):
                if len(exercises) >= 6:
                    break
                ex = get_exercise(ex_id)
                if ex is None:
                    continue
                if not _exercise_allowed(ex.name_pl, equipment, avoid_exercises):
                    continue
                if not _level_allowed(ex.level, training_level):
                    continue
                exercises.append({
                    "exercise_id": ex.id,
                    "name": ex.name_pl,
                    "sets": _parse_sets(ex.sets_range, False),
                    "reps": ex.reps_range,
                    "how_to": "",
                    "alternatives": [],
                })
                used_names_global.add(ex.name_pl)
                pm = ex.primary_muscles[0] if ex.primary_muscles else ""
                subgroup = _volume_subgroup(ex.primary_muscles)
                sets_val = _parse_sets(ex.sets_range, False)
                if subgroup and subgroup in volume_sets:
                    volume_sets[subgroup] += sets_val
                tg = _summary_group(ex.primary_muscles)
                if tg in weekly_sets:
                    weekly_sets[tg] += sets_val
                break


def _ensure_beginner_full_body_rules(
    days: list[dict],
    pool: dict[str, list[dict[str, Any]]],
    equipment: set[str],
    avoid_exercises: list[str],
    training_level: str | None,
    used_names_global: set[str],
    has_equipment_preset: bool,
    volume_sets: dict[str, int],
    weekly_sets: dict[str, int],
) -> None:
    """Początkujący full body: co najmniej jedno vertical_push w tygodniu,
    nie więcej niż dwa wyciskania poziome w tygodniu, rotacja wzorców zamiast
    drugiego wyciskania na płaskiej ławce. Co najmniej jedno ćwiczenie na
    triceps lub biceps (izolacja w jednej z sesji), jeśli sesja ma <5 ćwiczeń."""
    tl = (training_level or "").strip().casefold()
    if tl not in {"początkujący", "beginner"}:
        return

    week_has_vertical_push = False
    week_horizontal_push_count = 0
    for day in days:
        if day["day_type"] == "rest":
            continue
        for ex in day["workout"]["exercises"]:
            ex_obj = get_exercise(ex.get("exercise_id", ex["name"]))
            if ex_obj is None:
                continue
            if ex_obj.movement_pattern == "vertical_push":
                week_has_vertical_push = True
            if ex_obj.movement_pattern == "horizontal_push":
                week_horizontal_push_count += 1

    if not week_has_vertical_push:
        for day in days:
            if day["day_type"] == "rest":
                continue
            if "full_body" not in day["workout"]["focus"]:
                continue
            exercises = day["workout"]["exercises"]
            if len(exercises) >= 5:
                continue
            pm_count: dict[str, int] = {}
            for e in exercises:
                eo = get_exercise(e.get("exercise_id", e["name"]))
                if eo is None:
                    continue
                p = eo.primary_muscles[0] if eo.primary_muscles else ""
                pm_count[p] = pm_count.get(p, 0) + 1
            if pm_count.get("front_delts", 0) >= 1:
                continue
            for ex_id in ("seated_dumbbell_press", "overhead_press", "arnold_press", "pike_pushup"):
                ex = get_exercise(ex_id)
                if ex is None:
                    continue
                if not _exercise_allowed(ex.name_pl, equipment, avoid_exercises):
                    continue
                if not _level_allowed(ex.level, training_level):
                    continue
                if ex.name_pl in used_names_global:
                    continue
                exercises.append({
                    "exercise_id": ex.id,
                    "name": ex.name_pl,
                    "sets": _parse_sets(ex.sets_range, False),
                    "reps": ex.reps_range,
                    "how_to": "",
                    "alternatives": [],
                })
                used_names_global.add(ex.name_pl)
                sets_val = _parse_sets(ex.sets_range, False)
                subgroup = _volume_subgroup(ex.primary_muscles)
                if subgroup and subgroup in volume_sets:
                    volume_sets[subgroup] += sets_val
                tg = _summary_group(ex.primary_muscles)
                if tg in weekly_sets:
                    weekly_sets[tg] += sets_val
                break


def _calculate_estimated_minutes(exercises: list[dict[str, Any]]) -> int:
    """Szacowany czas sesji w minutach: suma serii * 2,5 + 5 min."""
    total_sets = 0
    for ex in exercises:
        sets_val = ex.get("sets", 3)
        if isinstance(sets_val, int):
            total_sets += sets_val
        elif isinstance(sets_val, str):
            try:
                total_sets += int(sets_val.split("-")[0])
            except (ValueError, AttributeError):
                total_sets += 3
    return total_sets * 2.5 + 5


def build_split_plan(
    user: Any,
    assessment: Any = None,
    progress_evidence: list[dict[str, Any]] | None = None,
) -> dict:
    """Generuje plan tygodniowy używając szablonów sesji opartych na wzorcach ruchu (v2).

    weekly_summary zawiera dla każdej grupy mięśniowej dwie liczby:
    sessions_per_week (liczba różnych dni treningowych, w których grupa występuje
    jako primary_muscles któregokolwiek ćwiczenia) oraz sets_per_week (suma serii
    roboczych tej grupy w tygodniu).
    """
    meal_catalog = _default_meal_catalog(user.diet or "")
    pool = build_exercise_pool()
    training_locations = user.get_list("training_locations_json")

    profile_days = _frequency_days(user.frequency)
    assessment_days = _assessment_value(assessment, "sessions_per_week")
    target_days = max(1, min(6, int(assessment_days or profile_days)))

    availability_raw = getattr(user, "training_availability_json", "{}")
    configured_availability: list[str] | None = None
    if isinstance(availability_raw, str) and availability_raw.strip():
        import json as _json
        try:
            parsed = _json.loads(availability_raw)
        except (TypeError, ValueError):
            parsed = {}
        if isinstance(parsed, dict) and "days" in parsed:
            configured_availability = [
                d for d in parsed["days"]
                if isinstance(d, str) and _normalize_weekday(d) is not None
            ]

    selected_days, schedule_notes = _select_training_days(target_days, configured_availability)

    training_level = _assessment_value(assessment, "training_level") or getattr(user, "fitness_level", None)
    split_key = _split_key(len(selected_days), training_level)
    template_names = SPLIT_TEMPLATES[split_key]

    raw_equipment = user.get_list("available_equipment_json")
    if not raw_equipment and getattr(user, "equipment", None):
        preset_map = {
            "gym_full": ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"],
            "gym_free": ["sztanga", "hantle", "ławka", "poręcze"],
            "dumbbells": ["hantle", "ławka"],
            "bodyweight": [],
            "court": ["piłka", "kosz"],
            "hybrid": ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia", "piłka", "kosz"],
        }
        raw_equipment = preset_map.get(str(getattr(user, "equipment", "")), [])
    equipment = _equipment_aliases(raw_equipment)
    has_equipment_preset = ("gym" in equipment) or ("dumbbell" in equipment)

    avoid_exercises = _normalized_constraints(user.get_list("avoid_exercises_json"))
    health_limitations = f"{getattr(user, 'health_limitations', '') or ''} {getattr(user, 'injuries', '') or ''}".lower()
    if ("kolan" in health_limitations or "kolana" in health_limitations) and not any("kolan" in x for x in avoid_exercises):
        avoid_exercises.append("przysiad ze sztangą")
    if ("bark" in health_limitations or "barki" in health_limitations) and not any("bark" in x for x in avoid_exercises):
        avoid_exercises.append("wyciskanie żołnierskie")

    recovery = _assessment_value(assessment, "recovery_score")
    hours = _assessment_value(assessment, "availability_hours_per_week")
    exercise_limit = _exercise_limit(training_level, recovery, hours, len(selected_days))

    base_calories = user.calories_target
    if not base_calories:
        from app.legacy_routes import calc_calories
        base_calories = calc_calories(user)

    meals_per_day = getattr(user, "meals_per_day", 3) or 3
    meal_slots = _meal_slots(max(3, min(5, int(meals_per_day))))

    volume_targets = _volume_targets(training_level)
    volume_sets: dict[str, int] = {m: 0 for m in volume_targets}
    weekly_sets: dict[str, int] = {g: 0 for g in _SUMMARY_GROUPS}
    weekly_sessions: dict[str, int] = {g: 0 for g in _SUMMARY_GROUPS}

    days: list[dict] = []
    used_names_global: set[str] = set()
    day_index = 0
    diagnostics: list[str] = list(schedule_notes)

    is_bodyweight_plan = not has_equipment_preset
    is_single_day = len(selected_days) == 1
    is_beginner = (training_level or "").strip().casefold() in {"początkujący", "beginner"}

    for day_name in selected_days:
        template_idx = day_index % len(template_names)
        template_name = template_names[template_idx]
        slots = SLOT_TEMPLATES[template_name]

        used_patterns_in_session: dict[str, int] = {}
        used_primary_muscles_in_session: dict[str, int] = {}
        used_families_in_session: set[str] = set()
        used_names_session: set[str] = set()
        exclude_names = {
            name for name in used_names_global
            if not (get_exercise(name) and getattr(get_exercise(name), "allow_repeat_across_sessions", False))
        }
        session_isolation_ids: set[str] = set()

        selected_exercises: list[dict[str, Any]] = []
        first_compound_done = False
        session_limit = 8 if template_name in ("upper_a", "upper_b") and not is_beginner else exercise_limit
        for slot in slots:
            if len(selected_exercises) >= session_limit:
                break
            # Planer objętości: jeśli to slot izolacji, a objętość podgrupy przekroczy limit górny (R11), pomiń slot
            if slot.get("kind") == "isolation":
                target_sg = None
                p_ids = slot.get("prefer_ids") or []
                if "standing_calf_raise" in p_ids:
                    target_sg = "calves"
                elif slot.get("group") == "barki":
                    target_sg = "side_delts"
                elif slot.get("group") == "triceps":
                    target_sg = "triceps"
                elif slot.get("group") == "biceps":
                    target_sg = "biceps"
                elif slot.get("group") == "klatka":
                    target_sg = "chest"
                if target_sg and target_sg in VOLUME_TARGETS_INTERMEDIATE:
                    base_high = VOLUME_TARGETS_INTERMEDIATE[target_sg][1] * (0.7 if is_beginner else 1.0)
                    max_allowed = base_high * 1.25
                    est_sets = slot.get("sets") or 3
                    if volume_sets.get(target_sg, 0) + est_sets > max_allowed:
                        continue
            ex = _fill_slot(
                slot, pool, equipment, avoid_exercises, training_level,
                used_names_session, used_patterns_in_session,
                used_primary_muscles_in_session, used_families_in_session,
                exclude_names, has_equipment_preset,
                session_isolation_ids, template_name, used_names_global,
                volume_sets,
            )
            if ex is None:
                # Fallback dla masy własnej: to samo mięsień, inny wzorzec.
                if is_bodyweight_plan:
                    group = slot["group"]
                    ex = _bodyweight_fallback(
                        group, pool, equipment, avoid_exercises, training_level,
                        used_names_session, used_patterns_in_session,
                        used_primary_muscles_in_session, used_families_in_session,
                        exclude_names, has_equipment_preset,
                        slot.get("pattern"), used_names_global,
                    )
                if ex is None:
                    continue
            ex_obj = get_exercise(ex.get("exercise_id", ex["name"]))
            if ex_obj and ex_obj.id in {"lateral_raise", "rear_delt_fly", "face_pull", "front_raise"}:
                session_isolation_ids.add(ex_obj.id)
            is_compound = ex_obj is not None and ex_obj.type != "isolation"
            is_first_compound = (not first_compound_done) and is_compound
            sets_val = slot.get("sets") or _parse_sets(ex.get("sets"), is_first_compound)
            if is_beginner:
                sets_val = min(sets_val, 3)
            if is_beginner and ex_obj and "calves" in (ex_obj.primary_muscles or []):
                sets_val = min(sets_val, 2)
            ex_with_sets = dict(ex)
            ex_with_sets["sets"] = sets_val
            selected_exercises.append(ex_with_sets)
            used_names_session.add(ex["name"])
            used_names_global.add(ex["name"])
            if is_compound:
                first_compound_done = True
                mp = ex_obj.movement_pattern
                used_patterns_in_session[mp] = used_patterns_in_session.get(mp, 0) + 1
            pm = ex_obj.primary_muscles[0] if ex_obj and ex_obj.primary_muscles else ""
            used_primary_muscles_in_session[pm] = used_primary_muscles_in_session.get(pm, 0) + 1
            fam = getattr(ex_obj, "family", None)
            if fam:
                used_families_in_session.add(fam)
            subgroup = _volume_subgroup(ex_obj.primary_muscles) if ex_obj else None
            if subgroup and subgroup in volume_sets:
                volume_sets[subgroup] += sets_val
            group = _summary_group(ex_obj.primary_muscles) if ex_obj else ""
            if group in weekly_sets:
                weekly_sets[group] += sets_val

        # Upewnij się że dzień ma co najmniej 3 ćwiczenia (fallback tej samej grupy).
        while len(selected_exercises) < 3 and len(selected_exercises) < session_limit:
            added_any = False
            for slot in slots:
                if len(selected_exercises) >= 3:
                    break
                group = slot["group"]
                ex = _bodyweight_fallback(
                    group, pool, equipment, avoid_exercises, training_level,
                    used_names_session, used_patterns_in_session,
                    used_primary_muscles_in_session, used_families_in_session,
                    exclude_names, has_equipment_preset,
                    slot.get("pattern"), used_names_global,
                )
                if ex is None:
                    continue
                ex_obj = get_exercise(ex.get("exercise_id", ex["name"]))
                is_compound = ex_obj is not None and ex_obj.type != "isolation"
                is_first_compound = (not first_compound_done) and is_compound
                sets_val = slot.get("sets") or _parse_sets(ex.get("sets"), is_first_compound)
            if is_beginner:
                sets_val = min(sets_val, 3)
            if is_beginner and ex_obj and "calves" in (ex_obj.primary_muscles or []):
                sets_val = min(sets_val, 2)
                ex_with_sets = dict(ex)
                ex_with_sets["sets"] = sets_val
                selected_exercises.append(ex_with_sets)
                used_names_session.add(ex["name"])
                used_names_global.add(ex["name"])
                if is_compound:
                    first_compound_done = True
                    mp = ex_obj.movement_pattern
                    used_patterns_in_session[mp] = used_patterns_in_session.get(mp, 0) + 1
                pm = ex_obj.primary_muscles[0] if ex_obj and ex_obj.primary_muscles else ""
                used_primary_muscles_in_session[pm] = used_primary_muscles_in_session.get(pm, 0) + 1
                fam = getattr(ex_obj, "family", None)
                if fam:
                    used_families_in_session.add(fam)
                subgroup = _volume_subgroup(ex_obj.primary_muscles) if ex_obj else None
                if subgroup and subgroup in volume_sets:
                    volume_sets[subgroup] += sets_val
                group_sg = _summary_group(ex_obj.primary_muscles) if ex_obj else ""
                if group_sg in weekly_sets:
                    weekly_sets[group_sg] += sets_val
                added_any = True
            if not added_any:
                break

        # R3: ćwiczenia złożone przed izolacjami/core w każdej sesji
        selected_exercises.sort(
            key=lambda e: 0 if (
                get_exercise(e.get("exercise_id", e["name"]))
                and get_exercise(e.get("exercise_id", e["name"])).type == "compound"
            ) else 1
        )

        if not selected_exercises:
            diagnostics.append(
                f"Dzień {day_name} pominięty: brak dozwolonych ćwiczeń dla zadeklarowanego sprzętu i poziomu."
            )
            continue

        if len(selected_exercises) < 3:
            diagnostics.append(
                f"Dzień {day_name} ma tylko {len(selected_exercises)} ćwiczenia(-ć); "
                f"zmniejszono liczbę dni treningowych."
            )
            continue

        workout_items = []
        for exercise in selected_exercises:
            ex_obj = get_exercise(exercise.get("exercise_id", exercise["name"]))
            alt_group = ex_obj.primary_muscles[0] if ex_obj and ex_obj.primary_muscles else "klatka"
            alt_group_key = _MUSCLE_TO_SUMMARY_GROUP.get(alt_group, "klatka")
            alternatives = [
                alt for alt in pool.get(alt_group_key, [])
                if alt["name"] != exercise["name"]
            ][:3]
            workout_items.append({
                **exercise,
                "how_to": exercise.get("how_to", ""),
                "alternatives": [
                    {"name": alt["name"], "sets": alt["sets"], "reps": alt["reps"]}
                    for alt in alternatives
                ],
            })

        day_type = _day_type(day_name, template_name)
        macros = calc_daily_macros(base_calories, day_type)

        meals = []
        forbidden_foods = _normalized_constraints(
            user.get_list("avoid_foods_json")
        ) + _normalized_constraints(
            (getattr(user, "allergies", "") or "").replace(",", ";").split(";")
        )
        preferred_foods = _normalized_constraints(user.get_list("preferred_foods_json"))
        for slot_name in meal_slots:
            catalog_candidates = list(meal_catalog.get(slot_name, []))
            candidates = [
                item for item in catalog_candidates
                if not any(term in str(item[0]).lower() for term in forbidden_foods if term)
            ]
            if preferred_foods:
                preferred_candidates = [
                    item for item in candidates
                    if any(term in item[0].lower() for term in preferred_foods)
                ]
                if preferred_candidates:
                    candidates = preferred_candidates
            if not candidates:
                meals.append({
                    "slot": slot_name,
                    "name": "Brak bezpiecznej propozycji w katalogu",
                    "kcal": 0,
                    "alternatives": [],
                    "constraint_blocked": True,
                })
                continue
            main = candidates[day_index % len(candidates)]
            meals.append({
                "slot": slot_name,
                "name": main[0],
                "kcal": main[1],
                "alternatives": [
                    {"name": item[0], "kcal": item[1]}
                    for item in candidates if item[0] != main[0]
                ][:3],
                "constraint_blocked": False,
            })

        days.append({
            "day": day_name,
            "locations": training_locations[day_index % len(training_locations):day_index % len(training_locations) + 1]
            if training_locations else [],
            "day_type": day_type,
            "macros": macros,
            "is_sport_session": False,
            "diagnostics": None,
            "workout": {
                "title": f"Sesja {template_name}",
                "focus": template_name,
                "is_sport_session": False,
                "sport": None,
                "specialization": None,
                "scheduled_time": None,
                "exercises": workout_items,
            },
            "meals": meals,
        })
        day_index += 1

    # Oblicz estimated_minutes dla każdej sesji.
    for day in days:
        if day["day_type"] == "rest":
            continue
        minutes = _calculate_estimated_minutes(day["workout"]["exercises"])
        day["workout"]["estimated_minutes"] = round(minutes)

    # Przelicz weekly_sets, weekly_sessions i volume_sets bezpośrednio z gotowego planu.
    volume_sets = {m: 0 for m in volume_targets}
    weekly_sets = {g: 0 for g in _SUMMARY_GROUPS}
    weekly_sessions = {g: 0 for g in _SUMMARY_GROUPS}
    for day in days:
        if day["day_type"] == "rest":
            continue
        day_groups = set()
        for ex in day["workout"]["exercises"]:
            ex_obj = get_exercise(ex.get("exercise_id", ex["name"]))
            if ex_obj is None or not ex_obj.primary_muscles:
                continue
            subgroup = _volume_subgroup(ex_obj.primary_muscles)
            if subgroup and subgroup in volume_sets:
                volume_sets[subgroup] += ex["sets"]
            g = _summary_group(ex_obj.primary_muscles)
            if g:
                if g in weekly_sets:
                    weekly_sets[g] += ex["sets"]
                day_groups.add(g)
        for g in day_groups:
            if g in weekly_sessions:
                weekly_sessions[g] += 1

    # Diagnostyka objętości.
    volume_notes: list[str] = []
    for muscle, (low, high) in volume_targets.items():
        actual = volume_sets.get(muscle, 0)
        if actual < low:
            pl_name = {
                "chest": "klatka", "back": "plecy", "side_delts": "barki boczne",
                "biceps": "biceps", "triceps": "triceps", "quads": "czworogłowe",
                "hamstrings": "dwugłowe", "calves": "łydki",
            }.get(muscle, muscle)
            # Dla początkujących nie raportuj braków biceps, triceps, łydek.
            if is_beginner and muscle in ("biceps", "triceps", "calves"):
                continue
            volume_notes.append(
                f"Grupa {pl_name}: {actual} serii, cel {low}-{high} (brakuje {low - actual})."
            )

    # Diagnostyka czasu sesji (>80 min).
    time_notes: list[str] = []
    for day in days:
        if day["day_type"] == "rest":
            continue
        mins = day["workout"].get("estimated_minutes", 0)
        if mins > 80:
            time_notes.append(f"{day['day']}: {mins} min (ponad 80 min).")

    # Dla 1 dnia i masy własnej: jeden krótki komunikat zamiast listy braków.
    if is_single_day or is_bodyweight_plan:
        if volume_notes or time_notes:
            short_parts = []
            if volume_notes:
                short_parts.append("niektóre grupy poniżej celu objętości")
            if time_notes:
                short_parts.append("niektóre sesje przekraczają 80 min")
            diagnostics.append("Uwaga: " + "; ".join(short_parts) + ".")
    else:
        if volume_notes:
            diagnostics.append("Objętość poniżej celu: " + " ".join(volume_notes))
        if time_notes:
            diagnostics.extend(time_notes)

    schedule_diagnostics = {
        "requested_training_days": target_days,
        "scheduled_training_days": len(selected_days),
        "unmet_training_days": max(0, target_days - len(selected_days)),
        "sport_reserved_days": [],
        "excluded_days": [],
        "split": split_key,
        "notes": diagnostics,
    }

    weekly_summary = {
        "sets_per_group": weekly_sets,
        "sessions_per_group": weekly_sessions,
    }

    return {
        "generated_at": None,
        "weekly_goal": user.goal,
        "days": days,
        "_planner": {
            "version": "deterministic-v2-splits",
            "target_training_days": target_days,
            "assessment_used": assessment is not None,
            "performance_signals": {},
            "progress_evidence_used": False,
            "progress_evidence_count": 0,
            "schedule_diagnostics": schedule_diagnostics,
            "training_locations_used": bool(training_locations),
            "location_equipment_count": 0,
            "reduced_days": [],
            "group_day_count": weekly_sessions,
            "weekly_summary": weekly_summary,
            "split_key": split_key,
        },
    }
