from pathlib import Path


ROOT = Path(__file__).parent
TRAINING_ROUTES = (ROOT / "app" / "training" / "routes.py").read_text(encoding="utf-8")
APP_INIT = (ROOT / "app" / "__init__.py").read_text(encoding="utf-8")
PLAN_ROUTES = (ROOT / "app" / "plan" / "routes.py").read_text(encoding="utf-8")


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
