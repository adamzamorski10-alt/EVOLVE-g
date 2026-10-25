from pathlib import Path


ROOT = Path(__file__).parent
APP_INIT = (ROOT / "app" / "__init__.py").read_text(encoding="utf-8")


def test_hosted_frontend_uses_same_origin_backend_on_render():
    assert 'fetch("/app/today"' in APP_INIT


def test_legacy_stats_error_handler_is_defined_before_stats_bootstrap():
    assert "window.apiErrorToast = window.apiErrorToast || function" in APP_INIT


def test_spa_routes_accept_head_requests_for_hosting_probes():
    assert '@app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)' in APP_INIT
    assert '@app.api_route("/{path:path}", methods=["GET", "HEAD"], include_in_schema=False)' in APP_INIT


def test_dashboard_first_targets_actual_legacy_shell_ids():
    assert 'id="evolve-dashboard-first-style"' in APP_INIT
    assert "#landingPage { display: none !important; }" in APP_INIT
    assert "#dashboardPage { display: flex !important; }" in APP_INIT
    assert "document.documentElement.classList.toggle('evolve-dashboard-first', authenticated);" in APP_INIT
    assert 'id="evolve-dashboard-first-boot"' in APP_INIT
    assert "var landing = document.getElementById('landingPage');" in APP_INIT
    assert "var dashboard = document.getElementById('dashboardPage');" in APP_INIT
    assert "landing.style.display = 'none';" in APP_INIT
    assert "landing.setAttribute('aria-hidden', 'true');" in APP_INIT
    assert "dashboard.style.display = 'flex';" in APP_INIT


def test_dashboard_boot_does_not_bypass_authentication():
    assert "var hasToken = Boolean(localStorage.getItem('fitai_token'));" in APP_INIT
    assert "fetch('/app/profile'" in APP_INIT
    assert "if (response.status === 401 || response.status === 403)" in APP_INIT
    assert "if (typeof initApp === 'function') initApp();" in APP_INIT


def test_shared_shell_contains_native_my_day_injection():
    required = [
        'id="evolve-my-day-shell-integration"',
        'id="tab-my-day"',
        'data-tab="my-day"',
        "showTab(\\\\'my-day\\\\')",
        "fetch(\"/app/today\"",
        "function injectMyDayShell",
        "window.loadEvolveMyDay",
        'id="myDayWorkout"',
        'id="myDayExercises"',
        'id="myDaySessionProgress"',
        "Wznów trening",
    ]
    for marker in required:
        assert marker in APP_INIT, f"Missing Mój dzień shell marker: {marker}"


def test_my_day_loader_supports_legacy_shell_identifiers():
    required = [
        'var get = function (primary, fallback)',
        'get("myDayWorkout", "myDayTrainingTitle")',
        'get("myDayPlanMeta", "myDayTrainingMeta")',
        'get("myDayStartLink", "myDayStart")',
        'get("myDaySessionBar", "myDaySessionProgressBar")',
    ]
    for marker in required:
        assert marker in APP_INIT, f"Missing legacy Today Hub compatibility marker: {marker}"


def test_my_day_removes_standalone_today_dependency_from_navigation():
    assert "id=\"nav-my-day\"" in APP_INIT
    assert "/app/training/today-ui" not in APP_INIT


def test_my_day_empty_state_disables_training_start_cta():
    assert "var canStartTraining = Boolean((data.primary_action || {}).can_start || session.id);" in APP_INIT
    assert 'startLink.removeAttribute("href");' in APP_INIT
    assert 'startLink.setAttribute("aria-disabled", "true");' in APP_INIT
    assert 'startLink.classList.add("btn-ghost");' in APP_INIT


def test_frontend_has_fallback_when_generated_index_is_empty():
    assert 'if not html.strip():' in APP_INIT
    assert 'STATIC_DIR / "fitai_dashboard.html"' in APP_INIT


def test_service_worker_does_not_cache_same_origin_api_responses_as_shell_assets():
    sw = (ROOT / "sw.js").read_text(encoding="utf-8")

    assert "const CACHE_VERSION = 'fitai-v3.3.2';" in sw
    assert "const isSameOriginApi = url.origin === self.location.origin" in sw
    assert "request.mode !== 'navigate'" in sw
    assert "(path.startsWith('/app/') || path.startsWith('/auth/'))" in sw
    assert "const isApi = isLocalApi || isProductionApi || isSameOriginApi;" in sw


def test_shared_shell_contains_native_recovery_integration():
    required = [
        'id="evolve-recovery-shell-integration"',
        'id="tab-recovery"',
        'id="nav-recovery"',
        'fetch("/app/recovery/today"',
        "window.loadEvolveRecovery",
        'id="recoverySummary"',
        'id="recoverySignals"',
        'id="recoveryEffect"',
    ]
    for marker in required:
        assert marker in APP_INIT, f"Missing Recovery shell marker: {marker}"


def test_progress_shell_exposes_explainable_adaptation():
    required = [
        'id="progressAdaptation"',
        'fetch("/app/training/adaptive/next-effective-preview"',
        "window.applyEvolveAdaptation",
        'fetch("/app/training/adaptive/apply"',
        "Zastosuj zmianę",
    ]
    for marker in required:
        assert marker in APP_INIT, f"Missing Progress & Lab adaptation marker: {marker}"
    assert 'document.querySelector(".content") || document.getElementById("mainContent")' in APP_INIT
    assert 'tab === "progress"' in APP_INIT
    assert 'tab === "postepy"' in APP_INIT


def test_injected_shell_escapes_quotes_inside_javascript_html_strings():
    assert 'font-family:\\\\\'Syne\\\\\',sans-serif;font-size:26px;font-weight:700;">Koszykówka' in APP_INIT
    for category in ("all", "rzuty", "drybling", "obrona", "kondycja"):
        assert f'renderBasketballCatalog(\\\\\'{category}\\\\\')' in APP_INIT


def test_frontend_script_injection_ignores_body_markup_inside_inline_javascript():
    import ast
    import re

    tree = ast.parse(APP_INIT)
    helper = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_insert_before_document_body_end"
    )
    module = ast.Module(body=[helper], type_ignores=[])
    namespace = {"re": re}
    exec(compile(module, "<frontend-injection-helper>", "exec"), namespace)

    html = (
        "<!doctype html><html><head></head><body>"
        "<script>const print = `</body></html>`;</script>"
        "<main>EVOLVE app</main></body></html>"
    )
    injected = namespace["_insert_before_document_body_end"](
        html, '<script id="evolve-test-injection"></script>'
    )

    injection_pos = injected.index('id="evolve-test-injection"')
    assert injection_pos > injected.index("<main>EVOLVE app</main>")
    assert injection_pos < injected.rindex("</body>")
    assert injected.count('id="evolve-test-injection"') == 1


def test_shared_shell_contains_native_basketball_integration():
    required = [
        'id="tab-basketball"',
        'id="nav-basketball"',
        'window.loadEvolveBasketball',
        'fetch("/app/drill-history',
        'fetch("/app/drill-result',
        'id="basketballSummary"',
        'id="basketballDrillsCatalog"',
        'openEvolveBasketballForm',
    ]
    for marker in required:
        assert marker in APP_INIT, f"Missing Basketball shell marker: {marker}"
