from pathlib import Path


APP_INDEX = Path(__file__).parent / "app" / "index.html"


def test_progress_shell_contains_metric_sections_and_loader():
    html = APP_INDEX.read_text(encoding="utf-8")
    required_markers = (
        'id="postepyStrengthWrap"',
        'id="postepyShootingWrap"',
        'id="postepyAssessmentWrap"',
        'id="postepyGoalsWrap"',
        "loadProgressStats();",
    )
    for marker in required_markers:
        assert marker in html
