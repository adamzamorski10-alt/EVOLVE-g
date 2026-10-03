from pathlib import Path


ROOT = Path(__file__).parent
TRAINING_ROUTES = (ROOT / "app" / "training" / "routes.py").read_text(encoding="utf-8")
APP_INIT = (ROOT / "app" / "__init__.py").read_text(encoding="utf-8")


def test_training_execution_api_contract_is_present():
    required = [
        '@router.post("/sessions/start")',
        '@router.post("/sessions/{session_id}/sets")',
        '@router.post("/sessions/{session_id}/complete")',
        "def start_training_session",
        "def log_training_set",
        "def complete_training_session",
    ]
    for marker in required:
        assert marker in TRAINING_ROUTES, f"Missing training execution marker: {marker}"


def test_my_day_is_integrated_into_shared_dashboard_shell():
    required = [
        'id="tab-my-day"',
        'data-tab="my-day"',
        "showTab(\\'my-day\\')",
        "window.loadEvolveMyDay",
        'fetch("/app/training/today"',
        'id="myDayWorkout"',
        'id="myDayExercises"',
        'id="myDaySessionProgress"',
        'href="/app/training/session-ui"',
        "Wznów trening",
    ]
    for marker in required:
        assert marker in APP_INIT, f"Missing Mój dzień shell marker: {marker}"


def test_my_day_no_longer_navigates_to_standalone_today_ui():
    assert 'id="nav-my-day"' in APP_INIT
    assert "/app/training/today-ui" not in APP_INIT


def test_my_day_routing_loads_daily_data_when_native_tab_opens():
    assert "function installMyDayRoutingHook()" in APP_INIT
    assert "var originalShowTab = window.showTab;" in APP_INIT
    assert 'if (tab === "my-day") {' in APP_INIT
    assert "window.loadEvolveMyDay();" in APP_INIT
    assert "installMyDayRoutingHook();" in APP_INIT


def test_my_day_shell_ignores_stale_daily_responses():
    assert "var myDayLoadSequence = 0;" in APP_INIT
    assert "var requestId = ++myDayLoadSequence;" in APP_INIT
    assert "if (requestId !== myDayLoadSequence) return;" in APP_INIT


def test_training_progress_endpoint_and_dashboard_contract():
    assert '@router.get("/progress")' in TRAINING_ROUTES
    assert "total_volume_kg" in TRAINING_ROUTES
    assert "total_completed_sets" in TRAINING_ROUTES
    assert "fetch('/app/training/progress?limit=12'" in TRAINING_ROUTES
