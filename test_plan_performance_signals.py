from types import SimpleNamespace

from app.plan.deterministic import build_deterministic_plan
from app.plan.performance_signals import build_performance_signals, prioritize_sport_drills


def assessment(**overrides):
    values = {
        "shooting_pct": 55,
        "free_throw_pct": 65,
        "sprint_30m_seconds": 5.5,
        "vertical_jump_cm": 40,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_basketball_weak_metrics_emit_bounded_priorities():
    signals = build_performance_signals(
        assessment(),
        sport_focus="koszykówka",
    )

    assert signals["sport"] == "koszykówka"
    assert signals["priorities"] == ["shooting", "free_throw", "speed", "explosiveness"]
    assert all(set(item) == {"value", "threshold", "priority"} for item in signals["signals"].values())
    assert all(isinstance(item["priority"], bool) for item in signals["signals"].values())


def test_basketball_missing_metrics_are_not_inferred():
    signals = build_performance_signals(
        assessment(shooting_pct=None, free_throw_pct=None, sprint_30m_seconds=None, vertical_jump_cm=None),
        sport_focus="koszykówka",
    )

    assert signals["priorities"] == []
    assert signals["signals"] == {}


def test_non_basketball_assessment_does_not_create_basketball_signals():
    signals = build_performance_signals(
        assessment(),
        sport_focus="siłownia",
    )

    assert signals == {"sport": "siłownia", "priorities": [], "signals": {}}


def test_threshold_boundaries_do_not_create_false_positive_priority():
    signals = build_performance_signals(
        assessment(
            shooting_pct=60,
            free_throw_pct=70,
            sprint_30m_seconds=5,
            vertical_jump_cm=45,
        ),
        sport_focus="koszykówka",
    )

    assert signals["priorities"] == []
    assert all(item["priority"] is False for item in signals["signals"].values())


def test_priority_reorders_matching_drills_stably():
    drills = [
        {"name": "Catch-and-shoot"},
        {"name": "Sprint acceleration"},
        {"name": "Ball handling"},
        {"name": "Spot shooting"},
    ]

    signals = {
        "priorities": ["shooting", "speed"],
    }

    ordered = prioritize_sport_drills(drills, signals)

    assert [item["name"] for item in ordered] == [
        "Catch-and-shoot",
        "Spot shooting",
        "Sprint acceleration",
        "Ball handling",
    ]


def test_no_priority_preserves_catalog_order():
    drills = [
        {"name": "A"},
        {"name": "B"},
        {"name": "C"},
    ]

    assert prioritize_sport_drills(drills, {"priorities": []}) == drills


class _PlannerUser:
    diet = ""
    goal = "forma"
    frequency = "1"
    sport_focus = "koszykówka"
    sport_specialization = "drybling"
    calories_target = 2400

    def __init__(self):
        self._lists = {
            "sport_training_days_json": ["Poniedziałek"],
            "training_focus_json": ["nogi"],
            "improvement_areas_json": [],
            "available_equipment_json": [],
            "avoid_exercises_json": [],
            "preferred_foods_json": [],
            "avoid_foods_json": [],
        }

    def get_list(self, field):
        return self._lists.get(field, [])


def _sport_day(plan):
    return next(day for day in plan["days"] if day["is_sport_session"])


def test_planner_adds_missing_shooting_priority_without_replacing_specialization():
    plan = build_deterministic_plan(
        _PlannerUser(),
        assessment(
            shooting_pct=50,
            free_throw_pct=80,
            sprint_30m_seconds=4.5,
            vertical_jump_cm=50,
            sessions_per_week=1,
        ),
    )

    day = _sport_day(plan)
    names = [item["name"] for item in day["workout"]["exercises"]]

    assert day["workout"]["specialization"] == "drybling"
    assert names[:2] == ["Figure-8 Dribbling", "Stationary Crossover"]
    assert "Rzuty osobiste" in names
    assert plan["_planner"]["performance_signals"]["priorities"] == ["shooting"]


def test_planner_applies_speed_and_explosiveness_when_specialization_has_no_match():
    plan = build_deterministic_plan(
        _PlannerUser(),
        assessment(
            shooting_pct=80,
            free_throw_pct=80,
            sprint_30m_seconds=5.6,
            vertical_jump_cm=40,
            sessions_per_week=1,
        ),
    )

    names = [item["name"] for item in _sport_day(plan)["workout"]["exercises"]]

    assert names[:2] == ["Figure-8 Dribbling", "Stationary Crossover"]
    assert names[2:] == ["Sprint 30 m", "Wyskok dosiężny"]


def test_planner_does_not_add_secondary_performance_drills_when_metrics_are_good():
    plan = build_deterministic_plan(
        _PlannerUser(),
        assessment(
            shooting_pct=80,
            free_throw_pct=80,
            sprint_30m_seconds=4.5,
            vertical_jump_cm=50,
            sessions_per_week=1,
        ),
    )

    names = [item["name"] for item in _sport_day(plan)["workout"]["exercises"]]

    assert names == ["Figure-8 Dribbling", "Stationary Crossover"]
    assert plan["_planner"]["performance_signals"]["priorities"] == []


def test_planner_missing_metrics_keeps_base_specialization_plan():
    plan = build_deterministic_plan(
        _PlannerUser(),
        assessment(
            shooting_pct=None,
            free_throw_pct=None,
            sprint_30m_seconds=None,
            vertical_jump_cm=None,
            sessions_per_week=1,
        ),
    )

    names = [item["name"] for item in _sport_day(plan)["workout"]["exercises"]]

    assert names == ["Figure-8 Dribbling", "Stationary Crossover"]
    assert plan["_planner"]["performance_signals"]["priorities"] == []
