"""Generuje próbki planów treningowych dla generatora v2.

Używa wyłącznie `app.plan.deterministic.build_deterministic_plan` (PLAN_GENERATOR=v2).
Zawartość markdown zwracana przez `generate_docs_content()` jest źródłem prawdy dla
`docs/PLAN_SAMPLES_V2.md` (test R34 porównuje plik z wynikiem w pamięci).
"""

from __future__ import annotations

import os
import sys
from types import SimpleNamespace

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

os.environ.setdefault("PLAN_GENERATOR", "v2")

from app.plan.deterministic import build_deterministic_plan  # noqa: E402
from app.exercises.data import get_exercise  # noqa: E402

# ---------------------------------------------------------------------------
# Osoby testowe (odpowiadają CONFIGS z tests/test_generator_v2_splits.py)
# ---------------------------------------------------------------------------

GYM_FULL = ["sztanga", "hantle", "maszyny", "wyciąg", "ławka", "poręcze", "siłownia"]
DUMBBELLS = ["hantle", "ławka"]

PERSONAS: dict[str, dict] = {
    "persona1_beginner_gym_3d": {
        "frequency": "3 dni", "days": 3, "level": "początkujący",
        "equipment": GYM_FULL, "focus": ["klatka", "plecy", "nogi", "brzuch", "barki"],
    },
    "persona2_beginner_dumbbells_2d": {
        "frequency": "2 dni", "days": 2, "level": "początkujący",
        "equipment": DUMBBELLS, "focus": ["klatka", "plecy", "nogi", "brzuch", "barki"],
    },
    "persona3_intermediate_gym_4d": {
        "frequency": "4 dni", "days": 4, "level": "średniozaawansowany",
        "equipment": GYM_FULL, "focus": ["klatka", "plecy", "nogi", "brzuch", "barki"],
    },
    "persona7_beginner_bodyweight_3d": {
        "frequency": "3 dni", "days": 3, "level": "początkujący",
        "equipment": [], "focus": ["klatka", "plecy", "nogi", "brzuch", "barki"],
    },
    "intermediate_gym_5d": {
        "frequency": "5 dni", "days": 5, "level": "średniozaawansowany",
        "equipment": GYM_FULL, "focus": ["klatka", "plecy", "nogi", "brzuch", "barki"],
    },
    "intermediate_gym_6d": {
        "frequency": "6 dni", "days": 6, "level": "średniozaawansowany",
        "equipment": GYM_FULL, "focus": ["klatka", "plecy", "nogi", "brzuch", "barki"],
    },
    "intermediate_gym_1d": {
        "frequency": "1 dzień", "days": 1, "level": "średniozaawansowany",
        "equipment": GYM_FULL, "focus": ["klatka", "plecy", "nogi", "brzuch", "barki"],
    },
    "beginner_gym_4d": {
        "frequency": "4 dni", "days": 4, "level": "początkujący",
        "equipment": GYM_FULL, "focus": ["klatka", "plecy", "nogi", "brzuch", "barki"],
    },
}

# Etykiety wyświetlane dla osób w dokumencie.
DISPLAY = {
    "persona1_beginner_gym_3d": ("persona 1", "początkujący, 3 dni, masa, pełna siłownia"),
    "persona2_beginner_dumbbells_2d": ("persona 2", "2 dni, hantle + ławka"),
    "persona3_intermediate_gym_4d": ("persona 3", "średniozaawansowany, 4 dni, masa, pełna siłownia"),
    "persona7_beginner_bodyweight_3d": ("persona 7 pure bodyweight", "3 dni, bez sprzętu"),
    "intermediate_gym_5d": ("intermediate gym 5d", "5 dni, siłownia"),
    "intermediate_gym_6d": ("intermediate gym 6d", "6 dni, siłownia"),
    "intermediate_gym_1d": ("intermediate gym 1d", "1 dzień, siłownia"),
    "beginner_gym_4d": ("beginner gym 4d", "4 dni, siłownia"),
}


def _make_user(*, frequency, days, level, equipment_list, focus, goal="masa mięśniowa"):
    import json
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
        training_focus_json=__import__("json").dumps(focus, ensure_ascii=False),
        improvement_areas_json="[]",
        available_equipment_json=__import__("json").dumps(equipment_list, ensure_ascii=False),
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
    user.get_list = lambda field: __import__("json").loads(getattr(user, field, "[]") or "[]")
    return user


def _make_assessment(*, days, level):
    return SimpleNamespace(
        sessions_per_week=days,
        training_level=level,
        recovery_score=None,
        availability_hours_per_week=None,
    )


def build_plan(key: str) -> dict:
    cfg = PERSONAS[key]
    user = _make_user(
        frequency=cfg["frequency"], days=cfg["days"], level=cfg["level"],
        equipment_list=cfg["equipment"], focus=cfg["focus"],
    )
    assessment = _make_assessment(days=cfg["days"], level=cfg["level"])
    return build_deterministic_plan(user, assessment)


def _exercise_line(day_name: str, ex: dict, plan_level: str) -> str:
    ex_obj = get_exercise(ex.get("exercise_id", ex["name"]))
    if ex_obj is None:
        return f'{day_name}, {ex.get("exercise_id","")}, {ex.get("name","")}, ?, ?, {ex.get("sets","")}'
    eq = ", ".join(ex_obj.equipment)
    return f'{day_name}, {ex_obj.id}, {ex_obj.name_pl}, {ex_obj.level}, {eq}, {ex.get("sets","")}'


def _push_pull(days):
    from app.plan.generator_v2 import calculate_push_pull_sets
    return calculate_push_pull_sets(days)


def _volume_notes(plan) -> str:
    notes = plan["_planner"]["schedule_diagnostics"].get("notes", [])
    return " ".join(notes) if notes else "-"


def _plan_markdown(key: str, plan: dict) -> str:
    display_name, subtitle = DISPLAY[key]
    cfg = PERSONAS[key]
    training_days = [d for d in plan["days"] if d["day_type"] != "rest"]
    summary = plan["_planner"]["weekly_summary"]
    sets = summary["sets_per_group"]
    sessions = summary["sessions_per_group"]
    push_s, pull_s = _push_pull(plan["days"])
    ratio = (pull_s / push_s) if push_s else 0.0

    lines: list[str] = []
    lines.append(f"## {display_name} ({cfg['days']} dni, siłownia)")
    lines.append(
        f"- Split: `{plan['_planner']['split_key']}` | Cel: {plan['weekly_goal']} | "
        f"Poziom: {cfg['level']} | Sprzęt: {', '.join(cfg['equipment']) or 'masa własna'}"
    )
    lines.append(f"- Dni treningowe: {len(training_days)}/{cfg['days']} | Niewypełnione: 0")
    diag = _volume_notes(plan)
    lines.append(f"- Diagnostyka: {diag}")
    lines.append("")
    lines.append(f"- Balans pchanie/ciągnięcie: Pchanie = {push_s} serii, Ciągnięcie = {pull_s} serii (stosunek ciągnięcie/pchanie = {ratio:.2f})")
    lines.append("")

    for day in training_days:
        exs = day["workout"]["exercises"]
        lines.append(f"| Dzień | Sesja | ćwiczenie | serie | powtórzenia | wzorzec ruchu | diagnostics |")
        lines.append(f"|-------|-------|-------------|-------|-------------|---------------|-------------|")
        for ex in exs:
            ex_obj = get_exercise(ex.get("exercise_id", ex["name"]))
            pattern = ex_obj.movement_pattern if ex_obj else ""
            lines.append(
                f"| {day['day']} | {day['workout']['focus']} | {ex['name']} | {ex['sets']} | {ex['reps']} | {pattern} | - |"
            )
        lines.append(f"| | | **Szacowany czas sesji: {day['workout'].get('estimated_minutes', 0)} min** | | | | |")
        lines.append("")

    # Klasyfikacja
    lines.append("### Klasyfikacja ćwiczeń (pchanie / ciągnięcie / żadne)")
    lines.append("| Dzień | ćwiczenie | Serie | Wzorzec ruchu | Grupa główna | Klasyfikacja |")
    lines.append("|-------|-----------|-------|---------------|--------------|--------------|")
    push_patterns = {"horizontal_push", "vertical_push"}
    pull_patterns = {"horizontal_pull", "vertical_pull"}
    pull_muscles = {"back", "lats", "upper_back", "mid_back", "lower_back", "traps", "biceps", "rear_delts"}
    push_muscles = {"chest", "triceps", "front_delts"}
    total_push = 0
    total_pull = 0
    for day in training_days:
        for ex in day["workout"]["exercises"]:
            ex_obj = get_exercise(ex.get("exercise_id", ex["name"]))
            if ex_obj is None:
                continue
            mp = ex_obj.movement_pattern
            pm = ex_obj.primary_muscles[0] if ex_obj.primary_muscles else ""
            group = {"chest": "klatka", "back": "plecy", "lats": "plecy", "upper_back": "plecy",
                     "mid_back": "plecy", "lower_back": "plecy", "traps": "plecy",
                     "front_delts": "barki", "side_delts": "barki", "rear_delts": "barki",
                     "biceps": "biceps", "triceps": "triceps", "quads": "nogi",
                     "hamstrings": "nogi", "glutes": "nogi", "calves": "nogi",
                     "abs": "brzuch", "obliques": "brzuch"}.get(pm, pm)
            if mp in push_patterns or (ex_obj.type == "isolation" and pm in push_muscles):
                klas = "PCHANIE"
                total_push += ex["sets"]
            elif mp in pull_patterns or pm in pull_muscles:
                klas = "CIĄGNIĘCIE"
                total_pull += ex["sets"]
            else:
                klas = "żadne"
            lines.append(f"| {day['day']} | {ex['name']} | {ex['sets']} | {mp} | {group} | {klas} |")
    lines.append(f"| **SUMA** | | | | | **Pchanie: {total_push}, Ciągnięcie: {total_pull} (ratio: {total_pull/total_push:.2f})** |")
    lines.append("")

    # weekly_summary
    lines.append("### weekly_summary")
    lines.append("")
    lines.append("#### Serie i sesje na grupę mięśniową")
    lines.append("| Grupa mięśniowa | Sesje w tygodniu | Serie robocze w tygodniu |")
    lines.append("|-----------------|------------------|--------------------------|")
    for g in ("klatka", "plecy", "barki", "biceps", "triceps", "nogi", "brzuch"):
        lines.append(f"| {g} | {sessions.get(g, 0)} | {sets.get(g, 0)} |")
    lines.append("")
    lines.append("#### Serie na mięsień (podgrupy)")
    lines.append("| Mięsień (podgrupa) | Serie robocze w tygodniu | Cel serii (min-max) |")
    lines.append("|--------------------|--------------------------|---------------------|")
    from app.plan.generator_v2 import VOLUME_TARGETS_INTERMEDIATE, _volume_subgroup, _summary_group
    subgroup_names = {
        "chest": "klatka", "back": "plecy", "side_delts": "barki boczne",
        "biceps": "biceps", "triceps": "triceps", "quads": "czworogłowe",
        "hamstrings": "dwugłowe", "calves": "łydki",
    }
    is_beginner = cfg["level"] in ("początkujący", "beginner")
    for muscle in ("chest", "back", "side_delts", "biceps", "triceps", "quads", "hamstrings", "calves"):
        low, high = VOLUME_TARGETS_INTERMEDIATE[muscle]
        if is_beginner:
            low = max(1, int(round(low * 0.7)))
            high = max(low, int(round(high * 0.7)))
        actual = 0
        for day in training_days:
            for ex in day["workout"]["exercises"]:
                ex_obj = get_exercise(ex.get("exercise_id", ex["name"]))
                if ex_obj and _volume_subgroup(ex_obj.primary_muscles) == muscle:
                    actual += ex["sets"]
        lines.append(f"| {subgroup_names[muscle]} ({muscle}) | {actual} | {low}-{high} |")
    lines.append("")
    return "\n".join(lines)


def generate_docs_content() -> str:
    """Zwraca pełną zawartość docs/PLAN_SAMPLES_V2.md jako jeden napis."""
    lines: list[str] = []
    lines.append("# Próbki planów treningowych - generator v2 (szablony sesji oparte na wzorcach ruchu)")
    lines.append("")
    lines.append("Generowane realnym kodem z `PLAN_GENERATOR=v2` (`app.plan.deterministic.build_deterministic_plan` -> `build_split_plan`).")
    lines.append("Serie są liczbami całkowitymi (pierwsze ćwiczenie złożone sesji dostaje górną wartość zakresu, pozostałe dolną).")
    lines.append("estimated_minutes = suma serii x 2,5 min + 5 min.")
    lines.append("")
    for key in PERSONAS:
        plan = build_plan(key)
        lines.append(_plan_markdown(key, plan))
    return "\n".join(lines) + "\n"


def _print_sample(key: str, limit: int = 40) -> None:
    plan = build_plan(key)
    display_name, _ = DISPLAY[key]
    print(f"=== {display_name} ({key}) ===")
    count = 0
    for day in plan["days"]:
        if day["day_type"] == "rest":
            continue
        for ex in day["workout"]["exercises"]:
            if count >= limit:
                return
            print(_exercise_line(day["day"], ex, PERSONAS[key]["level"]))
            count += 1


def main() -> int:
    # Wypisz pierwsze 40 linii dla person 1, 3 i beginner_gym_4d.
    for key in ("persona1_beginner_gym_3d", "persona3_intermediate_gym_4d", "beginner_gym_4d"):
        _print_sample(key, limit=40)
        print()
    # Zapisz dokument.
    content = generate_docs_content()
    docs_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "PLAN_SAMPLES_V2.md")
    with open(docs_path, "w", encoding="utf-8") as fh:
        fh.write(content)
    print(f"Zapisano {docs_path} ({len(content)} znaków).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
