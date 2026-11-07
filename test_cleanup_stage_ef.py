"""
test_cleanup_stage_ef.py — testy etapów E i F

E2: Moduły spoza MVP siłowego (sport, dieta, recovery) ukryte przez CSS/class
F1: Duplikaty HTML usunięte z repozytorium
F2: exercise_name w historii serii jest escapowane (ochrona XSS)
F3: Pliki scratch nie trafiły do repozytorium
"""
import subprocess
import pathlib

import pytest


# ── F1: Duplicate HTML files removed ─────────────────────────────────────────

def test_f1_original_app_html_not_in_git():
    """original_app.html jest usunięty z repozytorium."""
    result = subprocess.run(
        ["git", "ls-files", "original_app.html"],
        capture_output=True, text=True,
        cwd=r"f:\Projects\Training_coach"
    )
    assert result.stdout.strip() == "", f"original_app.html still in git index: {result.stdout}"


def test_f1_fitai_dashboard_not_in_git():
    """fitai_dashboard.html jest usunięty z repozytorium."""
    result = subprocess.run(
        ["git", "ls-files", "fitai_dashboard.html"],
        capture_output=True, text=True,
        cwd=r"f:\Projects\Training_coach"
    )
    assert result.stdout.strip() == "", f"fitai_dashboard.html still in git: {result.stdout}"


def test_f1_app_index_new_not_in_git():
    """app/index_new.html jest usunięty z repozytorium."""
    result = subprocess.run(
        ["git", "ls-files", "app/index_new.html"],
        capture_output=True, text=True,
        cwd=r"f:\Projects\Training_coach"
    )
    assert result.stdout.strip() == "", f"app/index_new.html still in git: {result.stdout}"


# ── F2: XSS escape in exercise_name ──────────────────────────────────────────

def test_f2_exercise_name_xss_escaped_in_history_sets():
    """index.html zawiera _escH() przy wstawianiu exercise_name do innerHTML."""
    index_path = pathlib.Path(r"f:\Projects\Training_coach\index.html")
    content = index_path.read_text(encoding="utf-8", errors="replace")
    
    # _escH must be used at the sBox.innerHTML assignment
    assert "_escH(s.exercise_name" in content, (
        "exercise_name in sBox.innerHTML must be wrapped in _escH() for XSS protection"
    )
    
    # The unescaped version must NOT exist anymore
    assert r"""truncate">' + (s.exercise_name""" not in content, (
        "Unescaped exercise_name still present in innerHTML — XSS vulnerability!"
    )


# ── F3: Scratch files not in git ──────────────────────────────────────────────

def test_f3_scratch_files_not_in_git():
    """Pliki scratch (patch_*, fix_*, inspect_*, update_wf*, stage_d*) nie są w repozytorium."""
    result = subprocess.run(
        ["git", "ls-files"],
        capture_output=True, text=True,
        cwd=r"f:\Projects\Training_coach"
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


# ── E2: Non-strength modules hidden in UI ────────────────────────────────────

def test_e2_non_strength_modules_have_hide_class():
    """Elementy nawigacji dla sport, dieta, recovery mają klasę non-strength-module."""
    index_path = pathlib.Path(r"f:\Projects\Training_coach\index.html")
    content = index_path.read_text(encoding="utf-8", errors="replace")
    
    # CSS rule must exist
    assert "non-strength-module" in content, "CSS class non-strength-module not found"
    
    # Sport nav item must have class
    assert 'data-tab="basketball" class="nav-item non-strength-module' in content, (
        "Sport nav item missing non-strength-module class"
    )
    
    # Diet nav item must have class
    assert 'data-tab="diet" class="nav-item non-strength-module' in content, (
        "Diet nav item missing non-strength-module class"
    )
    
    # Recovery nav item must have class
    assert 'data-tab="recovery" class="nav-item non-strength-module' in content, (
        "Recovery nav item missing non-strength-module class"
    )


def test_e2_strength_mvp_body_class_exists():
    """Body ma klasę strength-mvp aktywującą ukrycie modułów."""
    index_path = pathlib.Path(r"f:\Projects\Training_coach\index.html")
    content = index_path.read_text(encoding="utf-8", errors="replace")
    assert 'class="strength-mvp"' in content or "strength-mvp" in content[:500], (
        "Body missing strength-mvp class"
    )


def test_e2_mobile_bottom_nav_has_no_non_strength_items():
    """Mobilna nawigacja dolna zawiera tylko elementy siłowego MVP."""
    index_path = pathlib.Path(r"f:\Projects\Training_coach\index.html")
    content = index_path.read_text(encoding="utf-8", errors="replace")
    
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
    index_path = pathlib.Path(r"f:\Projects\Training_coach\index.html")
    content = index_path.read_text(encoding="utf-8", errors="replace")
    
    assert 'hidden md:flex' in content, (
        "Sidebar must have 'hidden md:flex' — visible on desktop, hidden on mobile"
    )
    assert 'id="sidebar"' in content, "sidebar element not found"

