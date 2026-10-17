import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def _rendered_inline_scripts(path: str) -> list[str]:
    html = client.get(path).text
    return [block for block in re.findall(r"<script[^>]*>(.*?)</script>", html, re.S) if block.strip()]


def test_assessment_ui_history_join_uses_javascript_escape():
    scripts = _rendered_inline_scripts("/app/assessment/ui")
    assert scripts, "assessment ui must render an inline script"
    joined = "\n".join(scripts)
    # Regression guard: a raw newline inside a JavaScript string literal is a
    # browser SyntaxError (the original defect).
    assert 'join("\n")' not in joined
    # The browser must receive the JavaScript escape sequence.
    assert 'join("\\n")' in joined
    assert "loadAssessmentHistory" in joined


def _json_literal(data) -> str:
    import json

    return json.dumps(data, ensure_ascii=False)


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable in this test environment")
def test_rendered_assessment_ui_script_parses_and_renders_history_with_node():
    statements = [
        line.strip()
        for line in _rendered_inline_scripts("/app/assessment/ui")[0].split("\n")
        if ".join(" in line
    ]
    assert len(statements) == 1, statements
    statement = statements[0]

    payloads = [
        {
            "label": "populated",
            "data": {
                "count": 2,
                "assessments": [
                    {"version": 1, "assessment_date": "2026-01-02", "status": "completed"},
                    {"version": 2, "assessment_date": "2026-02-03", "status": "superseded"},
                ],
            },
            "expected_lines": 2,
        },
        {
            "label": "empty",
            "data": {"count": 0, "assessments": []},
            "expected_lines": 1,
        },
    ]

    with tempfile.TemporaryDirectory() as workspace:
        for item in payloads:
            probe = (
                "const d = "
                + _json_literal(item["data"])
                + ";\nconst history = { textContent: null };\n"
                + statement
                + "\nprocess.stdout.write(history.textContent);\n"
            )
            script = Path(workspace) / f"assessment_{item['label']}.js"
            script.write_text(probe, encoding="utf-8", newline="")

            parsed = subprocess.run(
                ["node", "--check", str(script)], capture_output=True, text=True
            )
            assert parsed.returncode == 0, (
                f"assessment ui rendered invalid JavaScript: {parsed.stderr}"
            )

            ran = subprocess.run(["node", str(script)], capture_output=True, text=True)
            assert ran.returncode == 0, ran.stderr
            rendered = ran.stdout
            assert len(rendered.split("\n")) == item["expected_lines"], rendered
            if item["label"] == "empty":
                assert rendered == "Brak zapisanych wersji."
