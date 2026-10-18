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
        "showTab(",
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


def test_injected_navigation_uses_safe_event_listeners():
    navigation_lines = [line for line in APP_INIT.splitlines() if 'nav-' in line and 'data-tab=' in line]
    assert len(navigation_lines) == 6
    assert all('onclick=' not in line for line in navigation_lines)
    assert 'button.addEventListener("click"' in APP_INIT
    assert 'String.fromCharCode(34)' in APP_INIT


def test_injected_navigation_clicks_route_to_the_selected_tab_when_node_is_available(tmp_path):
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

    harness = r'''
const calls = [];
const buttons = {};
const expected = ["my-day", "training", "basketball", "diet", "recovery", "progress"];
function makeButton(id) {
  return {
    handlers: {},
    addEventListener(name, callback) { this.handlers[name] = callback; },
    getAttribute(name) { return name === "data-tab" ? id.replace("nav-", "") : null; },
    click() { if (this.handlers.click) this.handlers.click(); }
  };
}
const profile = {
  insertAdjacentHTML() {
    for (const id of ["nav-my-day", "nav-training", "nav-basketball", "nav-diet", "nav-recovery", "nav-progress"]) {
      buttons[id] = makeButton(id);
    }
  }
};
const content = { insertAdjacentHTML() {} };
const document = {
  ready: null,
  addEventListener(name, callback) { if (name === "DOMContentLoaded") this.ready = callback; },
  querySelector(selector) { return selector === ".sidebar" ? {} : selector === ".content" ? content : null; },
  getElementById(id) {
    if (id === "nav-profile") return profile;
    if (id === "tab-my-day" || id === "nav-myday" || id === "nav-plan" || id === "tab-myday") return null;
    return buttons[id] || null;
  }
};
const window = { location: { hash: "" }, addEventListener() {} };
function showTab(tab) { calls.push(tab); }
'''
    script_path = tmp_path / "navigation-runtime.js"
    script_path.write_text(harness + "\n" + match.group(1) + "\n" + r'''
if (!document.ready) throw new Error("DOMContentLoaded handler was not registered");
document.ready();
for (const id of ["nav-my-day", "nav-training", "nav-basketball", "nav-diet", "nav-recovery", "nav-progress"]) {
  if (!buttons[id] || typeof buttons[id].handlers.click !== "function") throw new Error("Missing click handler: " + id);
  buttons[id].click();
}
if (JSON.stringify(calls) !== JSON.stringify(expected)) throw new Error("Unexpected tabs: " + JSON.stringify(calls));
''', encoding="utf-8")
    result = subprocess.run([node, str(script_path)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
