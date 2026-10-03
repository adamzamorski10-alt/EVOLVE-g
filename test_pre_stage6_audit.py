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
        "/app/plan/readiness",
        "/app/plan/generate",
        "/app/training/today",
        "/app/training/sessions/start",
        "/app/training/sessions/{session_id}/sets",
        "/app/training/sessions/{session_id}/complete",
        "/app/training/progress",
        "/app/training/progress/exercises/{exercise_key}",
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
    revisions: dict[str, str | None] = {}
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
        if revision:
            revisions[revision] = down_revision

    assert "evolve19nutrition_adaptations" in revisions
    expected = {
        "evolve16goals": "evolve15adaptiveunique",
        "evolve17goalmetrics": "evolve16goals",
        "evolve18nutrition": "evolve17goalmetrics",
        "evolve19nutrition_adaptations": "evolve18nutrition",
    }
    for revision, parent in expected.items():
        assert revisions.get(revision) == parent

    children = {parent for parent in revisions.values() if parent}
    heads = sorted(revision for revision in revisions if revision not in children)
    assert heads == ["evolve19nutrition_adaptations"], heads


def test_external_verification_queue_keeps_stage_0_5_checks_pending():
    queue = (ROOT / "docs" / "EXTERNAL_VERIFICATION.md").read_text(encoding="utf-8")
    for item in ("EV-001", "EV-008", "EV-009", "EV-013", "EV-017"):
        start = queue.find(f"### {item}")
        assert start >= 0, f"Missing verification item {item}"
        block = queue[start:queue.find("\n### ", start + 5) if queue.find("\n### ", start + 5) >= 0 else None]
        assert "Status: PENDING" in block or "- Status: PENDING" in block
