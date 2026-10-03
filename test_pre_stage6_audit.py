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


def test_stage_0_5_core_router_contracts_are_registered():
    app_init = (ROOT / "app" / "__init__.py").read_text(encoding="utf-8")
    expected_routers = {
        "auth_router": "/auth",
        "assessment_router": "/app/assessment",
        "goals_router": "/app/goals",
        "nutrition_router": "/app/nutrition",
        "plan_router": "/app/plan",
        "training_router": "/app/training",
        "fitness_router": "/app",
    }
    for router_name, prefix in expected_routers.items():
        assert f"app.include_router({router_name})" in app_init
        if router_name == "auth_router":
            module = __import__("app.auth.routes", fromlist=["router"])
        elif router_name == "assessment_router":
            module = __import__("app.assessment.routes", fromlist=["router"])
        elif router_name == "goals_router":
            module = __import__("app.goals.routes", fromlist=["router"])
        elif router_name == "nutrition_router":
            module = __import__("app.nutrition.routes", fromlist=["router"])
        elif router_name == "plan_router":
            module = __import__("app.plan.routes", fromlist=["router"])
        elif router_name == "training_router":
            module = __import__("app.training.routes", fromlist=["router"])
        else:
            module = __import__("app.fitness.routes", fromlist=["router"])
        assert module.router.prefix == prefix
        assert module.router.routes, f"Router has no routes: {router_name}"

def test_main_shell_exposes_native_stage_0_5_domains():
    source = (ROOT / "app" / "__init__.py").read_text(encoding="utf-8")
    required = [
        'id="evolve-my-day-shell-integration"',
        'data-tab="my-day"',
        'data-tab="training"',
        'data-tab="basketball"',
        'data-tab="diet"',
        'data-tab="recovery"',
        'data-tab="progress"',
        'data-tab="goals"',
        'document.getElementById("nav-profile")',
        'id="tab-my-day"',
        'id="tab-progress"',
        'id="tab-goals"',
        'id="tab-diet"',
        'function injectProgressShell',
        'function injectGoalsShell',
        'window.showTab = wrappedShowTab',
    ]
    missing = [marker for marker in required if marker not in source]
    assert not missing, f"Missing native shell source markers: {missing}"

def test_migration_chain_has_single_head_through_stage_5():
    versions = ROOT / "alembic" / "versions"
    revisions: dict[str, object] = {}
    for path in versions.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        revision = None
        down_revision = None
        for node in tree.body:
            targets = []
            value = None
            if isinstance(node, ast.Assign):
                targets = node.targets
                value = node.value
            elif isinstance(node, ast.AnnAssign):
                targets = [node.target]
                value = node.value
            for target in targets:
                if isinstance(target, ast.Name) and target.id == "revision" and isinstance(value, ast.Constant):
                    revision = value.value
                if isinstance(target, ast.Name) and target.id == "down_revision":
                    if isinstance(value, ast.Constant):
                        down_revision = value.value
                    elif isinstance(value, (ast.Tuple, ast.List)):
                        down_revision = tuple(item.value for item in value.elts if isinstance(item, ast.Constant))
        if revision:
            revisions[revision] = down_revision

    assert "evolve19nutrition_adaptations" in revisions
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
    for item in ("EV-001", "EV-008", "EV-018", "EV-019"):
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


def test_stage_0_5_api_route_contracts_are_declared_and_auth_scoped():
    app_init = (ROOT / "app" / "__init__.py").read_text(encoding="utf-8")
    route_specs = [
        ("app.assessment.routes", "assessment_router", "/app/assessment"),
        ("app.goals.routes", "goals_router", "/app/goals"),
        ("app.nutrition.routes", "nutrition_router", "/app/nutrition"),
        ("app.plan.routes", "plan_router", "/app/plan"),
        ("app.training.routes", "training_router", "/app/training"),
        ("app.fitness.routes", "fitness_router", "/app"),
    ]
    for module_name, router_name, prefix in route_specs:
        assert f"app.include_router({router_name})" in app_init
        module = __import__(module_name, fromlist=["router"])
        router = module.router
        assert router.prefix == prefix
        for route in router.routes:
            path = getattr(route, "path", "")
            if not path.startswith(prefix):
                continue
            if path.endswith("/ui") or path.endswith("/today-ui") or path.endswith("/session-ui") or path.endswith("/dashboard"):
                continue
            dependency_names = set()
            for dependency in getattr(route, "dependant", None).dependencies if getattr(route, "dependant", None) else []:
                call = getattr(dependency, "call", None)
                if call is not None:
                    dependency_names.add(getattr(call, "__name__", ""))
            assert "get_current_user" in dependency_names, f"Missing auth dependency: {module_name} {path}"

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
