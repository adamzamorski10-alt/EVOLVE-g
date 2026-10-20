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
    assert "if (typeof enterApp === 'function') enterApp();" in APP_INIT


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


def test_frontend_has_fallback_when_generated_index_is_empty():
    assert 'if not html.strip():' in APP_INIT
    assert 'STATIC_DIR / "fitai_dashboard.html"' in APP_INIT



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
