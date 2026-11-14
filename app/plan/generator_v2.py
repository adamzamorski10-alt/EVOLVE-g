"""Generator v2: szablony sesji oparte na wzorcach ruchu (splity).

Zastępuje model "jedna partia na dzień" szablonami opartymi na wzorcach ruchu,
tak aby główne grupy mięśniowe były trenowane około 2 razy w tygodniu.
Format wyjścia jest kompatybilny z build_deterministic_plan (struktura dni,
ćwiczeń, serie, powtórzenia) aby adaptacja, historia treningów i interfejs
działały bez cambios.
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
    ExerciseDescription,
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

# Mapowanie primary_muscle -> podgrupa objętościowa (dla diagnostyki objętości).
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
    "glutes": "quads",
    "calves": "calves",
    "abs": "brzuch",
    "obliques": "brzuch",
}

# Mapowanie primary_muscle -> grupa podsumowania weekly_summary.
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

# Ćwiczenia z kompletnym opisem w data/descriptions (dodatkowy bonus przy remisie).
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


def _selection_rank_key(ex: Any, training_level: str | None, equipment: set[str],
                        has_equipment_preset: bool) -> tuple[int, int, int, str]:
    """Klucz sortowania slotu: poziom/sprzęt filtrowane wcześniej, potem selection_rank,
    bonus za kompletny opis, potem stabilnie po id."""
    ex_id = ex.id
    rank = 999
    pattern_ranks = SELECTION_RANK.get(ex.movement_pattern, {})
    if ex_id in pattern_ranks:
        rank = pattern_ranks[ex_id]
    # Bonus za kompletny opis (mniejsza ranga = wyżej).
    desc_bonus = 0 if ex_id in _described_exercise_ids() else 1
    # Przy sprzęcie siłownia/hantle: ćwiczenie masy własnej znieżscorej,
    # jeśli w tym wzorcu jest dozwolone ćwiczenie ze sprzętem.
    bodyweight_penalty = 0
    if has_equipment_preset and set(ex.equipment) <= {"bodyweight"}:
        bodyweight_penalty = 50
    return (rank, desc_bonus, bodyweight_penalty, ex_id)


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
        {"pattern": "vertical_push", "group": "barki", "kind": "compound"},
        {"pattern": "core", "group": "brzuch", "kind": "isolation"},
    ],
    "full_body_b": [
        {"pattern": "hinge", "group": "nogi", "kind": "compound"},
        {"pattern": "horizontal_push", "group": "klatka", "kind": "compound"},
        {"pattern": "horizontal_pull", "group": "plecy", "kind": "compound"},
        {"pattern": "vertical_pull", "group": "plecy", "kind": "compound"},
        {"pattern": "core", "group": "brzuch", "kind": "isolation"},
    ],
    "upper_a": [
        {"pattern": "horizontal_push", "group": "klatka", "kind": "compound"},
        {"pattern": "horizontal_pull", "group": "plecy", "kind": "compound"},
        {"pattern": "vertical_push", "group": "barki", "kind": "compound"},
        {"pattern": "vertical_pull", "group": "plecy", "kind": "compound"},
        {"pattern": "isolation", "group": "triceps", "kind": "isolation"},
        {"pattern": "isolation", "group": "biceps", "kind": "isolation"},
        {"pattern": "isolation", "group": "barki", "kind": "isolation"},
        {"pattern": "isolation", "group": "barki", "kind": "isolation"},
    ],
    "upper_b": [
        {"pattern": "horizontal_push", "group": "klatka", "kind": "compound"},
        {"pattern": "vertical_pull", "group": "plecy", "kind": "compound"},
        {"pattern": "vertical_push", "group": "barki", "kind": "compound"},
        {"pattern": "horizontal_pull", "group": "plecy", "kind": "compound"},
        {"pattern": "isolation", "group": "triceps", "kind": "isolation"},
        {"pattern": "isolation", "group": "biceps", "kind": "isolation"},
        {"pattern": "isolation", "group": "barki", "kind": "isolation"},
        {"pattern": "isolation", "group": "barki", "kind": "isolation"},
    ],
    "lower_a": [
        {"pattern": "squat", "group": "nogi", "kind": "compound"},
        {"pattern": "hinge", "group": "nogi", "kind": "compound"},
        {"pattern": "lunge", "group": "nogi", "kind": "compound"},
        {"pattern": "isolation", "group": "nogi", "kind": "isolation"},
        {"pattern": "isolation", "group": "nogi", "kind": "isolation"},
        {"pattern": "core", "group": "brzuch", "kind": "isolation"},
    ],
    "lower_b": [
        {"pattern": "hinge", "group": "nogi", "kind": "compound"},
        {"pattern": "squat", "group": "nogi", "kind": "compound"},
        {"pattern": "lunge", "group": "nogi", "kind": "compound"},
        {"pattern": "isolation", "group": "nogi", "kind": "isolation"},
        {"pattern": "isolation", "group": "brzuch", "kind": "isolation"},
    ],
    "push": [
        {"pattern": "horizontal_push", "group": "klatka", "kind": "compound"},
        {"pattern": "vertical_push", "group": "barki", "kind": "compound"},
        {"pattern": "isolation", "group": "triceps", "kind": "isolation"},
        {"pattern": "isolation", "group": "triceps", "kind": "isolation"},
    ],
    "pull": [
        {"pattern": "horizontal_pull", "group": "plecy", "kind": "compound"},
        {"pattern": "vertical_pull", "group": "plecy", "kind": "compound"},
        {"pattern": "isolation", "group": "biceps", "kind": "isolation"},
        {"pattern": "isolation", "group": "biceps", "kind": "isolation"},
    ],
    "legs": [
        {"pattern": "squat", "group": "nogi", "kind": "compound"},
        {"pattern": "hinge", "group": "nogi", "kind": "compound"},
        {"pattern": "lunge", "group": "nogi", "kind": "compound"},
        {"pattern": "isolation", "group": "nogi", "kind": "isolation"},
        {"pattern": "core", "group": "brzuch", "kind": "isolation"},
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


def _fill_slot(
    slot: dict[str, Any],
    pool: dict[str, list[dict[str, Any]]],
    equipment: set[str],
    avoid_exercises: list[str],
    training_level: str | None,
    used_names: set[str],
    used_patterns_in_session: dict[str, int],
    exclude_names: set[str] | None,
    has_equipment_preset: bool,
) -> dict[str, Any] | None:
    """Wypełnia jeden slot ćwiczeniem z puli.

    Filtruje po poziomie i sprzęcie, potem sortuje po selection_rank (jawny priorytet),
    bonusie za kompletny opis i na końcu po id. Ćwiczenie masy własnej jest wybierane
    przy sprzęcie siłownia/hantle tylko gdy nie ma dozwolonego ćwiczenia ze sprzętem
    w tym wzorcu.
    """
    exclude_names = exclude_names or set()
    pattern = slot["pattern"]
    group = slot["group"]
    kind = slot.get("kind")

    # Najpierw zbierz wszystkich kandydatów przechodzących filtry poziomu i sprzętu.
    candidates: list[dict[str, Any]] = []
    for ex in pool.get(group, []):
        ex_obj = get_exercise(ex.get("exercise_id", ex["name"]))
        if ex_obj is None:
            continue
        if ex["name"] in used_names or ex["name"] in exclude_names:
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
        if ex_obj.type != "isolation":
            if used_patterns_in_session.get(ex_obj.movement_pattern, 0) >= 2:
                continue
        candidates.append(ex)

    if not candidates:
        return None

    # Jeśli mamy sprzęt siłownia/hantle, oddziel ćwiczenia ze sprzętem od masy własnej.
    equipment_candidates = [
        ex for ex in candidates
        if not (set(getattr(get_exercise(ex.get("exercise_id", ex["name"])), "equipment", [])) <= {"bodyweight"})
    ]
    bodyweight_candidates = [
        ex for ex in candidates
        if set(getattr(get_exercise(ex.get("exercise_id", ex["name"])), "equipment", [])) <= {"bodyweight"}
    ]

    chosen_pool = equipment_candidates if equipment_candidates else bodyweight_candidates

    def rank_key(ex: dict[str, Any]) -> tuple[int, int, int, str]:
        ex_obj = get_exercise(ex.get("exercise_id", ex["name"]))
        return _selection_rank_key(ex_obj, training_level, equipment, has_equipment_preset)

    chosen_pool.sort(key=rank_key)
    return chosen_pool[0]


def _exercise_limit(training_level: str | None, recovery: Any = None, hours: Any = None,
                    target_days: int = 0) -> int:
    tl = (training_level or "").strip().casefold()
    limit = 5 if tl in {"początkujący", "beginner"} else 6
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


def build_split_plan(
    user: Any,
    assessment: Any = None,
    progress_evidence: list[dict[str, Any]] | None = None,
) -> dict:
    """Generuje plan tygodniowy używając szablonów sesji opartych na wzorcach ruchu (v2).

    weekly_summary zawiera dla każdej grupy mięśniowej dwie liczby:
    sessions_per_week (liczba dni z co najmniej jednym ćwiczeniem z tej grupy jako
    primary_muscles) oraz sets_per_week (suma serii roboczych tej grupy w tygodniu).
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

    training_level = _assessment_value(assessment, "training_level")
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

    for day_name in selected_days:
        template_idx = day_index % len(template_names)
        template_name = template_names[template_idx]
        slots = SLOT_TEMPLATES[template_name]

        used_patterns_in_session: dict[str, int] = {}
        used_names_session: set[str] = set()
        exclude_names = set(used_names_global)

        selected_exercises: list[dict[str, Any]] = []
        first_compound_done = False
        for slot in slots:
            if len(selected_exercises) >= exercise_limit:
                break
            ex = _fill_slot(
                slot, pool, equipment, avoid_exercises, training_level,
                used_names_session, used_patterns_in_session, exclude_names,
                has_equipment_preset,
            )
            if ex is None:
                continue
            ex_obj = get_exercise(ex.get("exercise_id", ex["name"]))
            selected_exercises.append(ex)
            used_names_session.add(ex["name"])
            used_names_global.add(ex["name"])
            is_compound = ex_obj is not None and ex_obj.type != "isolation"
            is_first_compound = (not first_compound_done) and is_compound
            if is_compound:
                first_compound_done = True
                used_patterns_in_session[ex_obj.movement_pattern] = (
                    used_patterns_in_session.get(ex_obj.movement_pattern, 0) + 1
                )
            sets_val = _parse_sets(ex.get("sets"), is_first_compound)
            # Zlicz objętość per podgrupa mięśniowa.
            subgroup = _volume_subgroup(ex_obj.primary_muscles) if ex_obj else None
            if subgroup and subgroup in volume_sets:
                volume_sets[subgroup] += sets_val
            # Zlicz objętość per grupa podsumowania.
            group = _summary_group(ex_obj.primary_muscles) if ex_obj else ""
            if group in weekly_sets:
                weekly_sets[group] += sets_val
                weekly_sessions[group] = weekly_sessions.get(group, 0) + 1

        # Jeśli dzień ma mniej niż 3 ćwiczenia, dopełnij fallbackami tej samej grupy mięśniowej
        # z innego wzorca ruchu (np. dla pleców: bird_dog, superman; dla pchania: pushups_narrow).
        while len(selected_exercises) < 3 and len(selected_exercises) < exercise_limit:
            added_any = False
            for slot in slots:
                if len(selected_exercises) >= 3:
                    break
                group = slot["group"]
                # Szukaj ćwiczenia tej grupy (po primary_muscles -> grupa podsumowania) z innego wzorca.
                target_group = None
                for ex in pool.get(group, []):
                    ex_obj = get_exercise(ex.get("exercise_id", ex["name"]))
                    if ex_obj is None:
                        continue
                    g = _summary_group(ex_obj.primary_muscles)
                    if g == group and ex["name"] not in used_names_session:
                        # Sprawdź filtry.
                        if not _exercise_allowed(ex["name"], equipment, avoid_exercises):
                            continue
                        if ex_obj.type == "cardio" or "plyometric" in (getattr(ex_obj, "tags", None) or []):
                            continue
                        if not _level_allowed(ex_obj.level, training_level):
                            continue
                        selected_exercises.append(ex)
                        used_names_session.add(ex["name"])
                        used_names_global.add(ex["name"])
                        added_any = True
                        break
                if added_any:
                    break
            if not added_any:
                break

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
            diagnostics.append(
                f"Dzień {day_name} ma tylko {len(selected_exercises)} ćwiczenia(-ć); "
                f"zmniejszono liczbę dni treningowych."
            )
            continue

        workout_items = []
        for exercise in selected_exercises:
            ex_obj = get_exercise(exercise.get("exercise_id", exercise["name"]))
            alt_group = ex_obj.primary_muscles[0] if ex_obj and ex_obj.primary_muscles else "klatka"
            alternatives = [
                alt for alt in pool.get(_MUSCLE_TO_SUMMARY_GROUP.get(alt_group, "klatka"), [])
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

    # Diagnostyka objętości: sprawdź czy cele zostały spełnione.
    volume_notes: list[str] = []
    for muscle, (low, high) in volume_targets.items():
        actual = volume_sets.get(muscle, 0)
        if actual < low:
            pl_name = {
                "chest": "klatka", "back": "plecy", "side_delts": "barki boczne",
                "biceps": "biceps", "triceps": "triceps", "quads": "czworogłowe",
                "hamstrings": "dwugłowe", "calves": "łydki",
            }.get(muscle, muscle)
            volume_notes.append(
                f"Grupa {pl_name}: {actual} serii, cel {low}-{high} (brakuje {low - actual})."
            )
    if volume_notes:
        diagnostics.append("Objętość poniżej celu: " + " ".join(volume_notes))

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
