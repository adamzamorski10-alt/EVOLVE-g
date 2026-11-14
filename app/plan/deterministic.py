"""Deterministic EVOLVE planning core.

This module is the implementation boundary for the new core-loop planner.
It may reuse legacy catalogs as reference data, but planning decisions here
are deterministic and derive only from explicit profile/assessment inputs.
"""

from __future__ import annotations

from typing import Any
import json

from app.exercise_descriptions import get_how_to
from app.exercises.data import get_exercise
from app.exercises.loader import KNOWN_GROUPS, muscle_group_for_exercise
from app.plan.performance_signals import build_performance_signals, prioritize_sport_drills
from app.legacy_routes import (
    SPORT_DRILLS_DB,
    _MUSCLE_MAP,
    _day_type,
    _default_meal_catalog,
    _exercise_pool,
    calc_daily_macros,
)


_DAY_SCHEDULE = [
    ("Poniedziałek", False),
    ("Wtorek", False),
    ("Środa", False),
    ("Czwartek", False),
    ("Piątek", False),
    ("Sobota", False),
    ("Niedziela", True),
]


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


def _frequency_days(value: str | None) -> int:
    import re

    numbers = [int(x) for x in re.findall(r"\d+", str(value or ""))]
    if not numbers:
        return 3
    # For a range such as "3-4 razy" use the upper bound so the generated
    # plan does not silently under-deliver the requested weekly frequency.
    return max(1, min(6, max(numbers)))


# Map polskiego nazwy sprzętu użytkownika na kanoniczne angielskie klucze z app.exercises.
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
    # Specjalne markery oznaczające pełny dostęp:
    "siłownia": "gym",
    "gym": "gym",
    "full": "gym",
}


def _equipment_aliases(items: list[str]) -> set[str]:
    """Zwraca kanoniczne nazwy sprzętu (angielskie klucze z app.exercises)."""
    out: set[str] = set()
    for item in items:
        if not item or not item.strip():
            continue
        key = item.strip().lower()
        out.add(_EQUIPMENT_PL_TO_EN.get(key, key))
    return out


def _exercise_equipment_en(name: str) -> set[str] | None:
    """Zwraca zestaw sprzętu wymaganego przez ćwiczenie (z app.exercises) lub None gdy nieznane."""
    from app.exercises.data import get_exercise, list_exercises

    ex = get_exercise(name)  # po id (slug)
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

    # Pełna siłownia / gym - wszystko dozwolone.
    if "gym" in equipment:
        return True

    # Pusta lista sprzętu = preset "masa własna" - tylko ćwiczenia bez sprzętu.
    if not equipment:
        req = _exercise_equipment_en(name)
        if req is not None:
            return req <= {"bodyweight"}
        # Fallback dla nieznanego ćwiczenia: odrzucaj (bezpieczniej niż domyślne zezwolenie).
        return False

    req = _exercise_equipment_en(name)
    if req is not None:
        # Ćwiczenia własnym ciałem zawsze dozwolone (nie wymagają sprzętu).
        if req <= {"bodyweight"}:
            return True
        return req.issubset(equipment)

    # Fallback: starsze wnioskowanie z nazwy dla ćwiczeń spoza nowej bazy.
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


_PREFERRED_PATTERNS: dict[str, set[str]] = {
    "klatka": {"horizontal_push"},
    "plecy": {"horizontal_pull", "vertical_pull"},
    "nogi": {"squat", "hinge", "lunge"},
    "barki": {"vertical_push"},
    "biceps": set(),
    "triceps": set(),
    "brzuch": {"core"},
}

_SUPPORTING_GROUPS: dict[str, list[str]] = {
    "klatka": ["triceps", "barki"],
    "plecy": ["biceps", "barki"],
    "nogi": ["brzuch"],
}


def _level_allowed(level: str, training_level: str | None) -> bool:
    """Czy ćwiczenie o danym poziomie jest dozwolone dla poziomu treningowego użytkownika."""
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


def _assessment_value(assessment: Any, field: str, default: Any = None) -> Any:
    return getattr(assessment, field, default) if assessment is not None else default


def _normalized_constraints(items: list[str]) -> list[str]:
    return [
        item.strip().lower()
        for item in items
        if isinstance(item, str) and item.strip()
    ]


def _meal_allowed(name: str, forbidden_terms: list[str]) -> bool:
    lowered = name.lower()
    return not any(term in lowered for term in forbidden_terms)


def _meal_slots(meals_per_day: int) -> list[str]:
    slots = ["Śniadanie", "Obiad", "Kolacja"]
    if meals_per_day >= 4:
        slots.insert(1, "Przekąska 1")
    if meals_per_day >= 5:
        slots.insert(3, "Przekąska 2")
    return slots


def build_deterministic_plan(
    user: Any,
    assessment: Any = None,
    progress_evidence: list[dict[str, Any]] | None = None,
) -> dict:
    """Generate a reproducible weekly plan from explicit inputs and evidence.

    Progress evidence is descriptive only. It may improve continuity by
    prioritizing exercises with observed history, but it never makes an
    adaptation decision or bypasses execution safety.
    """
    meal_catalog = _default_meal_catalog(user.diet or "")
    exercise_pool = _exercise_pool()
    training_locations = user.get_list("training_locations_json")
    location_equipment = {
        str(item)
        for location in training_locations
        if isinstance(location, dict)
        for item in (location.get("equipment") or [])
    }

    profile_days = _frequency_days(user.frequency)
    assessment_days = _assessment_value(assessment, "sessions_per_week")
    target_days = max(1, min(6, int(assessment_days or profile_days)))

    sport_focus = (user.sport_focus or "").lower().strip()
    if not sport_focus and getattr(user, "basketball_position", None):
        sport_focus = "koszykówka"
    sport_specialization = (user.sport_specialization or "").lower().strip()
    if not sport_specialization and getattr(user, "basketball_position", None):
        pos = str(getattr(user, "basketball_position", "") or "").upper()
        if pos in ("PG", "SG"):
            sport_specialization = "rzuty"
        elif pos in ("SF", "PF"):
            sport_specialization = "motoryka"
        elif pos == "C":
            sport_specialization = "rzuty"
    configured_sport_days = {
        day
        for value in user.get_list("sport_training_days_json")
        if (day := _normalize_weekday(value)) is not None
    }

    sport_drills: list[dict] = []
    performance_signals = build_performance_signals(
        assessment,
        sport_focus=sport_focus,
    )
    if sport_focus in SPORT_DRILLS_DB:
        spec_map = SPORT_DRILLS_DB[sport_focus]
        sport_drills = list(spec_map.get(sport_specialization) or next(iter(spec_map.values()), []))
        secondary_drills = [
            drill
            for drills in spec_map.values()
            for drill in drills
            if drill not in sport_drills
        ]
        sport_drills = prioritize_sport_drills(
            sport_drills,
            performance_signals,
            secondary_drills=secondary_drills,
        )

    def _read_constraint_dict(field: str) -> tuple[dict[str, Any], bool]:
        """Read persisted scheduling JSON without letting corrupt data widen availability."""
        raw = getattr(user, field, "{}")
        if isinstance(raw, dict):
            return raw, True
        if not isinstance(raw, str) or not raw.strip():
            return {}, True
        try:
            parsed = json.loads(raw)
        except (TypeError, ValueError, json.JSONDecodeError):
            return {}, False
        return (parsed, True) if isinstance(parsed, dict) else ({}, False)

    availability, availability_valid = _read_constraint_dict("training_availability_json")
    configured_availability = availability.get("days") if availability_valid else None
    if availability_valid and "days" in availability:
        availability_valid = (
            isinstance(configured_availability, list)
            and bool(configured_availability)
            and all(
                isinstance(day, str) and _normalize_weekday(day) is not None
                for day in configured_availability
            )
        )
    if availability_valid and "windows" in availability:
        availability_valid = isinstance(availability.get("windows"), dict)
    if availability_valid and "session_duration_minutes" in availability:
        duration = availability.get("session_duration_minutes")
        availability_valid = (
            isinstance(duration, int)
            and not isinstance(duration, bool)
            and 15 <= duration <= 240
        )
    if not availability_valid:
        configured_availability = ["<invalid-availability-constraint>"]
    available_days = {
        day
        for value in (configured_availability or [])
        if (day := _normalize_weekday(value)) is not None
    }
    raw_windows = availability.get("windows", {}) if isinstance(availability, dict) else {}
    windows = raw_windows if isinstance(raw_windows, dict) else {}
    sport_schedule, sport_schedule_valid = _read_constraint_dict("sport_training_schedule_json")
    if not sport_schedule_valid:
        # Sport time windows are optional; malformed stored data must not crash
        # plan generation or be surfaced as a trusted scheduled time.
        sport_schedule = {}
    raw_sport_windows = sport_schedule.get("windows", {})
    sport_windows = raw_sport_windows if isinstance(raw_sport_windows, dict) else {}
    try:
        required_minutes = max(15, min(240, int(availability.get("session_duration_minutes", 60))))
    except (TypeError, ValueError):
        required_minutes = 60

    def window_status(day: str) -> str:
        """Return unrestricted, sufficient, insufficient, or invalid for a weekday."""
        if day not in windows:
            return "unrestricted"
        window = windows[day]
        if not isinstance(window, dict):
            return "invalid"
        start, end = window.get("start"), window.get("end")
        if not isinstance(start, str) or not isinstance(end, str):
            return "invalid"
        import re
        if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", start):
            return "invalid"
        if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", end):
            return "invalid"
        start_hour, start_minute = (int(part) for part in start.split(":"))
        end_hour, end_minute = (int(part) for part in end.split(":"))
        start_total = start_hour * 60 + start_minute
        end_total = end_hour * 60 + end_minute
        if start_total >= end_total:
            return "invalid"
        if end_total - start_total < required_minutes:
            return "insufficient"
        return "sufficient"

    def has_sufficient_window(day: str) -> bool:
        return window_status(day) in {"unrestricted", "sufficient"}

    candidate_days = [
        name for name, is_rest in _DAY_SCHEDULE
        if availability_valid and not is_rest
        and (not configured_availability or name in available_days)
        and (
            (name in configured_sport_days and bool(sport_drills))
            or has_sufficient_window(name)
        )
    ]
    # Availability is a hard constraint: never fill the weekly target on an
    # unavailable day. A smaller feasible plan is safer than an impossible one.
    feasible_target_days = min(target_days, len(candidate_days))
    selected_days: list[str] = [
        day for day in candidate_days if day in configured_sport_days
    ]
    for day in candidate_days:
        if day not in selected_days and len(selected_days) < feasible_target_days:
            selected_days.append(day)
    selected_days = selected_days[:feasible_target_days]

    # Keep scheduling outcomes explicit so a reduced plan is not mistaken for
    # a fully satisfied weekly target. Diagnostics are deterministic and contain
    # only the authenticated user's own constraints.
    selected_day_set = set(selected_days)
    excluded_schedule_days = []
    for day_name, is_rest in _DAY_SCHEDULE:
        if is_rest or day_name in selected_day_set:
            continue
        if not availability_valid:
            reason_code = "invalid_constraint"
        elif configured_availability and day_name not in available_days:
            reason_code = "unavailable_day"
        elif day_name not in configured_sport_days or not sport_drills:
            status = window_status(day_name)
            if status == "invalid":
                reason_code = "invalid_constraint"
            elif status == "insufficient":
                reason_code = "insufficient_window"
            else:
                reason_code = "weekly_target_reached"
        else:
            reason_code = "weekly_target_reached"
        excluded_schedule_days.append({
            "day": day_name,
            "reason_code": reason_code,
        })
    sport_reserved_days = [
        day for day in selected_days
        if day in configured_sport_days and bool(sport_drills)
    ]
    schedule_diagnostics = {
        "requested_training_days": target_days,
        "scheduled_training_days": len(selected_days),
        "unmet_training_days": max(0, target_days - len(selected_days)),
        "sport_reserved_days": sport_reserved_days,
        "excluded_days": excluded_schedule_days,
    }

    focus = [x.lower() for x in user.get_list("training_focus_json") if isinstance(x, str) and x.strip()]
    improve = [x.lower() for x in user.get_list("improvement_areas_json") if isinstance(x, str) and x.strip()]
    preferred = focus + [x for x in improve if x not in focus] or ["klatka", "plecy", "nogi", "brzuch", "barki"]

    regular_days = [d for d in selected_days if d not in configured_sport_days or not sport_drills]
    focus_sequence: list[str] = []
    for index in range(len(regular_days)):
        focus_sequence.append(preferred[index % len(preferred)])
    focus_iter = iter(focus_sequence)

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

    avoid_exercises = _normalized_constraints(user.get_list("avoid_exercises_json"))
    health_limitations = f"{getattr(user, 'health_limitations', '') or ''} {getattr(user, 'injuries', '') or ''}".lower()
    if ("kolan" in health_limitations or "kolana" in health_limitations) and not any("kolan" in x for x in avoid_exercises):
        avoid_exercises.append("przysiad ze sztangą")
    if ("bark" in health_limitations or "barki" in health_limitations) and not any("bark" in x for x in avoid_exercises):
        avoid_exercises.append("wyciskanie żołnierskie")
    preferred_foods = _normalized_constraints(user.get_list("preferred_foods_json"))
    avoid_foods = _normalized_constraints(user.get_list("avoid_foods_json"))
    allergies_raw = getattr(user, "allergies", "") or ""
    allergies = _normalized_constraints(allergies_raw.replace(",", ";").split(";"))
    forbidden_foods = avoid_foods + [item for item in allergies if item not in avoid_foods]
    meals_per_day = getattr(user, "meals_per_day", 3) or 3
    meal_slots = _meal_slots(max(3, min(5, int(meals_per_day))))

    base_calories = user.calories_target
    if not base_calories:
        from app.legacy_routes import calc_calories

        base_calories = calc_calories(user)

    normalized_progress = [
        item for item in (progress_evidence or [])
        if isinstance(item, dict)
        and item.get("status") == "sufficient"
        and item.get("sufficient_data") is True
    ]

    def _progress_priority(exercise: dict[str, Any]) -> int:
        def _match_key(value: Any) -> str:
            normalized = "".join(
                char if char.isalnum() else "-"
                for char in str(value or "").strip().lower()
            )
            return "-".join(part for part in normalized.split("-") if part)

        exercise_keys = {
            _match_key(exercise.get("name")),
            _match_key(exercise.get("exercise_key")),
        }
        for evidence in normalized_progress:
            evidence_key = _match_key(evidence.get("exercise_key"))
            if evidence_key and evidence_key in exercise_keys:
                return 0 if evidence.get("material_change") else 1
        return 2

    days: list[dict] = []
    group_day_count: dict[str, int] = {g: 0 for g in KNOWN_GROUPS}
    prev_exercise_names: set[str] = set()
    reduced_days: list[str] = []
    for day_index, (day_name, is_sunday_rest) in enumerate(_DAY_SCHEDULE):
        is_selected = day_name in selected_days
        is_sport_day = is_selected and bool(sport_drills) and day_name in configured_sport_days
        day_diagnostics = None

        if is_sunday_rest or not is_selected:
            day_type = "rest"
            focus_key = "odpoczynek"
            workout_items = []
            workout_title = "Odpoczynek / Aktywna regeneracja"
            is_sport_session = False
        elif is_sport_day:
            day_type = "heavy"
            focus_key = sport_focus
            workout_items = []
            for drill in sport_drills:
                workout_items.append({
                    "name": drill["name"],
                    "total_attempts": drill["total_attempts"],
                    "description": drill["description"],
                    "progression_tip": drill["progression_tip"],
                    "sets": "-",
                    "reps": f'{drill["total_attempts"]} prób',
                    "notes": drill["description"],
                    "how_to": get_how_to(drill["name"], is_drill=True) or drill.get("progression_tip", ""),
                    "alternatives": [],
                })
            workout_title = f"Sesja Sportowa - {sport_focus.title()} ({sport_specialization.title() or 'Specjalistyczna'})"
            is_sport_session = True
        else:
            raw_focus = next(focus_iter, preferred[0])
            focus_key = _MUSCLE_MAP.get(raw_focus, raw_focus)
            if focus_key not in exercise_pool:
                focus_key = "klatka"
            day_type = _day_type(day_name, focus_key)

            has_equipment_preset = ("gym" in equipment) or ("dumbbell" in equipment)
            training_level = _assessment_value(assessment, "training_level")

            def _filter_available(ex: dict[str, Any], ex_obj: Any, group: str, is_cardio_focus: bool) -> dict[str, Any] | None:
                """Zwraca ćwiczenie jeśli przechodzi filtry sprzętu, poziomu i typu, lub None."""
                if not _exercise_allowed(ex["name"], equipment, avoid_exercises):
                    return None
                if ex_obj is None:
                    # Ćwiczenie spoza nowej bazy - nie filtruj poziomu ani typu.
                    return ex
                if ex_obj.type == "cardio" and not is_cardio_focus:
                    return None
                if not _level_allowed(ex_obj.level, training_level):
                    return None
                return ex

            def _rank_key(ex: dict[str, Any], ex_obj: Any, group: str) -> tuple[int, int, int, str]:
                """Klucz sortowania: sprzęt przed bodyweight, compound przed isolation,
                wzorce partii na początku, potem stabilnie po id."""
                if has_equipment_preset and ex_obj is not None:
                    equip_score = 1 if set(ex_obj.equipment) <= {"bodyweight"} else 0
                else:
                    equip_score = 0
                if ex_obj is None:
                    type_order = 2
                    pattern_pref = 1
                    ex_id = str(ex.get("name", ""))
                else:
                    t = ex_obj.type
                    if t == "compound":
                        type_order = 0
                    elif t == "isolation":
                        type_order = 1
                    else:
                        type_order = 2
                    mp = ex_obj.movement_pattern
                    pattern_pref = 0 if mp in _PREFERRED_PATTERNS.get(group, set()) else 1
                    ex_id = ex_obj.id
                return (equip_score, type_order, pattern_pref, ex_id)

            def _available_for(group: str) -> list[dict[str, Any]]:
                is_cardio_focus = (group == "cardio")
                result: list[dict[str, Any]] = []
                for ex in exercise_pool.get(group, []):
                    ex_obj = get_exercise(ex.get("exercise_id", ex["name"]))
                    kept = _filter_available(ex, ex_obj, group, is_cardio_focus)
                    if kept is not None:
                        result.append(kept)
                return result

            available = _available_for(focus_key)

            # Rotacja: nie generuj dnia, który dubluje poprzedni dzień co do ćwiczeń.
            rotated = [ex for ex in available if ex["name"] not in prev_exercise_names]
            if rotated:
                available = rotated
            day_diagnostics = None

            if not available:
                # Zamień partię na dozwoloną z najmniejszą liczbą dni w tym tygodniu.
                best_group: str | None = None
                best_count = None
                for candidate_group in KNOWN_GROUPS:
                    if candidate_group == focus_key:
                        continue
                    cand_available = _available_for(candidate_group)
                    if not cand_available:
                        continue
                    cand_rotated = [
                        ex for ex in cand_available
                        if ex["name"] not in prev_exercise_names
                    ]
                    if not cand_rotated:
                        continue
                    count = group_day_count.get(candidate_group, 0)
                    if best_count is None or count < best_count:
                        best_group = candidate_group
                        best_count = count
                if best_group is not None:
                    available = _available_for(best_group)
                    rotated = [
                        ex for ex in available
                        if ex["name"] not in prev_exercise_names
                    ]
                    if rotated:
                        available = rotated
                    day_diagnostics = (
                        f"Partia '{focus_key}' nie ma ćwiczeń dostępnych dla zadeklarowanego sprzętu. "
                        f"Zastąpiono partią '{best_group}' (ćwiczenia: "
                        f"{', '.join(e['name'] for e in available[:3])})."
                    )
                    focus_key = best_group
                else:
                    # Żadna partia nie ma dostępnych ćwiczeń - zmniejsz liczbę dni.
                    reduced_days.append(day_name)
                    day_diagnostics = (
                        f"Dzień {day_name} pominięty: brak ćwiczeń dostępnych dla zadeklarowanego sprzętu."
                    )
                    # Nie dodaj dnia do wyjścia - kontynuuj do następnego.
                    continue

            available = sorted(
                available,
                key=lambda ex: _rank_key(ex, get_exercise(ex.get("exercise_id", ex["name"])), focus_key),
            )

            # Limit: maksymalnie 2 ćwiczenia o tym samym movement_pattern w sesji,
            # izolacje (type == "isolation") nie liczą się do tego limitu.
            limited: list[dict[str, Any]] = []
            pattern_count: dict[str, int] = {}
            for ex in available:
                ex_obj = get_exercise(ex.get("exercise_id", ex["name"]))
                mp = ex_obj.movement_pattern if ex_obj else ""
                is_isolation = ex_obj is not None and ex_obj.type == "isolation"
                if not is_isolation and pattern_count.get(mp, 0) >= 2:
                    continue
                limited.append(ex)
                if not is_isolation:
                    pattern_count[mp] = pattern_count.get(mp, 0) + 1
            available = limited

            exercise_limit = 4
            if training_level == "początkujący":
                exercise_limit = 3
            recovery = _assessment_value(assessment, "recovery_score")
            if recovery is not None and int(recovery) <= 4:
                exercise_limit = min(exercise_limit, 2)
            elif recovery is not None and int(recovery) <= 6:
                exercise_limit = min(exercise_limit, 3)
            hours = _assessment_value(assessment, "availability_hours_per_week")
            if hours is not None and target_days and float(hours) / target_days < 0.75:
                exercise_limit = min(exercise_limit, 3)

            selected = available[:exercise_limit]

            # Uzupełnienie dnia do minimum 3 ćwiczeń z partii wspierających.
            if len(selected) < 3:
                added: list[str] = []
                selected_names = {ex["name"] for ex in selected}
                for support_group in _SUPPORTING_GROUPS.get(focus_key, []):
                    if len(selected) >= 3:
                        break
                    support_available = []
                    for ex in _available_for(support_group):
                        if ex["name"] in selected_names:
                            continue
                        support_available.append(ex)
                    support_available = sorted(
                        support_available,
                        key=lambda ex: _rank_key(ex, get_exercise(ex.get("exercise_id", ex["name"])), support_group),
                    )
                    for ex in support_available:
                        if len(selected) >= 3:
                            break
                        selected.append(ex)
                        selected_names.add(ex["name"])
                        added.append(ex["name"])
                if added:
                    day_diagnostics = ("Uzupełniono dzień o ćwiczenia z partii wspierających: "
                                       + ", ".join(added))
            group_day_count[focus_key] = group_day_count.get(focus_key, 0) + 1
            prev_exercise_names = {ex["name"] for ex in selected}
            workout_items = []
            for exercise in selected:
                alternatives = [
                    alt for alt in available if alt["name"] != exercise["name"]
                ][:3]
                workout_items.append({
                    **exercise,
                    "how_to": get_how_to(exercise["name"], is_drill=False) or exercise.get("how_to", ""),
                    "alternatives": [
                        {"name": alt["name"], "sets": alt["sets"], "reps": alt["reps"]}
                        for alt in alternatives
                    ],
                })
            workout_title = f"Sesja {focus_key.title()}"
            is_sport_session = False

        meals = []
        for slot in meal_slots:
            catalog_candidates = list(meal_catalog.get(slot, []))
            candidates = [
                item for item in catalog_candidates
                if _meal_allowed(str(item[0]), forbidden_foods)
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
                    "slot": slot,
                    "name": "Brak bezpiecznej propozycji w katalogu",
                    "kcal": 0,
                    "alternatives": [],
                    "constraint_blocked": True,
                })
                continue
            main = candidates[day_index % len(candidates)]
            meals.append({
                "slot": slot,
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
            if training_locations and day_type != "rest" else [],
            "day_type": day_type,
            "macros": calc_daily_macros(base_calories, day_type),
            "is_sport_session": is_sport_session,
            "diagnostics": day_diagnostics,
            "workout": {
                "title": workout_title,
                "focus": focus_key if not is_sport_session else sport_focus,
                "is_sport_session": is_sport_session,
                "sport": sport_focus if is_sport_session else None,
                "specialization": sport_specialization if is_sport_session else None,
                "scheduled_time": sport_windows.get(day_name) if is_sport_session else None,
                "exercises": workout_items,
            },
            "meals": meals,
        })

    return {
        "generated_at": None,
        "weekly_goal": user.goal,
        "days": days,
        "_planner": {
            "version": "deterministic-v2",
            "target_training_days": target_days,
            "assessment_used": assessment is not None,
            "performance_signals": performance_signals,
            "progress_evidence_used": bool(normalized_progress),
            "progress_evidence_count": len(normalized_progress),
            "schedule_diagnostics": schedule_diagnostics,
            "training_locations_used": bool(training_locations),
            "location_equipment_count": len(location_equipment),
            "reduced_days": reduced_days,
            "group_day_count": group_day_count,
        },
    }
