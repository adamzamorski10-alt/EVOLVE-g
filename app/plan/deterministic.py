"""Deterministic EVOLVE planning core.

This module is the implementation boundary for the new core-loop planner.
It may reuse legacy catalogs as reference data, but planning decisions here
are deterministic and derive only from explicit profile/assessment inputs.
"""

from __future__ import annotations

from typing import Any

from app.exercise_descriptions import get_how_to
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


def _frequency_days(value: str | None) -> int:
    import re

    numbers = [int(x) for x in re.findall(r"\d+", str(value or ""))]
    if not numbers:
        return 3
    # For a range such as "3-4 razy" use the upper bound so the generated
    # plan does not silently under-deliver the requested weekly frequency.
    return max(1, min(6, max(numbers)))


def _equipment_aliases(items: list[str]) -> set[str]:
    aliases = {
        "sztanga olimpijska": "sztanga",
        "hantle regulowane": "hantle",
        "wyciąg": "wyciąg",
        "maszyny": "maszyny",
        "siłownia": "siłownia",
    }
    return {aliases.get(item.strip().lower(), item.strip().lower()) for item in items if item and item.strip()}


def _exercise_required_equipment(name: str) -> set[str]:
    n = name.lower()
    required: set[str] = set()
    if "sztang" in n:
        required.add("sztanga")
    if "hantl" in n:
        required.add("hantle")
    if "kettlebell" in n:
        required.add("kettlebell")
    if any(token in n for token in ("maszyn", "leg press", "pec deck", "hammer")):
        required.add("maszyny")
    if any(token in n for token in ("kabel", "brama")):
        required.add("wyciąg")
    if "poręcz" in n:
        required.add("poręcze")
    if "ławce" in n or "ławka" in n:
        required.add("ławka")
    return required


def _exercise_allowed(name: str, equipment: set[str], avoid_exercises: list[str]) -> bool:
    lowered = name.lower()
    if any(term.lower() in lowered for term in avoid_exercises if term):
        return False
    if not equipment or "siłownia" in equipment or "gym" in equipment:
        return True
    required = _exercise_required_equipment(name)
    return not required or required.issubset(equipment)


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


def build_deterministic_plan(user: Any, assessment: Any = None) -> dict:
    """Generate a reproducible weekly plan from explicit inputs only."""
    meal_catalog = _default_meal_catalog(user.diet or "")
    exercise_pool = _exercise_pool()

    profile_days = _frequency_days(user.frequency)
    assessment_days = _assessment_value(assessment, "sessions_per_week")
    target_days = max(1, min(6, int(assessment_days or profile_days)))

    sport_focus = (user.sport_focus or "").lower().strip()
    sport_specialization = (user.sport_specialization or "").lower().strip()
    configured_sport_days = {
        d.strip()
        for d in user.get_list("sport_training_days_json")
        if isinstance(d, str) and d.strip()
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

    candidate_days = [name for name, is_rest in _DAY_SCHEDULE if not is_rest]
    selected_days: list[str] = [
        day for day in candidate_days if day in configured_sport_days
    ]
    for day in candidate_days:
        if day not in selected_days and len(selected_days) < target_days:
            selected_days.append(day)
    selected_days = selected_days[:target_days]

    focus = [x.lower() for x in user.get_list("training_focus_json") if isinstance(x, str) and x.strip()]
    improve = [x.lower() for x in user.get_list("improvement_areas_json") if isinstance(x, str) and x.strip()]
    preferred = focus + [x for x in improve if x not in focus] or ["klatka", "plecy", "nogi", "brzuch", "barki"]

    regular_days = [d for d in selected_days if d not in configured_sport_days or not sport_drills]
    focus_sequence: list[str] = []
    for index in range(len(regular_days)):
        focus_sequence.append(preferred[index % len(preferred)])
    focus_iter = iter(focus_sequence)

    equipment = _equipment_aliases(user.get_list("available_equipment_json"))
    avoid_exercises = _normalized_constraints(user.get_list("avoid_exercises_json"))
    preferred_foods = _normalized_constraints(user.get_list("preferred_foods_json"))
    avoid_foods = _normalized_constraints(user.get_list("avoid_foods_json"))
    allergies = _normalized_constraints((user.allergies or "").replace(",", ";").split(";"))
    forbidden_foods = avoid_foods + [item for item in allergies if item not in avoid_foods]
    meal_slots = _meal_slots(max(3, min(5, int(user.meals_per_day or 3))))

    base_calories = user.calories_target
    if not base_calories:
        from app.legacy_routes import calc_calories

        base_calories = calc_calories(user)

    days: list[dict] = []
    for day_index, (day_name, is_sunday_rest) in enumerate(_DAY_SCHEDULE):
        is_selected = day_name in selected_days
        is_sport_day = is_selected and bool(sport_drills) and day_name in configured_sport_days

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
            workout_title = f"Sesja Sportowa – {sport_focus.title()} ({sport_specialization.title() or 'Specjalistyczna'})"
            is_sport_session = True
        else:
            raw_focus = next(focus_iter, preferred[0])
            focus_key = _MUSCLE_MAP.get(raw_focus, raw_focus)
            if focus_key not in exercise_pool:
                focus_key = "klatka"
            day_type = _day_type(day_name, focus_key)

            available = [
                ex for ex in exercise_pool.get(focus_key, [])
                if _exercise_allowed(ex["name"], equipment, avoid_exercises)
            ]
            if not available:
                # Never silently bypass equipment or exercise restrictions.
                available = []

            exercise_limit = 4
            if _assessment_value(assessment, "training_level") == "początkujący":
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
            "day_type": day_type,
            "macros": calc_daily_macros(base_calories, day_type),
            "is_sport_session": is_sport_session,
            "workout": {
                "title": workout_title,
                "focus": focus_key if not is_sport_session else sport_focus,
                "is_sport_session": is_sport_session,
                "sport": sport_focus if is_sport_session else None,
                "specialization": sport_specialization if is_sport_session else None,
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
        },
    }
