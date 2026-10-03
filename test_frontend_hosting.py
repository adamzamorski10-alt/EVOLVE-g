from pathlib import Path


def test_hosted_frontend_uses_same_origin_backend_on_render_and_exposes_my_day():
    html = (Path(__file__).parent / "index.html").read_text(encoding="utf-8")

    assert "location.hostname.endsWith('.onrender.com')" in html
    assert "location.origin" in html
    assert 'href="/app/training/today-ui"' in html
    assert "<span>Mój dzień</span>" in html
    assert "<span>Today</span>" not in html


def test_main_navigation_matches_evolve_domain_model():
    html = (Path(__file__).parent / "index.html").read_text(encoding="utf-8")

    expected = [
        "Home",
        "Mój dzień",
        "Trening",
        "Koszykówka",
        "Dieta",
        "Recovery",
        "Postępy",
        "Profil",
    ]
    for label in expected:
        assert f"<span>{label}</span>" in html

    assert "<span>Plan</span>" not in html
    assert 'id="tab-recovery"' in html
    assert "data-tab="recovery"" in html


def test_frontend_supports_hash_deep_link_to_my_day():
    html = (Path(__file__).parent / "index.html").read_text(encoding="utf-8")

    assert "showTabFromHash" in html
    assert "window.location.hash.replace" in html
    assert "hashchange" in html


def test_frontend_deep_link_enters_dashboard_before_selecting_tab():
    html = (Path(__file__).parent / "index.html").read_text(encoding="utf-8")

    assert "typeof enterDashboard === 'function'" in html
    assert "enterDashboard();" in html
    assert "showTab(tabId);" in html


def test_server_serves_dashboard_first_without_landing_flash():
    app_init = (Path(__file__).parent / "app" / "__init__.py").read_text(encoding="utf-8")

    assert 'id="evolve-dashboard-first-style"' in app_init
    assert "#landingPage { display: none !important; }" in app_init
    assert "#dashboardPage.hidden { display: flex !important; }" in app_init
    assert "document.documentElement.classList.add('evolve-dashboard-first')" in app_init
    assert 'id="evolve-dashboard-first-boot"' in app_init
    assert "if (typeof enterDashboard === 'function') enterDashboard();" in app_init
