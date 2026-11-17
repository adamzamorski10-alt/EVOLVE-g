"""
Silnik progresji siłowej dla Evolve.

Czyste funkcje: bez DB, bez mutacji wejść.
Obsługuje: podwójną progresję, zakres reps, zaokrąglenia sprzętu, szacowanie wagi startowej.
"""

from __future__ import annotations
from typing import Any


# Kroki zaokrąglenia wagowego per typ sprzętu
WEIGHT_STEPS = {
    "barbell": 2.5,
    "dumbbell": 2.0,
    "machine": 2.5,
    "cable": 2.5,
    "default": 2.5,
}

# Zakresy powtórzeń per cel użytkownika
GOAL_REPS_RANGES = {
    "masa mięśniowa": {"compound": (6, 12), "isolation": (10, 20)},
    "siła": {"compound": (3, 6), "isolation": (8, 12)},
    "redukcja": {"compound": (8, 15), "isolation": (12, 20)},
    "rekompozycja": {"compound": (6, 10), "isolation": (10, 15)},
    "default": {"compound": (6, 12), "isolation": (10, 15)},
}


def round_to_step(weight: float, step: float) -> float:
    """Zaokrąglij ciężar do najbliższego kroku."""
    if step <= 0:
        return max(0.0, float(weight))
    return max(0.0, round(round(weight / step) * step, 2))


def get_weight_step(equipment: list[str] | None) -> float:
    """Zwróć krok wagowy dla danego sprzętu."""
    if not equipment:
        return WEIGHT_STEPS["default"]
    for eq in equipment:
        key = str(eq).lower().strip()
        if key in WEIGHT_STEPS:
            return WEIGHT_STEPS[key]
        if "hant" in key or "dumbbell" in key:
            return WEIGHT_STEPS["dumbbell"]
        if "sztang" in key or "barbell" in key:
            return WEIGHT_STEPS["barbell"]
        if "maszyn" in key or "machine" in key:
            return WEIGHT_STEPS["machine"]
        if "wyciąg" in key or "wyciag" in key or "cable" in key:
            return WEIGHT_STEPS["cable"]
    return WEIGHT_STEPS["default"]


def get_rep_range_for_goal(goal: str | None, exercise_type: str) -> tuple[int, int]:
    """Zwróć (min_reps, max_reps) na podstawie celu i typu ćwiczenia."""
    goal_str = (goal or "").lower().strip()
    ex_type = "isolation" if exercise_type == "isolation" else "compound"

    if any(k in goal_str for k in ("siła", "sila", "strength", "dynamika", "skoczność", "skocznosc", "eksplozywność", "eksplozywnosc")):
        ranges = GOAL_REPS_RANGES["siła"]
    elif any(k in goal_str for k in ("masa", "hipertrof", "hypertrophy", "mięśni", "miesni", "budowa masy", "budowa beztłuszczowej")):
        ranges = GOAL_REPS_RANGES["masa mięśniowa"]
    elif any(k in goal_str for k in ("redukcja", "cut", "spalanie", "odchudzanie")) or ("tłuszcz" in goal_str and "beztłuszcz" not in goal_str):
        ranges = GOAL_REPS_RANGES["redukcja"]
    elif any(k in goal_str for k in ("rekompozycj", "recomposition")):
        ranges = GOAL_REPS_RANGES["rekompozycja"]
    else:
        ranges = GOAL_REPS_RANGES["default"]

    return ranges[ex_type]


def estimate_starting_weight(
    user_weight_kg: float,
    exercise_type: str,  # "compound" or "isolation"
    movement_pattern: str,  # "squat", "hinge", "horizontal_push", etc.
    gender: str,
    training_level: str,
    equipment: list[str] | None = None,
) -> float:
    """
    Szacuj wagę startową na podstawie wagi ciała, wzorca ruchu, sprzętu i profilu.
    Konserwatywne wartości startowe zapewniające bezpieczną kalibrację.
    """
    eq_set = {str(e).lower().strip() for e in (equipment or [])}
    if eq_set and eq_set <= {"bodyweight"} or movement_pattern == "core":
        return 0.0

    bw = max(45.0, float(user_weight_kg or 70.0))

    # Bazowe % masy ciała dla sztangi (compound) u średniozaawansowanego mężczyzny
    pattern_pct = {
        "squat": 0.70,
        "hinge": 0.75,
        "horizontal_push": 0.55,
        "vertical_push": 0.35,
        "horizontal_pull": 0.50,
        "vertical_pull": 0.00,  # najczęściej podciąganie lub wyciąg
        "lunge": 0.30,
        "core": 0.00,
        "isolation": 0.12,
    }
    base_pct = pattern_pct.get(movement_pattern, 0.30)
    if exercise_type == "isolation":
        base_pct = 0.12

    # Korekta poziomu zaawansowania
    level_str = (training_level or "").lower().strip()
    if any(k in level_str for k in ("beginner", "początkujący", "poczatkujacy")):
        level_mult = 0.60
    elif any(k in level_str for k in ("advanced", "zaawansowany", "elite")):
        level_mult = 1.00
    else:
        level_mult = 0.80

    # Korekta płci
    gender_str = (gender or "").lower().strip()
    gender_mult = 0.65 if any(k in gender_str for k in ("kobieta", "female", "f")) else 1.0

    weight = bw * base_pct * level_mult * gender_mult

    # Dla hantli waga jest podawana na jedną rękę (hantel) -> ok. 40-50% oburęcznej sztangi
    is_dumbbell = any("hant" in e or "dumbbell" in e for e in eq_set)
    if is_dumbbell:
        weight = weight * 0.45

    step = get_weight_step(equipment)
    return round_to_step(weight, step)


def decide_next_step(
    current_weight: float,
    current_reps: int,
    reps_min: int,
    reps_max: int,
    average_rpe: float | None,
    completion_pct: float,
    equipment: list[str] | None,
    sessions_without_progress: int = 0,
) -> dict:
    """
    Podwójna progresja: decyduj o kolejnym kroku (ciężar vs powtórzenia).
    
    Zwraca:
        dict: action, next_weight, next_reps, reason
    """
    eq_set = {str(e).lower().strip() for e in (equipment or [])}
    is_pure_bodyweight = (eq_set and eq_set <= {"bodyweight"}) or (current_weight == 0.0 and not equipment)
    step = get_weight_step(equipment)

    # 1. Redukcja przy złym wykonaniu (<80% serii)
    if completion_pct < 80:
        if is_pure_bodyweight or current_weight <= 0:
            next_reps = max(1, current_reps - 1)
            return {
                "action": "reduce_reps",
                "next_weight": 0.0,
                "next_reps": max(reps_min, next_reps),
                "reason": "Ukończono mniej niż 80% zaplanowanych serii — obniżam liczbę powtórzeń",
            }
        next_weight = round_to_step(current_weight * 0.90, step)
        if next_weight == current_weight:
            next_weight = max(0.0, current_weight - step)
        return {
            "action": "reduce_load",
            "next_weight": max(0.0, next_weight),
            "next_reps": reps_min,
            "reason": "Ukończono mniej niż 80% serii — zmniejszam ciężar roboczy o 10%",
        }

    # 2. Redukcja przy przeciążeniu (RPE >= 9.5)
    if average_rpe is not None and average_rpe >= 9.5:
        if is_pure_bodyweight or current_weight <= 0:
            return {
                "action": "maintain",
                "next_weight": 0.0,
                "next_reps": max(reps_min, current_reps - 1),
                "reason": "RPE ≥ 9.5 (blisko upadku) — obniżam powtórzenia dla regeneracji",
            }
        next_weight = round_to_step(current_weight * 0.925, step)
        if next_weight == current_weight:
            next_weight = max(0.0, current_weight - step)
        return {
            "action": "reduce_load",
            "next_weight": max(0.0, next_weight),
            "next_reps": reps_min,
            "reason": "Średnie RPE ≥ 9.5 (zbyt duży wysiłek) — zmniejszam obciążenie",
        }

    # 3. Utrzymanie przy wysokim zmęczeniu (8.5 <= RPE < 9.5)
    if average_rpe is not None and average_rpe >= 8.5:
        return {
            "action": "maintain",
            "next_weight": current_weight,
            "next_reps": min(current_reps + 1, reps_max) if current_reps < reps_max else current_reps,
            "reason": f"RPE {average_rpe} (wysoki wysiłek) — utrzymuję obecny ciężar ({current_weight} kg)",
        }

    # 4. Progresja dla masy własnej
    if is_pure_bodyweight or current_weight <= 0:
        if current_reps >= reps_max:
            # Osiągnięto górę zakresu dla masy własnej -> można zwiększyć reps lub utrzymać
            return {
                "action": "progress_reps",
                "next_weight": 0.0,
                "next_reps": current_reps + 1,
                "reason": f"Osiągnięto górną granicę {reps_max} powtórzeń — dodaję +1 powtórzenie (cel: {current_reps + 1})",
            }
        next_reps = min(current_reps + 1, reps_max)
        return {
            "action": "progress_reps",
            "next_weight": 0.0,
            "next_reps": next_reps,
            "reason": f"W zakresie {reps_min}-{reps_max} — dodaję 1 powtórzenie (cel: {next_reps})",
        }

    # 5. Podwójna progresja z ciężarem zewnętrznym:
    # Czy osiągnięto górę zakresu powtórzeń?
    if current_reps >= reps_max:
        # Podnieś ciężar o 1 krok, wróć do dolnej granicy zakresu powtórzeń
        new_weight = round_to_step(current_weight + step, step)

        # Bezpieczeństwo: limit skoku maksymalnie 10% bieżącego ciężaru (chyba że 1 krok to minimum)
        max_jump = max(step, current_weight * 0.10)
        if (new_weight - current_weight) > max_jump:
            new_weight = round_to_step(current_weight + max_jump, step)
        if new_weight <= current_weight:
            new_weight = current_weight + step

        return {
            "action": "progress_load",
            "next_weight": new_weight,
            "next_reps": reps_min,
            "reason": f"Osiągnięto {reps_max} powtórzeń przy kontrolowanym wysiłku — zwiększam ciężar o {step} kg (do {new_weight} kg) i wracam do {reps_min} powt.",
        }

    # W zakresie, ale poniżej góry zakresu -> ten sam ciężar, +1 powtórzenie
    target_reps = min(current_reps + 1, reps_max)
    return {
        "action": "progress_reps",
        "next_weight": current_weight,
        "next_reps": target_reps,
        "reason": f"W zakresie {reps_min}-{reps_max} powtórzeń — utrzymuję {current_weight} kg i dodaję +1 powtórzenie (cel: {target_reps})",
    }
