from types import SimpleNamespace

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
