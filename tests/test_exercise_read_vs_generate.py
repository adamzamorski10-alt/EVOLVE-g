"""Testy rozdzielenia ścieżki odczytu istniejących planów od nowego generowania."""

from types import SimpleNamespace

import app.plan.deterministic as deterministic
from app.exercises.data import get_exercise


def _user():
    return SimpleNamespace(
        diet="",
        frequency="3 razy",
        goal="masa",
        sport_focus="",
        sport_specialization="",
        calories_target=2500,
        training_focus_json='["klatka"]',
        sport_training_days_json="[]",
        improvement_areas_json="[]",
        available_equipment_json='["sztanga", "hantle"]',
        training_locations_json="[]",
        avoid_exercises_json="[]",
        preferred_foods_json="[]",
        avoid_foods_json="[]",
        allergies="",
        meals_per_day=3,
        equipment=["sztanga", "hantle"],
    )


def test_new_generation_rejects_exercise_outside_db(monkeypatch):
    """Ćwiczenie spoza bazy (bez metadanych) nie trafia do NOWO generowanego planu."""
    user = _user()
    user.get_list = lambda key: {
        "training_focus_json": '["klatka"]',
        "available_equipment_json": '["sztanga", "hantle"]',
        "avoid_exercises_json": "[]",
    }.get(key, "[]")

    monkeypatch.setattr(
        deterministic,
        "_exercise_pool",
        lambda: {
            "klatka": [
                {"name": "Nieznane ćwiczenie spoza bazy", "sets": "3", "reps": "8"},
                {"name": "Wyciskanie sztangi leżąc", "sets": "4", "reps": "6-8"},
            ]
        },
    )
    monkeypatch.setattr(
        deterministic,
        "_default_meal_catalog",
        lambda _: {"Śniadanie": [("Meal", 500)], "Obiad": [("Meal", 500)], "Kolacja": [("Meal", 500)]},
    )

    plan = deterministic.build_deterministic_plan(user, None)
    names = [e["name"] for d in plan["days"] for e in d["workout"]["exercises"]]
    assert "Nieznane ćwiczenie spoza bazy" not in names


def test_read_existing_plan_tolerates_exercise_outside_db():
    """Odczyt istniejących danych toleruje ćwiczenie spoza bazy (get_exercise zwraca None, nie crashuje)."""
    assert get_exercise("nieistniejące_id_ćwiczenia") is None
    # _exercise_equipment_en dla nieznanej nazwy zwraca None zamiast crashować
    assert deterministic._exercise_equipment_en("Nieznane ćwiczenie spoza bazy") is None
