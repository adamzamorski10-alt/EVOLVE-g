"""Generator v2: szablony sesji oparte na wzorcach ruchu (splity).

Zastępuje model "jedna partia na dzień" szablonami opartymi na wzorcach ruchu,
tak aby główne grupy mięśniowe były trenowane około 2 razy w tygodniu.
Format wyjścia jest kompatybilny z build_deterministic_plan (struktura dni,
ćwiczeń, serie, powtórzenia) aby adaptacja, historia treningów i interfejs
działały bez zmian.
"""

from __future__ import annotations

import os
from typing import Any

from app.exercises.data import get_exercise, list_exercises, MUSCLE_TO_GROUP
from app.exercises.loader import build_exercise_pool, KNOWN_GROUPS
from app.legacy_routes import (
    _MUSCLE_MAP,
    _day_type,
    _default_meal_catalog,
    calc_daily_macros,
)


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


PLAN_GENERATOR = os.environ.get("PLAN_GENERATOR", "v2").strip().lower()

# ---------------------------------------------------------------------------
# Slot sesji: (wzorzec ruchu, preferowana grupa mięśniowa, typ ćwiczenia, czy izolacja)
# typ: "compound" lub "isolation"; None = dowolny
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
    ],
    "upper_b": [
        {"pattern": "horizontal_push", "group": "klatka", "kind": "compound"},
        {"pattern": "vertical_pull", "group": "plecy", "kind": "compound"},
        {"pattern": "vertical_push", "group": "barki", "kind": "compound"},
        {"pattern": "horizontal_pull", "group": "plecy", "kind": "compound"},
        {"pattern": "isolation", "group": "triceps", "kind": "isolation"},
        {"pattern": "isolation", "group": "biceps", "kind": "isolation"},
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

# Klucz splitu -> nazwy dni szablonów w kolejności tygodnia.
SPLIT_TEMPLATES: dict[str, list[str]] = {
    "full_body_1": ["full_body_a"],
    "full_body_2": ["full_body_a", "full_body_b"],
    "full_body_3": ["full_body_a", "full_body_b", "full_body_a"],
    "upper_lower_full_3": ["upper_a", "lower_a", "full_body_a"],
    "upper_lower_4": ["upper_a", "lower_a", "upper_b", "lower_b"],
    "upper_lower_push_pull_legs_5": ["upper_a", "lower_a", "push", "pull", "legs"],
    "push_pull_legs_x2_6": ["push", "pull", "legs", "push", "pull", "legs"],
}

# Dni tygodnia w kolejności (Poniedziałek .. Sobota; Niedziela = spoczynek).
_WEEKDAY_ORDER = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota"]


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


def _available_weekdays(configured_availability: list[str] | None) -> list[str]:
    """Zwraca dostępne dni robocze (Pn-Sob) w kolejności, uwzględniając availability użytkownika."""
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
) -> list[str]:
    """Wybiera dni treningowe tak, aby przerwa między sesjami tej samej partii była >= 1 dzień."""
    available = _available_weekdays(configured_availability)
    # Niedziela nie jest dniem treningowym (chyba że użytkownik jawnie ją poda, ale np. dla splitu
    # nie ma sensu - pomijamy Niedzielę jako dzień treningowy domyślnie).
    available = [d for d in available if d != "Niedziela"]
    if not available:
        available = list(_WEEKDAY_ORDER)
    return available[:num_days]


def _group_of(pattern: str, group: str) -> str:
    """Zwraca grupę mięśniową dla slotu. Dla izolacji używa grupy ze slotu."""
    return group


def _pattern_of(slot: dict[str, Any]) -> str:
    return slot["pattern"]


def _fill_slot(
    slot: dict[str, Any],
    pool: dict[str, list[dict[str, Any]]],
    equipment: set[str],
    avoid_exercises: list[str],
    training_level: str | None,
    used_names: set[str],
    used_patterns_in_session: dict[str, int],
    exclude_names: set[str] | None = None,
) -> dict[str, Any] | None:
    """Wypełnia jeden slot ćwiczeniem z puli, szukając wzorca ruchu najpierw, potem grupy."""
    exclude_names = exclude_names or set()
    pattern = slot["pattern"]
    group = slot["group"]
    kind = slot.get("kind")

    candidates: list[dict[str, Any]] = []
    for ex in pool.get(group, []):
        ex_obj = get_exercise(ex.get("exercise_id", ex["name"]))
        if ex_obj is None:
            continue
        if ex["name"] in used_names or ex["name"] in exclude_names:
            continue
        # Filtr poziomu, sprzętu, cardio/plyometria (nigdy w sesji siłowej).
        if not _exercise_allowed(ex["name"], equipment, avoid_exercises):
            continue
        if ex_obj.type == "cardio":
            continue
        if "plyometric" in (getattr(ex_obj, "tags", None) or []):
            continue
        if not _level_allowed(ex_obj.level, training_level):
            continue
        # Wzorzec ruchu: jeśli slot ma konkretny wzorzec, ćwiczenie musi go mieć
        # (chyba że to izolacja, gdzie wzorzec może być "isolation" lub inny).
        if pattern != "isolation" and ex_obj.movement_pattern != pattern:
            continue
        if kind == "isolation" and ex_obj.type != "isolation":
            continue
        if kind == "compound" and ex_obj.type != "compound":
            continue
        # Limit: max 2 ćwiczenia tego samego wzorca ruchu w sesji (poza izolacjami).
        if ex_obj.type != "isolation":
            if used_patterns_in_session.get(ex_obj.movement_pattern, 0) >= 2:
                continue
        candidates.append(ex)

    # Sortuj deterministycznie: compound przed isolation, potem po id.
    def rank(ex: dict[str, Any]) -> tuple[int, str]:
        ex_obj = get_exercise(ex.get("exercise_id", ex["name"]))
        type_order = 0 if (ex_obj and ex_obj.type == "compound") else 1
        return (type_order, ex_obj.id if ex_obj else ex["name"])

    candidates.sort(key=rank)
    for ex in candidates:
        return ex
    return None


def _exercise_equipment_en(name: str) -> set[str] | None:
    """Zwraca zestaw sprzętu wymaganego przez ćwiczenie (z app.exercises) lub None gdy nieznane."""
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


def _exercise_limit(training_level: str | None, recovery: Any = None, hours: Any = None, target_days: int = 0) -> int:
    tl = (training_level or "").strip().casefold()
    if tl in {"początkujący", "beginner"}:
        limit = 5
    else:
        limit = 6
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


def _muscle_group_label(group: str) -> str:
    """Konwertuje angielską nazwę mięśnia na polską grupę mięśniową."""
    return MUSCLE_TO_GROUP.get(group, group)


def build_split_plan(
    user: Any,
    assessment: Any = None,
    progress_evidence: list[dict[str, Any]] | None = None,
) -> dict:
    """Generuje plan tygodniowy używając szablonów sesji opartych na wzorcach ruchu (v2)."""
    meal_catalog = _default_meal_catalog(user.diet or "")
    pool = build_exercise_pool()
    training_locations = user.get_list("training_locations_json")

    profile_days = _frequency_days(user.frequency)
    assessment_days = _assessment_value(assessment, "sessions_per_week")
    target_days = max(1, min(6, int(assessment_days or profile_days)))

    # Parsuj dostępne dni z assessment (training_availability_json).
    configured_availability: list[str] | None = None
    availability_raw = getattr(user, "training_availability_json", "{}")
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

    selected_days = _select_training_days(target_days, configured_availability)
    if len(selected_days) < target_days:
        # Nie wystarczy dostępnych dni - zachowaj to co się da.
        pass

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
    equipment = set()
    for item in raw_equipment:
        if not item or not item.strip():
            continue
        key = item.strip().lower()
        equipment.add(_EQUIPMENT_PL_TO_EN.get(key, key))

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

    # Tygodniowe podsumowanie: serie robocze na grupę i liczba sesji na grupę.
    weekly_sets: dict[str, int] = {g: 0 for g in ("klatka", "plecy", "barki", "biceps", "triceps", "nogi", "brzuch")}
    weekly_sessions: dict[str, int] = {g: 0 for g in ("klatka", "plecy", "barki", "biceps", "triceps", "nogi", "brzuch")}

    days: list[dict] = []
    used_names_global: set[str] = set()  # ćwiczenia użyte w tym tygodniu (dla rotacji A/B)
    day_index = 0

    for day_name in selected_days:
        # Wybierz szablon sesji dla tego dnia (rotacja A/B/A itp.).
        template_idx = day_index % len(template_names)
        template_name = template_names[template_idx]
        slots = SLOT_TEMPLATES[template_name]

        used_patterns_in_session: dict[str, int] = {}
        used_names_session: set[str] = set()
        # exclude_names: ćwiczenia użyte w poprzedniej sesji tej samej partii (rotacja A vs B).
        exclude_names = set(used_names_global)

        selected_exercises: list[dict[str, Any]] = []
        for slot in slots:
            if len(selected_exercises) >= exercise_limit:
                break
            ex = _fill_slot(
                slot, pool, equipment, avoid_exercises, training_level,
                used_names_session, used_patterns_in_session, exclude_names,
            )
            if ex is None:
                continue
            ex_obj = get_exercise(ex.get("exercise_id", ex["name"]))
            selected_exercises.append(ex)
            used_names_session.add(ex["name"])
            used_names_global.add(ex["name"])
            if ex_obj and ex_obj.type != "isolation":
                used_patterns_in_session[ex_obj.movement_pattern] = (
                    used_patterns_in_session.get(ex_obj.movement_pattern, 0) + 1
                )
            # Zlicz serie i sesje na grupy miesniowa.
            group = _muscle_group_label(ex_obj.primary_muscles[0]) if ex_obj and ex_obj.primary_muscles else slot["group"]
            if group in weekly_sets:
                try:
                    weekly_sets[group] += int(ex.get("sets", "1").split("-")[0]) if ex.get("sets") else 1
                except (TypeError, ValueError):
                    weekly_sets[group] += 1
                weekly_sessions[group] = weekly_sessions.get(group, 0) + 1

        if not selected_exercises:
            # Sesja nie może być pusta - spróbuj dowolnego ćwiczenia z puli dla partii dnia.
            # (diagnostics zapisuje to)
            pass

        # Buduj elementy treningowe w formacie kompatybilnym z v1.
        workout_items = []
        for exercise in selected_exercises:
            ex_obj = get_exercise(exercise.get("exercise_id", exercise["name"]))
            alternatives = [
                alt for alt in pool.get(ex_obj.primary_muscles[0] if ex_obj and ex_obj.primary_muscles else "klatka", [])
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

        # Posiłki (kompatybilnie z v1).
        meals = []
        for slot_name in meal_slots:
            catalog_candidates = list(meal_catalog.get(slot_name, []))
            forbidden_foods = _normalized_constraints(
                user.get_list("avoid_foods_json")
            ) + _normalized_constraints(
                (getattr(user, "allergies", "") or "").replace(",", ";").split(";")
            )
            preferred_foods = _normalized_constraints(user.get_list("preferred_foods_json"))
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

    schedule_diagnostics = {
        "requested_training_days": target_days,
        "scheduled_training_days": len(selected_days),
        "unmet_training_days": max(0, target_days - len(selected_days)),
        "sport_reserved_days": [],
        "excluded_days": [],
        "split": split_key,
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


_EQUIPMENT_PL_TO_EN: dict[str, str] = {
    "sztanga": "barbell",
    "sztanga olimpijska": "barbell",
    "hantle": "dumbbell",
    "hantle regulowane": "dumbbell",
    "kettlebell": "kettlebell",
    "maszyny": "machine",
    "maszyna": "machine",
    "wyciąg": "cable",
    "kabel": "cable",
    "ławka": "bench",
    "ławce": "bench",
    "drążek": "pullup_bar",
    "poręcz": "dip_station",
    "poręcze": "dip_station",
    "dip_station": "dip_station",
    "pullup_bar": "pullup_bar",
    "bands": "bands",
    "taśmy": "bands",
    "bodyweight": "bodyweight",
    "masa własna": "bodyweight",
    "talerz": "weight_plate",
    "talerze": "weight_plate",
    "koło brzuszkowe": "ab_wheel",
    "koło": "ab_wheel",
    "kółko brzuszkowe": "ab_wheel",
    "stół": "table_or_low_bar",
    "niski drążek": "table_or_low_bar",
    "drążek niski": "table_or_low_bar",
    "siłownia": "gym",
    "gym": "gym",
    "full": "gym",
}


def _frequency_days(value: str | None) -> int:
    import re
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
