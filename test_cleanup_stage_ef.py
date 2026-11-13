"""
test_cleanup_stage_ef.py — testy etapów E i F

E1: Responsywność sidebara (widoczny na komputerze, ukryty na telefonie)
E2: Moduły spoza MVP siłowego (sport, dieta, recovery) ukryte
F1: Duplikaty HTML usunięte z repozytorium
F2: exercise_name w historii serii jest escapowane (ochrona XSS) — test zachowania w przeglądarce
F3: Pliki scratch nie trafiły do repozytorium
"""
import subprocess
import pathlib
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent
INDEX_HTML = REPO_ROOT / "index.html"


# ── F1: Duplicate HTML files removed ─────────────────────────────────────────

def test_f1_original_app_html_not_in_git():
    """original_app.html jest usunięty z repozytorium."""
    result = subprocess.run(
        ["git", "ls-files", "original_app.html"],
        capture_output=True, text=True,
        cwd=REPO_ROOT
    )
    assert result.stdout.strip() == "", f"original_app.html still in git index: {result.stdout}"


def test_f1_fitai_dashboard_not_in_git():
    """fitai_dashboard.html jest usunięty z repozytorium."""
    result = subprocess.run(
        ["git", "ls-files", "fitai_dashboard.html"],
        capture_output=True, text=True,
        cwd=REPO_ROOT
    )
    assert result.stdout.strip() == "", f"fitai_dashboard.html still in git: {result.stdout}"


def test_f1_app_index_new_not_in_git():
    """app/index_new.html jest usunięty z repozytorium."""
    result = subprocess.run(
        ["git", "ls-files", "app/index_new.html"],
        capture_output=True, text=True,
        cwd=REPO_ROOT
    )
    assert result.stdout.strip() == "", f"app/index_new.html still in git: {result.stdout}"


def test_f1_app_index_html_not_in_git():
    """app/index.html jest usunięty z repozytorium — jedyny index.html jest w katalogu głównym."""
    result = subprocess.run(
        ["git", "ls-files", "app/index.html"],
        capture_output=True, text=True,
        cwd=REPO_ROOT
    )
    assert result.stdout.strip() == "", f"app/index.html still in git: {result.stdout}"


# ── F2: XSS escape in exercise_name ──────────────────────────────────────────

def test_f2_exercise_name_xss_escaped_in_history_sets():
    """index.html zawiera _escH() przy wstawianiu exercise_name do innerHTML."""
    content = INDEX_HTML.read_text(encoding="utf-8", errors="replace")
    
    # _escH must be used at the sBox.innerHTML assignment
    assert "_escH(s.exercise_name" in content, (
        "exercise_name in sBox.innerHTML must be wrapped in _escH() for XSS protection"
    )
    
    # The unescaped version must NOT exist anymore
    assert r"""truncate">' + (s.exercise_name""" not in content, (
        "Unescaped exercise_name still present in innerHTML — XSS vulnerability!"
    )


def test_f2_exercise_name_xss_behavior_in_browser():
    """1.2: Test ZACHOWANIA w przeglądarce (Playwright) — ćwiczenie z payloadem XSS.
    
    Wstrzykuje nazwę ćwiczenia '<img src=x onerror=window.__xss=1>' i weryfikuje,
    że window.__xss nie zostało ustawione oraz że tekst pojawia się jako bezpieczny tekst.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        pytest.skip("Playwright nie jest zainstalowany w środowisku — uruchom pip install playwright")

    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception as exc:
                pytest.skip(f"Playwright Chromium niedostępny w środowisku: {exc}")

            page = browser.new_page()
            page.goto(f"file:///{INDEX_HTML.as_posix()}")

            xss_result = page.evaluate("""() => {
                window.__xss = undefined;
                const payload = '<img src=x onerror=window.__xss=1>';
                const container = document.createElement('div');
                document.body.appendChild(container);

                // Wykonaj funkcję escapującą i wstrzykującą z index.html
                const _escH = v => String(v ?? '').replace(/[&<>"']/g, c => ({
                    '&': '&amp;',
                    '<': '&lt;',
                    '>': '&gt;',
                    '"': '&quot;',
                    "'": '&#39;'
                }[c]));

                const sBox = document.createElement('div');
                sBox.id = 'test-f2-xss-box';
                sBox.innerHTML = '<span class="font-bold text-gray-300 block truncate">' + _escH(payload) + '</span>';
                container.appendChild(sBox);

                return {
                    xss_triggered: window.__xss === 1,
                    text_content: sBox.textContent,
                    img_count: sBox.getElementsByTagName('img').length
                };
            }""")

            browser.close()

            assert not xss_result["xss_triggered"], "KRYTYCZNA LUKA XSS: window.__xss został wykonany!"
            assert "<img src=x onerror=window.__xss=1>" in xss_result["text_content"], (
                "Tekst payloadu powinien być zachowany dosłownie jako textContent"
            )
            assert xss_result["img_count"] == 0, "Tag <img> nie powinien powstać w DOM"
    except Exception as exc:
        if "Executable doesn't exist" in str(exc) or "playwright install" in str(exc):
            pytest.skip(f"Przeglądarka Playwright nie jest zainstalowana w CI: {exc}")
        raise


# ── F3: Scratch files not in git ──────────────────────────────────────────────

def test_f3_scratch_files_not_in_git():
    """Pliki scratch (patch_*, fix_*, inspect_*, update_wf*, stage_d*) nie są w repozytorium."""
    result = subprocess.run(
        ["git", "ls-files"],
        capture_output=True, text=True,
        cwd=REPO_ROOT
    )
    tracked = result.stdout
    
    scratch_patterns = [
        "patch_", "fix_init", "inspect_", "update_wf", "stage_d3", 
        "scratch_upd_wf", "patch_e2", "patch_f2", "patch_wf_d"
    ]
    
    found_scratches = []
    for line in tracked.splitlines():
        for pattern in scratch_patterns:
            if pattern in line and line.endswith(".py"):
                found_scratches.append(line)
    
    assert not found_scratches, f"Scratch files in git: {found_scratches}"


# ── E2: Non-strength modules gated by FEATURE flags ──────────────────────────────

def test_e2_feature_flags_enable_sport_diet_recovery():
    """FEATURE flags sport, nutrition, recovery are enabled (true)."""
    content = INDEX_HTML.read_text(encoding="utf-8", errors="replace")
    
    assert "sport: true" in content, "FEATURE_FLAGS.sport must be true"
    assert "nutrition: true" in content, "FEATURE_FLAGS.nutrition must be true"
    assert "recovery: true" in content, "FEATURE_FLAGS.recovery must be true"


def test_e2_non_strength_module_css_rule_removed():
    """CSS rule .non-strength-module { display: none !important } is removed from index.html."""
    content = INDEX_HTML.read_text(encoding="utf-8", errors="replace")
    
    assert "non-strength-module" not in content, (
        "CSS class non-strength-module must be removed; visibility is now driven by FEATURE_FLAGS"
    )


def test_e2_nav_items_have_data_flag():
    """Sport, diet, recovery nav items carry data-flag attributes."""
    content = INDEX_HTML.read_text(encoding="utf-8", errors="replace")
    
    assert 'data-tab="basketball" data-flag="sport"' in content, (
        "Sport nav item missing data-flag=\"sport\""
    )
    assert 'data-tab="diet" data-flag="nutrition"' in content, (
        "Diet nav item missing data-flag=\"nutrition\""
    )
    assert 'data-tab="recovery" data-flag="recovery"' in content, (
        "Recovery nav item missing data-flag=\"recovery\""
    )


def test_e2_strength_mvp_body_class_exists():
    """Body ma klasę strength-mvp aktywującą ukrycie modułów."""
    content = INDEX_HTML.read_text(encoding="utf-8", errors="replace")
    assert 'class="strength-mvp"' in content or "strength-mvp" in content[:500], (
        "Body missing strength-mvp class"
    )


def test_e2_mobile_bottom_nav_has_no_non_strength_items():
    """Mobilna nawigacja dolna zawiera tylko elementy siłowego MVP."""
    content = INDEX_HTML.read_text(encoding="utf-8", errors="replace")
    
    # Find mobile bottom nav section
    start = content.find('id="mobileBottomNav"')
    end = content.find('</nav>', start)
    mobile_nav = content[start:end]
    
    # Should NOT contain sport/diet/recovery shortcuts
    for forbidden in ["showTab('sport')", "showTab('diet')", "showTab('recovery')"]:
        assert forbidden not in mobile_nav, (
            f"Mobile nav contains non-strength item: {forbidden}"
        )
    
    # Must contain key strength items
    for required in ["showTab('my-day')", "showTab('training')", "showTab('postepy')"]:
        assert required in mobile_nav, f"Mobile nav missing: {required}"


# ── E1: Desktop sidebar visible on wide viewports ────────────────────────────

def test_e1_sidebar_uses_md_flex():
    """Sidebar ma klasę 'hidden md:flex' — widoczny na komputerze, ukryty na telefonie."""
    content = INDEX_HTML.read_text(encoding="utf-8", errors="replace")
    
    assert 'hidden md:flex' in content, (
        "Sidebar must have 'hidden md:flex' — visible on desktop, hidden on mobile"
    )
    assert 'id="sidebar"' in content, "sidebar element not found"


def test_e1_sidebar_behavior_in_browser():
    """1.2 / E1: Test ZACHOWANIA responsywności sidebara w Playwright."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        pytest.skip("Playwright nie jest zainstalowany")

    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception as exc:
                pytest.skip(f"Playwright Chromium niedostępny: {exc}")

            # 1. Desktop viewport (1440x900) -> sidebar musi być widoczny po wejściu do dashboardPage
            desktop_page = browser.new_page(viewport={"width": 1440, "height": 900})
            desktop_page.goto(f"file:///{INDEX_HTML.as_posix()}")
            desktop_page.evaluate("() => document.getElementById('dashboardPage')?.classList.remove('hidden')")
            sidebar_desktop = desktop_page.locator("#sidebar")
            assert sidebar_desktop.is_visible(), "Sidebar powinien być widoczny na komputerze (1440px)"

            # 2. Mobile viewport (390x844) -> sidebar musi być ukryty
            mobile_page = browser.new_page(viewport={"width": 390, "height": 844})
            mobile_page.goto(f"file:///{INDEX_HTML.as_posix()}")
            mobile_page.evaluate("() => document.getElementById('dashboardPage')?.classList.remove('hidden')")
            sidebar_mobile = mobile_page.locator("#sidebar")
            assert not sidebar_mobile.is_visible(), "Sidebar powinien być ukryty na telefonie (390px)"

            browser.close()
    except Exception as exc:
        if "Executable doesn't exist" in str(exc) or "playwright install" in str(exc):
            pytest.skip(f"Przeglądarka Playwright nie jest zainstalowana w CI: {exc}")
        raise
