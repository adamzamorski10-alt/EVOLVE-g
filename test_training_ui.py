from pathlib import Path


ROOT = Path(__file__).parent
INDEX = ROOT / "fitai_dashboard.html"
APP_INIT = (ROOT / "app" / "__init__.py").read_text(encoding="utf-8")


def test_training_execution_ui_is_wired_to_stage2_api():
    html = INDEX.read_text(encoding="utf-8")
    required = [
        "evolveStartTrainingBtn",
        "window.evolveStartTraining",
        "/app/training/sessions/start",
        "/app/training/sessions/",
        "encodeURIComponent(session.id)",
        "/sets",
        "/complete",
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
    required = [
        'id="tab-my-day"',
        'data-tab="my-day"',
        "showTab(\\'my-day\\')",
        "window.loadEvolveMyDay",
        'fetch("/app/training/today"',
        'id="myDayWorkout"',
        'id="myDayExercises"',
        'href="/app/training/session-ui"',
    ]
    for marker in required:
        assert marker in APP_INIT, f"Missing Mój dzień shell marker: {marker}"


def test_my_day_no_longer_navigates_to_standalone_today_ui():
    assert 'id="nav-my-day"' in APP_INIT
    assert "/app/training/today-ui" not in APP_INIT
