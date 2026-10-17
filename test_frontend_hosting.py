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

def test_dashboard_plan_refresh_has_a_matching_try_block():
    dashboard = (ROOT / "fitai_dashboard.html").read_text(encoding="utf-8")
    lines = dashboard.splitlines()
    fetch_index = next(i for i, line in enumerate(lines) if "const plResp = await fetch('/app/plan/current'" in line)
    assert lines[fetch_index - 1].strip() == "try {"
    assert "}catch (e) { console.warn('fetch plan failed', e); }" in dashboard

def test_dashboard_inline_javascript_parses_when_node_is_available(tmp_path):
    import re
    import shutil
    import subprocess

    node = shutil.which("node")
    if not node:
        import pytest
        pytest.skip("Node.js is not installed")

    dashboard = (ROOT / "fitai_dashboard.html").read_text(encoding="utf-8")
    scripts = re.findall(r"<script(?:\s[^>]*)?>([\s\S]*?)</script>", dashboard, re.IGNORECASE)
    inline_script = max(scripts, key=len)
    script_path = tmp_path / "dashboard-inline.js"
    script_path.write_text(inline_script, encoding="utf-8")
    result = subprocess.run([node, "--check", str(script_path)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_injected_shell_javascript_parses_when_node_is_available(tmp_path):
    import ast
    import re
    import shutil
    import subprocess

    node = shutil.which("node")
    if not node:
        import pytest
        pytest.skip("Node.js is not installed")

    module = ast.parse(APP_INIT)
    shell_value = next(
        ast.literal_eval(node.value)
        for node in ast.walk(module)
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "evolve_shell_integration" for target in node.targets)
    )
    match = re.search(r"<script(?:\s[^>]*)?>([\s\S]*?)</script>", shell_value, re.IGNORECASE)
    assert match, "Injected shell script tag is missing"
    script_path = tmp_path / "injected-shell.js"
    script_path.write_text(match.group(1), encoding="utf-8")
    result = subprocess.run([node, "--check", str(script_path)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
