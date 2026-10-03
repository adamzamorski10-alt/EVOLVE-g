from pathlib import Path


ROOT = Path(__file__).parent
APP_INIT = (ROOT / "app" / "__init__.py").read_text(encoding="utf-8")


def test_hosted_frontend_uses_same_origin_backend_on_render():
    assert 'fetch("/app/training/today"' in APP_INIT


def test_dashboard_first_targets_actual_legacy_shell_ids():
    assert 'id="evolve-dashboard-first-style"' in APP_INIT
    assert "#landing { display: none !important; }" in APP_INIT
    assert "#appContainer { display: flex !important; }" in APP_INIT
    assert "document.documentElement.classList.add('evolve-dashboard-first')" in APP_INIT
    assert 'id="evolve-dashboard-first-boot"' in APP_INIT
    assert "var landing = document.getElementById('landing');" in APP_INIT
    assert "var dashboard = document.getElementById('appContainer');" in APP_INIT
    assert "landing.style.display = 'none';" in APP_INIT
    assert "landing.setAttribute('aria-hidden', 'true');" in APP_INIT
    assert "dashboard.style.display = 'flex';" in APP_INIT
    assert "if (typeof initApp === 'function') initApp();" in APP_INIT
    assert "dashboard visibility must not depend on it" in APP_INIT


def test_shared_shell_contains_native_my_day_injection():
    required = [
        'id="evolve-my-day-shell-integration"',
        'id="tab-my-day"',
        'data-tab="my-day"',
        "showTab(\\'my-day\\')",
        "fetch(\"/app/training/today\"",
        "function injectMyDayShell",
        "window.loadEvolveMyDay",
        'id="myDayWorkout"',
        'id="myDayExercises"',
        'id="myDaySessionProgress"',
        "Wznów trening",
    ]
    for marker in required:
        assert marker in APP_INIT, f"Missing Mój dzień shell marker: {marker}"


def test_my_day_removes_standalone_today_dependency_from_navigation():
    assert "id=\"nav-my-day\"" in APP_INIT
    assert "/app/training/today-ui" not in APP_INIT


def test_my_day_empty_state_disables_training_start_cta():
    assert "var canStartTraining = Boolean(data.can_start || session.id);" in APP_INIT
    assert 'startLink.removeAttribute("href");' in APP_INIT
    assert 'startLink.setAttribute("aria-disabled", "true");' in APP_INIT
    assert 'startLink.classList.add("btn-ghost");' in APP_INIT


def test_frontend_has_fallback_when_generated_index_is_empty():
    assert 'if not html.strip():' in APP_INIT
    assert 'STATIC_DIR / "fitai_dashboard.html"' in APP_INIT
