import json
import re
import shutil
import socket
import subprocess
import tempfile
import threading
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from main import app

ROOT = Path(__file__).parent
TRAINING_ROUTES = (ROOT / "app" / "training" / "routes.py").read_text(encoding="utf-8")
APP_INIT = (ROOT / "app" / "__init__.py").read_text(encoding="utf-8")
PLAN_ROUTES = (ROOT / "app" / "plan" / "routes.py").read_text(encoding="utf-8")

_UI_CLIENT = TestClient(app)


def _rendered_inline_scripts(path: str) -> list[str]:
    html = _UI_CLIENT.get(path).text
    return [block for block in re.findall(r"<script[^>]*>(.*?)</script>", html, re.S) if block.strip()]



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
        "showTab(\\\\'my-day\\\\')",
        "window.loadEvolveMyDay",
        'fetch("/app/today"',
        'id="myDayWorkout"',
        'id="myDayExercises"',
        'id="myDaySessionProgress"',
        'href="/app/training/session-ui"',
        'href="/app/plan/ui',
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


def test_training_progress_2abc_contracts_are_present():
    required = [
        '@router.get("/progress/exercises/{exercise_key}")',
        '@router.get("/progress/trends")',
        '@router.get("/progress/records")',
        '"best_weight"',
        '"best_reps"',
        '"best_session_volume"',
        '"weight": {"trend"',
        '"volume": {"trend"',
        '"rpe": {"trend"',
    ]
    for marker in required:
        assert marker in TRAINING_ROUTES, f"Missing Progress 2A/2B/2C marker: {marker}"


def test_progress_2def_native_shell_contract():
    required = [
        'id="nav-progress"',
        'id="tab-progress"',
        'id="progressSummary"',
        'id="progressTrends"',
        'id="progressRecords"',
        'id="progressExercises"',
        'id="progressConsistency"',
        'id="progressHistory"',
        'loadEvolveProgress',
        'loadEvolveProgressExercise',
        'loadEvolveSessionDetail',
        'progressSparkline',
        '/app/training/progress/consistency?limit=52',
        '/app/training/sessions/history?limit=12',
        '/app/training/sessions/history/"',
        'else if (tab === "progress")',
    ]
    for marker in required:
        assert marker in APP_INIT or marker in TRAINING_ROUTES, f"Missing Progress 2D/2E/2F marker: {marker}"



def test_goals_ux_native_shell_contract():
    required = [
        'id="nav-goals"',
        'id="tab-goals"',
        'id="goalsSummary"',
        'id="goalsList"',
        'id="goalForm"',
        'id="goalDetail"',
        'loadEvolveGoals',
        'openEvolveGoalForm',
        'saveEvolveGoal',
        'editEvolveGoal',
        'loadEvolveGoalDetail',
        'updateEvolveGoalStatus',
        'archiveEvolveGoal',
        '/app/goals',
        '/app/goals/"',
        '/progress',
        'else if (tab === "goals")',
        'injectGoalsShell();',
    ]
    for marker in required:
        assert marker in APP_INIT, f"Missing Goals UX marker: {marker}"


def test_goals_ux_has_empty_error_and_lifecycle_states():
    required = [
        'Brak celów. Utwórz pierwszy cel, aby rozpocząć.',
        'Nie udało się załadować celów.',
        'Zarchiwizować ten cel?',
        'Ukończ',
        'Archiwizuj',
        'ARCHIWUM',
    ]
    for marker in required:
        assert marker in APP_INIT, f"Missing Goals UX state marker: {marker}"


def test_training_4abc_execution_ui_contract():
    required = [
        '@router.get("/session-ui"',
        'START -> EXECUTE -> SAVE SET -> COMPLETE',
        'Aktywna sesja',
        'Wykonanie',
        'Zapisz serię',
        'Edytuj / zapisz',
        'actual_reps',
        'actual_weight_kg',
        'actual_rpe',
        'note',
        '/app/training/sessions/start',
        '/app/training/sessions/',
        '/sets',
        '/complete',
        'Wznowiono aktywną sesję.',
        'Możesz odświeżyć stronę i wznowić.',
    ]
    for marker in required:
        assert marker in TRAINING_ROUTES, f"Missing Training UX 4A/4B/4C marker: {marker}"


def test_training_4def_rest_flow_and_completion_summary_contract():
    source = (Path(__file__).parent / "app" / "training" / "routes.py").read_text(encoding="utf-8")
    assert "startRest(90)" in source
    assert "skipRest" in source
    assert "focusNext()" in source
    assert "renderSummary()" in source
    assert "Końcowe RPE" in source
    assert "Przejdź do Postępów" in source
    assert "current.status==='completed'" in source


def test_today_ui_uses_semantic_action_contract():
    assert 'fetch("/app/today"' in APP_INIT
    assert 'id="myDayActionTitle"' in APP_INIT
    assert 'id="myDayActionText"' in APP_INIT
    assert 'id="myDayActionWhy"' in APP_INIT
    assert 'data.primary_action' in APP_INIT
    assert 'data.workout' in APP_INIT



def test_rolling_plan_ui_uses_dated_api_and_canonical_execution():
    required = [
        '@router.get("/rolling"',
        '"/app/plan/rolling?horizon_days=14"',
        'id="rollingHorizon"',
        'plannedDays=data.planned_days||upcoming',
        'item.scheduled_date',
        'item.status==="rest"',
        'item.status==="completed"',
        'list_completed_training_history',
        'href="/app/training/session-ui"',
    ]
    for marker in required:
        assert marker in PLAN_ROUTES, f"Missing rolling-plan UX marker: {marker}"

def test_plan_ui_exposes_weekly_availability_editor():
    required = [
        'id="availabilityDays"',
        'id="saveAvailability"',
        'id="availabilityStatus"',
        '"/app/plan/availability"',
        'name="availabilityDay"',
        'name="availabilityStart"',
        'name="availabilityEnd"',
        'id="sessionDuration"',
        'id="sportFocus"',
        'id="sportSpecialization"',
        'id="sportScheduleDays"',
        'id="saveSportSchedule"',
        'name="sportStart"',
        'name="sportEnd"',
        '"/app/sport-config"',
        'data.sport_training_schedule?.windows',
        "esc(w.start||'')",
        "esc(w.end||'')",
        "Godzina: ",
        "schedule_diagnostics",
        "uwaga: plan nie spełnia pełnego celu tygodniowego",
        "Dlaczego plan ma mniej treningów?",
        "brak dostępności",
        "za krótkie okno czasowe",
        "nieprawidłowe ustawienia harmonogramu",
        "session_duration_minutes:Number",
        "Uzupełnij obie godziny albo pozostaw oba pola puste:",
        "Zapisz dostępność",
        "Nie ustawiono ograniczeń — wszystkie dni są dostępne.",
        "Zaznacz co najmniej jeden dzień.",
    ]
    for marker in required:
        assert marker in PLAN_ROUTES, f"Missing weekly availability UI marker: {marker}"


def test_session_ui_rendered_script_has_no_escaped_quote_corruption():
    scripts = _rendered_inline_scripts("/app/training/session-ui")
    assert scripts, "session-ui must render an inline script"
    joined = "\n".join(scripts)
    # Regression guard for the original defect: the Python template must not
    # consume the backslash escapes the browser needs, which corrupted every
    # string in the page and blocked load() at parse time.
    assert "logSet(''" not in joined
    assert 'onclick="logSet(' not in joined


HOSTILE_EXERCISE_KEYS = [
    "bench_press",
    "bench's press",
    'a"b<c>&d',
    "100% ciezaru",
    "back\\slash",
    "klucz&#39;zewnetrzny&quot;",
    "klucz ze spacja",
    "przysiad-ünïcode-ü",
    "",
]


def _session_payload_with_exercise_key(exercise_key: str) -> dict:
    """Shape returned by POST /app/training/sessions/start."""
    return {
        "status": "started",
        "session": {
            "id": "11111111-2222-3333-4444-555555555555",
            "session_date": "2026-10-11",
            "status": "active",
            "execution_blocked": False,
            "planned": {
                "exercises": [
                    {
                        "exercise_key": exercise_key,
                        "exercise_name": "Wrogie ćwiczenie",
                        "sets": 2,
                        "reps": 10,
                        "reps_label": "10",
                        "weight_kg": 50,
                        "rpe": 8,
                    }
                ]
            },
            "sets": [],
        },
    }


def _browser_module():
    """Return playwright.sync_api or skip when the browser tooling is absent."""
    pytest.importorskip("playwright", reason="playwright is not installed")
    from playwright import sync_api

    return sync_api


@pytest.fixture(scope="session")
def live_session_ui_server():
    import uvicorn

    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]

    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    try:
        for _ in range(200):
            if server.started:
                break
            time.sleep(0.05)
        else:  # pragma: no cover - startup failure
            pytest.skip("live server did not start")
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        thread.join(timeout=10)


@pytest.fixture(scope="session")
def playwright_browser():
    sync_api = _browser_module()
    handle = sync_api.sync_playwright().start()
    try:
        try:
            browser = handle.chromium.launch()
        except Exception as error:  # pragma: no cover - browser not provisioned
            pytest.skip(f"chromium could not be launched: {error}")
        if not browser:  # pragma: no cover - defensive
            pytest.skip("chromium could not be launched")
        yield browser
        browser.close()
    finally:
        handle.stop()


@pytest.fixture
def rendered_session_page(playwright_browser):
    context = playwright_browser.new_context()
    page = context.new_page()
    try:
        yield page
    finally:
        context.close()


@pytest.mark.parametrize("exercise_key", HOSTILE_EXERCISE_KEYS)
def test_session_ui_data_key_escapes_hostile_exercise_key_in_real_browser(
    exercise_key, live_session_ui_server, rendered_session_page
):
    """The save button must keep a hostile key as one attribute value.

    The application renders this markup client-side, so the only faithful check
    is to drive the shipped page in a real browser and inspect the resulting DOM.
    Deliberately no Python copy of esc() is used and no source text is pinned,
    so refactoring the template cannot break or fake this test.
    """
    sync_api = _browser_module()
    page = rendered_session_page
    page.add_init_script("localStorage.setItem('fitai_token','browser-test-token')")
    stubbed_body = json.dumps(_session_payload_with_exercise_key(exercise_key))
    page.route(
        "**/app/training/sessions/start",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=stubbed_body,
        ),
    )

    page.goto(f"{live_session_ui_server}/app/training/session-ui", wait_until="load")
    page.wait_for_selector("button.save", timeout=10000)

    button = page.locator("button.save").first
    attribute_names = button.evaluate("el => [...el.attributes].map(a => a.name)")
    attribute_names.sort()

    # A hostile key must not create extra attributes on the button.
    assert attribute_names == ["class", "data-key", "data-set"], (
        f"hostile key {exercise_key!r} produced attributes {attribute_names}"
    )
    # The decoded attribute value must be exactly the key the API returned.
    assert button.evaluate("el => el.dataset.key") == exercise_key
    # The key must reach the input ids the save flow reads from.
    expected_input_id = "r-" + _js_encode_uri_component(exercise_key) + "-1"
    assert page.evaluate(
        "id => document.getElementById(id) !== null", expected_input_id
    ), f"save-flow input for {exercise_key!r} was not rendered"
    # No stray elements may be created by unescaped angle brackets.
    assert page.locator(".exercise").count() == 1
    assert page.locator(".set").count() == 2


def _js_encode_uri_component(value: str) -> str:
    """Percent-encoding identical to JavaScript encodeURIComponent."""

    class _Raw(str):
        pass

    import urllib.parse

    return urllib.parse.quote(value, safe="-_.!~*'()")


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable in this test environment")
def test_rendered_ui_scripts_parse_with_node():
    for path in ("/app/training/session-ui", "/app/training/today-ui", "/app/training/dashboard"):
        for block in _rendered_inline_scripts(path):
            with tempfile.TemporaryDirectory() as workspace:
                target = Path(workspace) / "rendered.js"
                target.write_text(block, encoding="utf-8", newline="")
                result = subprocess.run(
                    ["node", "--check", str(target)], capture_output=True, text=True
                )
                assert result.returncode == 0, f"{path} rendered invalid JavaScript: {result.stderr}"
