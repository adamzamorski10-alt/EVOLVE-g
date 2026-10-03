from pathlib import Path


INDEX = Path(__file__).with_name("index.html")


def test_training_execution_ui_is_wired_to_stage2_api():
    html = INDEX.read_text(encoding="utf-8")
    required = [
        "evolveStartTrainingBtn",
        "window.evolveStartTraining",
        "/app/training/sessions/start",
        "/app/training/sessions/" + "' + encodeURIComponent(session.id) + '" + "/sets",
        "/app/training/sessions/" + "' + encodeURIComponent(session.id) + '" + "/complete",
        "data-save-ex",
        "✓ Zakończ trening",
    ]
    for marker in required:
        assert marker in html, f"Missing training UI integration marker: {marker}"


def test_training_execution_ui_keeps_existing_today_container():
    html = INDEX.read_text(encoding="utf-8")
    assert 'id="activeDayExerciseList"' in html
    assert "loadTodayData" in html
    assert "renderWorkoutsList" in html


def test_my_day_is_integrated_into_shared_dashboard_shell():
    html = INDEX.read_text(encoding="utf-8")
    required = [
        'id="tab-my-day"',
        'data-tab="my-day"',
        "showTab('my-day')",
        "loadEvolveMyDay",
        "/app/training/today",
        'id="myDayWorkout"',
        'id="myDayExercises"',
        'href="/app/training/session-ui"',
    ]
    for marker in required:
        assert marker in html, f"Missing Mój dzień shell marker: {marker}"


def test_my_day_no_longer_navigates_to_standalone_today_ui():
    html = INDEX.read_text(encoding="utf-8")
    nav_marker = 'data-tab="my-day"'
    start = html.index(nav_marker)
    nav = html[start:html.index("</a>", start)]
    assert "/app/training/today-ui" not in nav
