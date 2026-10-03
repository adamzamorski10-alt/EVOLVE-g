from __future__ import annotations

import ast
from pathlib import Path

from fastapi.testclient import TestClient

from main import app


ROOT = Path(__file__).parent
client = TestClient(app)


def _route_paths() -> set[str]:
    return {
        route.path
        for route in app.routes
        if getattr(route, "path", None)
    }


def test_stage_0_5_core_routes_are_registered():
    paths = _route_paths()
    required = {
        "/auth/register",
        "/auth/login",
        "/app/profile",
        "/app/assessment",
        "/app/assessment/latest",
        "/app/assessment/history",
        "/app/plan/readiness",
        "/app/plan/generate",
        "/app/plan/current",
        "/app/plan/swap",
        "/app/training/today",
        "/app/training/sessions/start",
        "/app/training/sessions/{session_id}/sets",
        "/app/training/sessions/{session_id}/complete",
        "/app/training/progress",
        "/app/training/progress/exercises/{exercise_key}",
        "/app/training/progress/trends",
        "/app/training/progress/records",
        "/app/training/progress/consistency",
        "/app/training/sessions/history",
        "/app/training/sessions/history/{session_id}",
        "/app/training/sessions/{session_id}",
        "/app/training/sessions/{session_id}/analysis",
        "/app/training/sessions/{session_id}/progression",
        "/app/training/sessions/{session_id}/next-plan-preview",
        "/app/training/adaptive/preview",
        "/app/training/adaptive/plan-current",
        "/app/training/adaptive/apply",
        "/app/training/adaptive/history",
        "/app/training/adaptive/plan-preview",
        "/app/training/exercises/{exercise_key}/history",
        "/app/goals",
        "/app/goals/{goal_id}",
        "/app/goals/{goal_id}/progress",
        "/app/goals/metrics",
        "/app/nutrition/entries",
        "/app/nutrition/today",
        "/app/nutrition/adherence",
        "/app/nutrition/response",
        "/app/nutrition/adaptation",
        "/app/nutrition/adaptation/apply",
    }
    missing = sorted(required - paths)
    assert not missing, f"Missing registered Stage 0-5 routes: {missing}"


def test_main_shell_exposes_native_stage_0_5_domains():
    response = client.get("/app")
    assert response.status_code == 200
    html = response.text
    required = [
        'data-tab="my-day"',
        'data-tab="training"',
        'data-tab="basketball"',
        'data-tab="diet"',
        'data-tab="recovery"',
        'data-tab="progress"',
        'data-tab="goals"',
        'data-tab="profile"',
        'id="tab-my-day"',
        'id="tab-progress"',
        'id="tab-goals"',
        'id="tab-diet"',
    ]
    missing = [marker for marker in required if marker not in html]
    assert not missing, f"Missing native shell markers: {missing}"


def test_migration_chain_has_single_head_through_stage_5():
    versions = ROOT / "alembic" / "versions"
    revisions: dict[str, object] = {}
    for path in versions.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        revision = None
        down_revision = None
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "revision":
                        if isinstance(node.value, ast.Constant):
                            revision = node.value.value
                    if isinstance(target, ast.Name) and target.id == "down_revision":
                        if isinstance(node.value, ast.Constant):
                            down_revision = node.value.value
                        elif isinstance(node.value, (ast.Tuple, ast.List)):
                            down_revision = tuple(
                                item.value for item in node.value.elts
                                if isinstance(item, ast.Constant)
                            )
        if revision:
            revisions[revision] = down_revision

    assert "evolve19nutrition_adaptations" in revisions
    assert revisions.get("evolve20migration_merge") == ("evolve19nutrition_adaptations", "72efb594294f")
    assert revisions.get("7a6d4c3e9b12") == "c8b1f3d9a77d"
    assert revisions.get("evolve20migration_merge") == ("evolve19nutrition_adaptations", "72efb594294f")
    expected = {
        "evolve16goals": "evolve15adaptiveunique",
        "evolve17goalmetrics": "evolve16goals",
        "evolve18nutrition": "evolve17goalmetrics",
        "evolve19nutrition_adaptations": "evolve18nutrition",
    }
    for revision, parent in expected.items():
        assert revisions.get(revision) == parent

    expected_legacy = {
        "9d8e7f6a5b43": "c8b1f3d9a77d",
        "a1b2c3d4e5f6": "9d8e7f6a5b43",
        "72efb594294f": "a1b2c3d4e5f6",
    }
    for revision, parent in expected_legacy.items():
        assert revisions.get(revision) == parent

    children = set()
    for parent in revisions.values():
        if isinstance(parent, tuple):
            children.update(parent)
        elif parent:
            children.add(parent)
    heads = sorted(revision for revision in revisions if revision not in children)
    assert heads == ["evolve20migration_merge"], heads


def test_external_verification_queue_keeps_stage_0_5_checks_pending():
    queue = (ROOT / "docs" / "EXTERNAL_VERIFICATION.md").read_text(encoding="utf-8")
    for item in ("EV-001", "EV-008", "EV-009", "EV-013", "EV-017", "EV-018"):
        start = queue.find(f"### {item}")
        assert start >= 0, f"Missing verification item {item}"
        block = queue[start:queue.find("\n### ", start + 5) if queue.find("\n### ", start + 5) >= 0 else None]
        assert "Status: PENDING" in block or "- Status: PENDING" in block


def test_no_duplicate_http_method_and_path_routes_are_registered():
    seen: set[tuple[str, str]] = set()
    duplicates: list[tuple[str, str]] = []
    for route in app.routes:
        path = getattr(route, "path", None)
        methods = getattr(route, "methods", set()) or set()
        for method in methods:
            key = (method, path)
            if key in seen:
                duplicates.append(key)
            seen.add(key)
    assert not duplicates, f"Duplicate FastAPI routes registered: {duplicates}"


def test_stage_0_5_api_routes_are_authenticated():
    public_ui = {
        "/app",
        "/app/version",
        "/app/assessment/ui",
        "/app/plan/ui",
        "/app/training/today-ui",
        "/app/training/session-ui",
        "/app/training/dashboard",
    }

    def dependency_names(dependant):
        names = set()
        for dependency in getattr(dependant, "dependencies", []):
            call = getattr(dependency, "call", None)
            if call is not None:
                names.add(getattr(call, "__name__", ""))
            names.update(dependency_names(dependency))
        return names

    missing_auth = []
    for route in app.routes:
        path = getattr(route, "path", "")
        if not path.startswith("/app/") or path in public_ui:
            continue
        if "get_current_user" not in dependency_names(getattr(route, "dependant", None)):
            missing_auth.append(path)
    assert not missing_auth, f"App API routes without get_current_user dependency: {sorted(set(missing_auth))}"


def test_audit_file_is_syntactically_valid():
    import ast
    ast.parse(Path(__file__).read_text(encoding="utf-8"))


def test_all_app_and_migration_python_files_parse():
    import ast
    roots = [ROOT / "app", ROOT / "alembic"]
    failures = []
    for base in roots:
        for path in base.rglob("*.py"):
            try:
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except SyntaxError as exc:
                failures.append(f"{path}: {exc}")
    assert not failures, "\n".join(failures)
