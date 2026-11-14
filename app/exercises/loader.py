"""Buduje pulę ćwiczeń (_exercise_pool) z jednego źródła danych w app.exercises.

Zwracany kształt jest identyczny ze stara funkcją w legacy_routes.py:

    {
        "klatka": [{"name", "sets", "reps", "notes", "how_to"}, ...],
        "nogi":   [...],
        ...
    }

Grupa ćwiczenia jest wyprowadzana z primary_muscles przez
`muscle_group_for_exercise()` (jedno źródło prawdy). Etykiety grup ze starej
puli legacy (klucze EXERCISE_POOL_DEFINITION) przestają mieć znaczenie przy
doborze - służą jedynie jako źródło nadpisć sets/reps/notes per ćwiczenie.
"""

from __future__ import annotations

from app.exercises.data import EXERCISES, Exercise, muscle_group_for_exercise

# Grupa klucza -> lista wpisów. Wpis: {exercise_id, sets?, reps?, notes?}.
# sets/reps/notes nadpisują wartości domyślne z exercise.sets_range/reps_range.
# Gdy nie podano, stosuje się defaults z definicji ćwiczenia.
EXERCISE_POOL_DEFINITION: dict[str, list[dict]] = {
    "klatka": [
        {"exercise_id": "barbell_bench_press", "sets": "4", "reps": "6-8", "notes": "Łopatki ściśnięte, stopy stabilnie na podłodze."},
        {"exercise_id": "incline_dumbbell_press", "sets": "4", "reps": "8-10", "notes": "Ławka 30-45°, kontroluj fazę ekscentryczną (3 sek.)."},
        {"exercise_id": "decline_dumbbell_press", "sets": "3", "reps": "10-12", "notes": "Aktywuje dolną część klatki."},
        {"exercise_id": "pec_deck", "sets": "3", "reps": "12-15", "notes": "Maksymalne ściskanie klatki na szczycie."},
        {"exercise_id": "cable_crossover", "sets": "3", "reps": "12-15", "notes": "Prowadź dłonie szerokim łukiem przed siebie."},
        {"exercise_id": "dips", "sets": "3", "reps": "8-12", "notes": "Łokcie blisko tułowia, nie rozchylaj ich na boki."},
        {"exercise_id": "weighted_wide_pushups", "sets": "3", "reps": "10-15", "notes": "Talerz na plecach, sztywny tułów."},
        {"exercise_id": "hammer_machine_press", "sets": "3", "reps": "10-12", "notes": "Oparcie ławki ustawione pionowo lub lekko odchylone."},
        {"exercise_id": "floor_press", "sets": "3", "reps": "8-12", "notes": "Wyciskanie hantli leżąc na podłodze, łokcie wzdłuż tułowia."},
        {"exercise_id": "floor_fly", "sets": "3", "reps": "10-15", "notes": "Rozpiętki hantlami na podłodze, lekko ugięte łokcie."},
        {"exercise_id": "pushups_classic", "sets": "3", "reps": "8-15", "notes": "Ciało w jednej linii, brzuch napięty."},
        {"exercise_id": "pushups_knee", "sets": "3", "reps": "10-15", "notes": "Łatwiejszy wariant pompek na kolanach."},
        {"exercise_id": "pushups_feet_elevated", "sets": "3", "reps": "8-12", "notes": "Nogi na podwyższeniu, więcej pracy na górną klatkę."},
        {"exercise_id": "pushups_narrow", "sets": "3", "reps": "8-12", "notes": "Ręce bliżej siebie – więcej pracy tricepsa."},
        {"exercise_id": "pushups_diamond_knee", "sets": "3", "reps": "8-12", "notes": "Pompki diamentowe na kolanach – łatwiejszy wariant."},
    ],
    "nogi": [
        {"exercise_id": "back_squat", "sets": "4", "reps": "6-8", "notes": "Neutralny kręgosłup, kolana podążają za stopami."},
        {"exercise_id": "front_squat", "sets": "4", "reps": "6-8", "notes": "Większe zaangażowanie czworogłowych i gorsetu."},
        {"exercise_id": "romanian_deadlift", "sets": "3", "reps": "8-10", "notes": "Ruch inicjuj biodrem, bez zaokrąglenia lędźwi."},
        {"exercise_id": "bulgarian_split_squat", "sets": "3", "reps": "8/strona", "notes": "Stabilność przed kolanem – kolano nad stopą."},
        {"exercise_id": "leg_press", "sets": "4", "reps": "10-12", "notes": "Nie blokuj kolan na szczycie ruchu."},
        {"exercise_id": "leg_extension", "sets": "3", "reps": "12-15", "notes": "Wyprost do końca, zatrzymaj napięcie na sekundę."},
        {"exercise_id": "leg_curl", "sets": "3", "reps": "10-12", "notes": "Opuszczaj powoli, ważna faza ekscentryczna."},
        {"exercise_id": "standing_calf_raise", "sets": "4", "reps": "15-20", "notes": "Pięty poniżej poziomu stopnia – pełne rozciągnięcie."},
        {"exercise_id": "bodyweight_squat", "sets": "3", "reps": "10-15", "notes": "Przysiad z masą własną – głęboki, kontrolowany."},
        {"exercise_id": "reverse_lunge", "sets": "3", "reps": "10/strona", "notes": "Wykrok w tył – stabilność kolana."},
        {"exercise_id": "glute_bridge", "sets": "3", "reps": "12-15", "notes": "Mostek biodrowy – ścisk pośladków na szczycie."},
        {"exercise_id": "single_leg_glute_bridge", "sets": "3", "reps": "10/strona", "notes": "Mostek jednonóż – trudniejszy wariant."},
        {"exercise_id": "wall_sit", "sets": "3", "reps": "30-45 s", "notes": "Wall sit – izometryczny przysiad przy ścianie."},
    ],
    "plecy": [
        {"exercise_id": "conventional_deadlift", "sets": "4", "reps": "4-6", "notes": "Król ćwiczeń wielostawowych – priorytet techniczny."},
        {"exercise_id": "pullup_wide", "sets": "4", "reps": "6-10", "notes": "Aktywuj łopatki przed ruchem (scapular pull)."},
        {"exercise_id": "chinup", "sets": "3", "reps": "8-10", "notes": "Większe zaangażowanie bicepsów, wąski chwyt."},
        {"exercise_id": "barbell_row", "sets": "4", "reps": "6-8", "notes": "Plecy proste, ściągaj sztangę do pępka."},
        {"exercise_id": "one_arm_dumbbell_row", "sets": "3", "reps": "8-12/strona", "notes": "Łokieć blisko tułowia przez cały ruch."},
        {"exercise_id": "lat_pulldown", "sets": "3", "reps": "10-12", "notes": "Aktywuj łopatki przed ruchem (scapular pull)."},
        {"exercise_id": "seated_cable_row", "sets": "3", "reps": "10-12", "notes": "Łokcie przy tułowiu przez cały ruch."},
        {"exercise_id": "barbell_shrugs", "sets": "3", "reps": "12-15", "notes": "Maksymalna izolacja czworobocznego."},
        {"exercise_id": "australian_pullup", "sets": "3", "reps": "8-12", "notes": "Podciąganie australijskie pod stołem lub niską poręczą."},
        {"exercise_id": "bent_over_row_db", "sets": "3", "reps": "8-12", "notes": "Wiosłowanie hantlami w opadzie tułowia."},
        {"exercise_id": "one_arm_row_thigh", "sets": "3", "reps": "8-12/strona", "notes": "Wiosłowanie jednorącz z oparciem o udo."},
        {"exercise_id": "bodyweight_good_morning", "sets": "3", "reps": "10-15", "notes": "Dobry poranek bez obciążenia – ruch z bioder."},
    ],
    "barki": [
        {"exercise_id": "overhead_press", "sets": "4", "reps": "6-8", "notes": "Brak przeprostu lędźwi, aktywny brzuch."},
        {"exercise_id": "seated_dumbbell_press", "sets": "3", "reps": "8-10", "notes": "Oparcie ławki ustawione pionowo lub lekko odchylone."},
        {"exercise_id": "arnold_press", "sets": "3", "reps": "10-12", "notes": "Rotacja angażuje przedni i środkowy akton barku."},
        {"exercise_id": "lateral_raise", "sets": "4", "reps": "12-15", "notes": "Unoś ramiona do poziomu barków, nie wyżej."},
        {"exercise_id": "front_raise", "sets": "3", "reps": "10-12", "notes": "Łokcie przy tułowiu przez cały ruch."},
        {"exercise_id": "face_pull", "sets": "4", "reps": "15-20", "notes": "Monitoruj tętno – sprint >85% HRmax, marsz <65%."},
        {"exercise_id": "rear_delt_fly", "sets": "3", "reps": "12-15", "notes": "Odpoczynek 30 s między seriami."},
        {"exercise_id": "pike_pushup", "sets": "3", "reps": "6-10", "notes": "Pike push-up - barki bez sprzętu."},
        {"exercise_id": "pike_pushup_feet_elevated", "sets": "3", "reps": "6-10", "notes": "Pike push-up z nogami na podwyższeniu – trudniejszy wariant."},
        {"exercise_id": "reverse_fly_db", "sets": "3", "reps": "12-15", "notes": "Odwodzenie hantli w opadzie - tylne deltoidy."},
        {"exercise_id": "prone_ytw_raises", "sets": "3", "reps": "10-15", "notes": "Prone Y-T-W raises - barki i górne plecy."},
    ],
    "biceps": [
        {"exercise_id": "barbell_curl", "sets": "4", "reps": "8-10", "notes": "Brak bujania tułowia, łokcie przy boku."},
        {"exercise_id": "alternating_dumbbell_curl", "sets": "3", "reps": "10/strona", "notes": "Supinacja nadgarstka w górnej fazie ruchu."},
        {"exercise_id": "concentration_curl", "sets": "3", "reps": "10-12/strona", "notes": "Maksymalna izolacja bicepsa."},
        {"exercise_id": "cable_curl", "sets": "3", "reps": "12-15", "notes": "Łokcie przy tułowiu przez cały ruch."},
        {"exercise_id": "hammer_curl", "sets": "3", "reps": "10-12", "notes": "Neutralny chwyt, łokcie blisko ciała."},
        {"exercise_id": "spider_curl", "sets": "3", "reps": "10-12", "notes": "Maksymalna izolacja bicepsa na ławce skośnej."},
    ],
    "triceps": [
        {"exercise_id": "close_grip_bench_press", "sets": "4", "reps": "6-8", "notes": "Chwyt na szerokość barków, łokcie blisko tułowia."},
        {"exercise_id": "triceps_pushdown", "sets": "3", "reps": "12-15", "notes": "Łokcie przy tułowiu przez cały ruch."},
        {"exercise_id": "skull_crushers", "sets": "3", "reps": "10-12", "notes": "Długa głowa tricepsa – ruch ponad głowę."},
        {"exercise_id": "french_press", "sets": "3", "reps": "10-12", "notes": "Łokcie blisko tułowia, nie rozchylaj ich."},
        {"exercise_id": "triceps_kickback", "sets": "3", "reps": "12-15/strona", "notes": "Ramię przy boku, nie ruszaj go podczas ruchu."},
        {"exercise_id": "dips", "sets": "3", "reps": "8-12", "notes": "Długa głowa tricepsa – ruch ponad głowę."},
        {"exercise_id": "pushups_diamond", "sets": "3", "reps": "8-12", "notes": "Pompki diamentowe - triceps bez sprzętu."},
        {"exercise_id": "french_press_db_two_hand", "sets": "3", "reps": "10-12", "notes": "Francuskie wyciskanie hantli oburącz zza głowy."},
        {"exercise_id": "kickback_db_bent", "sets": "3", "reps": "10-15/strona", "notes": "Prostowanie ramion w opadzie - triceps z hantlem."},
    ],
    "brzuch": [
        {"exercise_id": "plank", "sets": "3", "reps": "45-60 s", "notes": "Linia barków-biodra-kostka, brak opadania bioder."},
        {"exercise_id": "dead_bug", "sets": "3", "reps": "10/strona", "notes": "Lędźwie DOCIŚNIJTE do podłogi przez cały ruch."},
        {"exercise_id": "hanging_leg_raise", "sets": "3", "reps": "8-12", "notes": "Bez bujania – kontrolowany ruch."},
        {"exercise_id": "ab_wheel_rollout", "sets": "3", "reps": "6-10", "notes": "Ćwiczenie balistyczne – siła eksplozywna i koordynacja."},
        {"exercise_id": "hollow_body_hold", "sets": "3", "reps": "30-45 s", "notes": "Lędźwie DOCIŚNIJTE do podłogi przez cały ruch."},
        {"exercise_id": "cable_crunch", "sets": "3", "reps": "15-20", "notes": "Tempo średnie, 500m split ~2:20-2:40."},
        {"exercise_id": "side_plank", "sets": "3", "reps": "8/strona", "notes": "Linia barków-biodra-kostka, brak opadania bioder."},
        {"exercise_id": "superman", "sets": "3", "reps": "10-15", "notes": "Superman - wzmacnianie dolnej części pleców."},
        {"exercise_id": "reverse_snow_angel", "sets": "3", "reps": "10-15", "notes": "Reverse snow angel - barki i górne plecy."},
        {"exercise_id": "bird_dog", "sets": "3", "reps": "10/strona", "notes": "Bird dog - stabilizacja core i dolnej części pleców."},
    ],
    "full body": [
        {"exercise_id": "conventional_deadlift", "sets": "4", "reps": "5-6", "notes": "Wzorzec ruchowy numer jeden – cały łańcuch tylny."},
        {"exercise_id": "clean_and_press", "sets": "3", "reps": "5-6", "notes": "Ćwiczenie balistyczne – siła eksplozywna i koordynacja."},
        {"exercise_id": "back_squat", "sets": "3", "reps": "8", "notes": "Łączy nogi, tułów i stabilizację."},
        {"exercise_id": "pullup_wide", "sets": "3", "reps": "6-8", "notes": "Aktywuj łopatki przed ruchem (scapular pull)."},
        {"exercise_id": "kettlebell_swing", "sets": "4", "reps": "15", "notes": "Ruch inicjuj biodrem, bez zaokrąglenia lędźwi."},
        {"exercise_id": "turkish_get_up", "sets": "3", "reps": "3/strona", "notes": "Ćwiczenie balistyczne – siła eksplozywna i koordynacja."},
    ],
    "cardio": [
        {"exercise_id": "hiit_intervals", "sets": "8", "reps": "1 runda", "notes": "Monitoruj tętno – sprint >85% HRmax, marsz <65%."},
        {"exercise_id": "rowing_steady_state", "sets": "1", "reps": "20 min", "notes": "Tempo średnie, 500m split ~2:20-2:40."},
        {"exercise_id": "jump_rope", "sets": "5", "reps": "1 min", "notes": "Odpoczynek 30 s między seriami."},
        {"exercise_id": "box_jumps", "sets": "4", "reps": "8", "notes": "Bez bujania – kontrolowany ruch."},
        {"exercise_id": "burpees", "sets": "5", "reps": "10", "notes": "Bez bujania – kontrolowany ruch."},
        {"exercise_id": "assault_bike_tabata", "sets": "8", "reps": "20 s sprint / 10 s odpocz.", "notes": "Tempo średnie, 500m split ~2:20-2:40."},
    ],
}

KNOWN_GROUPS: list[str] = ["klatka", "plecy", "barki", "nogi", "biceps", "triceps", "brzuch", "full body", "cardio"]


def _resolve(entry: dict) -> Exercise:
    ex_id = entry["exercise_id"]
    ex = EXERCISES.get(ex_id)
    if ex is None:
        raise KeyError(f"Nieznane id ćwiczenia w puli: {ex_id!r}")
    return ex


def _field(entry: dict, exercise: Exercise, attr: str, default: str) -> str:
    val = entry.get(attr)
    if val is None:
        return default
    return str(val)


def _pool_entries_by_id() -> dict[str, list[dict]]:
    """Skończone wpisy z EXERCISE_POOL_DEFINITION indeksowane po exercise_id."""
    by_id: dict[str, list[dict]] = {}
    for entries in EXERCISE_POOL_DEFINITION.values():
        for entry in entries:
            by_id.setdefault(entry["exercise_id"], []).append(entry)
    return by_id


def build_exercise_pool() -> dict[str, list[dict]]:
    """Zwróć pulę ćwiczeń w kształcie kompatybilnym ze stara funkcją _exercise_pool().

    Grupa każdego ćwiczenia jest wyprowadzana z primary_muscles przez
    muscle_group_for_exercise(), a nie z klucza w EXERCISE_POOL_DEFINITION.
    """
    pool: dict[str, list[dict]] = {group: [] for group in KNOWN_GROUPS}
    entries_by_id = _pool_entries_by_id()

    for ex in list(EXERCISES.values()):
        group = muscle_group_for_exercise(ex)
        if group is None or group not in pool:
            continue
        entries = entries_by_id.get(ex.id, [])
        entry = entries[0] if entries else {}
        summary = ex.description.summary or ""
        pool[group].append({
            "exercise_id": ex.id,
            "name": ex.name_pl,
            "sets": _field(entry, ex, "sets", ex.sets_range),
            "reps": _field(entry, ex, "reps", ex.reps_range),
            "notes": _field(entry, ex, "notes", summary),
            "how_to": summary,
        })
    return pool


__all__ = ["build_exercise_pool", "EXERCISE_POOL_DEFINITION", "KNOWN_GROUPS"]
