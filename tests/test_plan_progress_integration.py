from datetime import date
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


def test_progress_cannot_inject_adaptation_or_recovery_decisions(monkeypatch):
    user = _user()
    user.get_list = lambda key: _get_list(user, key)

    monkeypatch.setattr(
        deterministic,
        "_exercise_pool",
        lambda: {"klatka": [{"name": "Bench", "sets": 3, "reps": 8, "weight_kg": 100}]},
    )
    monkeypatch.setattr(
        deterministic,
        "_default_meal_catalog",
        lambda _: {"Śniadanie": [("Meal", 500)], "Obiad": [("Meal", 500)], "Kolacja": [("Meal", 500)]},
    )

    plan = deterministic.build_deterministic_plan(
        user,
        SimpleNamespace(recovery_score=2),
        [
            {
                "status": "sufficient",
                "sufficient_data": True,
                "exercise_key": "bench",
                "material_change": True,
                "changes": {"volume_kg_delta": -100},
                "decision": "progress",
                "can_start": True,
                "recovery": "ignored",
                "mutates_plan": True,
            }
        ],
    )

    exercise = plan["days"][0]["workout"]["exercises"][0]
    assert exercise["sets"] == 3
    assert exercise["reps"] == 8
    assert "decision" not in plan["_planner"]
    assert "can_start" not in plan["_planner"]
    assert plan["_planner"]["progress_evidence_used"] is True


def test_progress_fingerprint_excludes_temporal_snapshot_objects():
    from app.plan.routes import _planning_progress_fingerprint

    evidence = [{
        "status": "sufficient",
        "sufficient_data": True,
        "exercise_key": "bench",
        "reason_codes": ["MATERIAL_CHANGE"],
        "material_change": True,
        "changes": {"volume_kg_delta": 20},
        "latest": {"session_date": date(2026, 10, 8)},
        "previous": {"session_date": date(2026, 10, 1)},
    }]

    first = _planning_progress_fingerprint(evidence)
    evidence[0]["latest"]["session_date"] = date(2026, 10, 9)
    assert first == _planning_progress_fingerprint(evidence)



def test_progress_evidence_contract_is_read_only_and_finite():
    from app.plan.progress_evidence import build_planning_progress_evidence
    result = build_planning_progress_evidence({
        "status": "sufficient",
        "sufficient_data": True,
        "exercise_key": "bench",
        "material_change": True,
        "changes": {"volume_kg_delta": float("inf"), "reps_delta": 2},
    })
    assert result["changes"] == {"reps_delta": 2.0}
    assert result["mutates_plan"] is False
    assert result["source"] == "canonical_progress"


def test_progress_aware_planner_is_deterministic_for_identical_inputs(monkeypatch):
    user = _user()
    user.get_list = lambda key: _get_list(user, key)
    monkeypatch.setattr(
        deterministic,
        "_exercise_pool",
        lambda: {"klatka": [
            {"name": "First", "sets": 3, "reps": 8},
            {"name": "Bench", "sets": 3, "reps": 8},
        ]},
    )
    monkeypatch.setattr(
        deterministic,
        "_default_meal_catalog",
        lambda _: {"Śniadanie": [("Meal", 500)], "Obiad": [("Meal", 500)], "Kolacja": [("Meal", 500)]},
    )
    evidence = [{
        "status": "sufficient",
        "sufficient_data": True,
        "exercise_key": "bench",
        "material_change": True,
        "changes": {"volume_kg_delta": 20},
    }]
    first = deterministic.build_deterministic_plan(user, None, evidence)
    second = deterministic.build_deterministic_plan(user, None, evidence)
    assert first["days"] == second["days"]
    assert first["_planner"] == second["_planner"]
