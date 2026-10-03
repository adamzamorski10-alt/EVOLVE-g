from pathlib import Path


def test_hosted_frontend_uses_same_origin_backend_on_render_and_exposes_today():
    html = (Path(__file__).parent / "index.html").read_text(encoding="utf-8")

    assert "location.hostname.endsWith('.onrender.com')" in html
    assert "location.origin" in html
    assert 'href="/app/training/today-ui"' in html
    assert "<span>Today</span>" in html
