from types import SimpleNamespace

import app.plan.deterministic as deterministic


def _user():
    return SimpleNamespace(
        diet="",
        frequency="3 razy",
        goal="siła",
        sport_focus="",
        sport_specialization="",
        calories_target=2000,
        training_focus_json='["klatka"]',
        improvement_areas_json="[]",
        available_equipment_json='["siłownia"]',
        avoid_exercises_json="[]",
        preferred_foods_json="[]",
        avoid_foods_json="[]",
        allergies="",
        meals_per_day=3,
    )


def _get_list(user, key):
    import json
    return json.loads(getattr(user, key))


def test_progress_evidence_prioritizes_continuity_without_adaptation(monkeypatch):
    user = _user()
    user.get_list = lambda key: _get_list(user, key)

    monkeypatch.setattr(
        deterministic,
        "_exercise_pool",
        lambda: {
            "klatka": [
                {"name": "New Exercise", "sets": 3, "reps": 8},
                {"name": "Bench", "sets": 3, "reps": 8},
            ]
        },
    )
    monkeypatch.setattr(
        deterministic,
        "_default_meal_catalog",
        lambda _: {"Śniadanie": [("Meal", 500)], "Obiad": [("Meal", 500)], "Kolacja": [("Meal", 500)]},
    )

    plan = deterministic.build_deterministic_plan(
        user,
        None,
        [
            {
                "status": "sufficient",
                "sufficient_data": True,
                "exercise_key": "bench",
                "material_change": True,
                "changes": {"volume_kg_delta": 20},
            }
        ],
    )

    exercises = plan["days"][0]["workout"]["exercises"]
    assert exercises[0]["name"] == "Bench"
    assert plan["_planner"]["progress_evidence_used"] is True
    assert plan["_planner"]["progress_evidence_count"] == 1
    assert "decision" not in plan["_planner"]


def test_insufficient_or_missing_progress_does_not_change_base_order(monkeypatch):
    user = _user()
    user.get_list = lambda key: _get_list(user, key)

    monkeypatch.setattr(
        deterministic,
        "_exercise_pool",
        lambda: {
            "klatka": [
                {"name": "First", "sets": 3, "reps": 8},
                {"name": "Second", "sets": 3, "reps": 8},
            ]
        },
    )
    monkeypatch.setattr(
        deterministic,
        "_default_meal_catalog",
        lambda _: {"Śniadanie": [("Meal", 500)], "Obiad": [("Meal", 500)], "Kolacja": [("Meal", 500)]},
    )

    base = deterministic.build_deterministic_plan(user, None)
    insufficient = deterministic.build_deterministic_plan(
        user,
        None,
        [{"status": "insufficient_data", "sufficient_data": False, "exercise_key": "first"}],
    )

    assert base["days"][0]["workout"]["exercises"][0]["name"] == "First"
    assert insufficient["days"][0]["workout"]["exercises"][0]["name"] == "First"
    assert insufficient["_planner"]["progress_evidence_used"] is False
