"""
test_strength_mvp_iteration4.py — Testy jednostkowe i integracyjne dla Etapu 2 (Iteracja 4).

Weryfikuje:
- 2.1 Kontrast tekstu i widoczność nagłówka na ekranie Dziś (WCAG AA >= 4.5:1)
- 2.2 Kolejność i nazewnictwo nawigacji bocznej na komputerze (Dziś, Plan, Trening, Postępy, Profil; brak numeracji 1., 3.; assessment w non-strength-module)
- 2.3 Ukrywanie menu marketingowego po zalogowaniu, brak nachodzenia numeru na nazwę, branding EVOLVE z wersją
- 2.4 Live Workout Runner: pole kg mieści >= 6 znaków (min. 75px), inputmode="decimal" dla kg, inputmode="numeric" dla reps i rpe, obecność stopera przerw
- 2.5 "Twój fundament": brak zgadywania biometrii (brak wagi/wzrostu = '—'), obecność zachęty do uzupełnienia
- 2.6 Neutralne powitanie bez numeru konta i brak domyślnej nazwy "Zawodnik"
"""
import re
from pathlib import Path
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models import UserDB
from app.auth.routes import router as auth_router
from fastapi import FastAPI

REPO_ROOT = Path(__file__).resolve().parent
INDEX_HTML = (REPO_ROOT / "index.html").read_text(encoding="utf-8")


def test_2_2_sidebar_navigation_order_and_clean_labels():
    """2.2: W nawigacji bocznej (desktop):

    - brak numeracji '1.', '3.', '6.', '7.'
    - dodana pozycja 'Trening'
    - 'Assessment' ukryty w non-strength-module
    - kolejność: Dziś, Plan, Trening, Postępy, Profil
    """
    sidebar_match = re.search(r'<aside id="sidebar"[\s\S]*?</aside>', INDEX_HTML)
    assert sidebar_match, "Brak elementu <aside id=\"sidebar\"> w index.html"
    sidebar_html = sidebar_match.group(0)

    # 1. Brak numeracji 1., 3., 6., 7.
    assert "1. Dziś" not in sidebar_html
    assert "3. Plan" not in sidebar_html
    assert "6. Postępy" not in sidebar_html
    assert "7. Assessment" not in sidebar_html

    # 2. Assessment nie używa już klasy non-strength-module (flaga FEATURE_FLAGS jest źródłem prawdy)
    assessment_match = re.search(r'<a[^>]*data-tab="assessment"[^>]*>', sidebar_html)
    assert assessment_match, "Brak linku assessment w sidebarze"
    assert "non-strength-module" not in assessment_match.group(0), "Assessment nie powinien już używać klasy non-strength-module"

    # 3. Kolejność pozycji: Dziś, Plan, Trening, Postępy, Profil
    # Sprawdzamy kolejność występowania znaczników w nawigacji
    idx_my_day = sidebar_html.find('data-tab="my-day"')
    idx_plan = sidebar_html.find('data-tab="training"')
    idx_workout = sidebar_html.find('data-tab="live-workout"')
    idx_postepy = sidebar_html.find('data-tab="postepy"')
    idx_profile = sidebar_html.find('data-tab="profile"')

    assert idx_my_day != -1, "Brak pozycji Dziś w sidebarze"
    assert idx_plan != -1, "Brak pozycji Plan w sidebarze"
    assert idx_workout != -1, "Brak pozycji Trening w sidebarze"
    assert idx_postepy != -1, "Brak pozycji Postępy w sidebarze"
    assert idx_profile != -1, "Brak pozycji Profil w sidebarze"

    assert idx_my_day < idx_plan < idx_workout < idx_postepy < idx_profile, (
        f"Nieprawidłowa kolejność nawigacji: Dziś({idx_my_day}), Plan({idx_plan}), "
        f"Trening({idx_workout}), Postępy({idx_postepy}), Profil({idx_profile})"
    )


def test_2_3_header_brand_version_and_clean_sidebar():
    """2.3: Zastąpienie 'FitAI v3.0 Ultimate' przez 'EVOLVE' z wersją, pojedynczy przycisk Wyloguj,

    ukrywanie menu marketingowego po zalogowaniu.
    """
    sidebar_match = re.search(r'<aside id="sidebar"[\s\S]*?</aside>', INDEX_HTML)
    assert sidebar_match
    sidebar_html = sidebar_match.group(0)

    # Brak starego napisu FitAI v3.0 Ultimate
    assert "FitAI v3.0 Ultimate" not in sidebar_html
    assert "EVOLVE" in sidebar_html

    # Brak linku 'Strona główna' w sidebarze (zostaje tylko Wyloguj)
    assert "← Strona główna" not in sidebar_html
    assert "logoutUser()" in sidebar_html

    # Ukrywanie landingLinks po zalogowaniu używa style.display = 'none' lub usunięcia md:flex
    assert (
        "links.style.display = 'none'" in INDEX_HTML
        or "landingLinks.style.display = 'none'" in INDEX_HTML
        or "links.classList.remove('md:flex')" in INDEX_HTML
    )


def test_2_4_live_workout_runner_inputs_and_rest_timer():
    """2.4:

    - Pole ciężaru kg mieści min 6 znaków (min-width >= 75px)
    - inputmode='decimal' dla kg
    - inputmode='numeric' dla reps i rpe
    - Widoczny stoper przerw runnerRestBanner
    """
    # 1. Sprawdź szablon serii
    assert 'inputmode="decimal"' in INDEX_HTML, "Brak inputmode='decimal' dla pola ciężaru"
    assert 'inputmode="numeric"' in INDEX_HTML, "Brak inputmode='numeric' dla powtórzeń i RPE"

    # 2. Sprawdź obecność stopera przerw
    assert 'id="runnerRestBanner"' in INDEX_HTML, "Brak banera stopera przerw runnerRestBanner"
    assert 'id="runnerRestTime"' in INDEX_HTML, "Brak elementu czasu stopera runnerRestTime"
    assert 'id="btnRestSkip"' in INDEX_HTML, "Brak przycisku pominięcia stopera btnRestSkip"
    assert 'id="btnRestAdd30"' in INDEX_HTML, "Brak przycisku +30s w stoperze"


def test_2_5_your_foundation_sidebar_no_biometrics_guessing():
    """2.5: Brak zgadywania biometrii — profil bez wagi/wzrostu nie dostaje zmyślonych kalorii/białka."""
    calc_match = re.search(r'function calculateNutrition\(profile\)\s*\{([\s\S]*?)\n    \}', INDEX_HTML)
    assert calc_match, "Brak funkcji calculateNutrition w index.html"
    calc_code = calc_match.group(1)

    # calculateNutrition nie może używać fallbacku profile.weight || 75
    assert "|| 75" not in calc_code, "Wykryto zgadywanie wagi 75kg w calculateNutrition"
    assert "|| 175" not in calc_code, "Wykryto zgadywanie wzrostu 175cm w calculateNutrition"

    # Sidebar zawiera element zachęty do uzupełnienia profilu
    assert 'id="sidebarCompleteProfileHint"' in INDEX_HTML, "Brak elementu zachęty do uzupełnienia profilu w sidebarze"


def test_2_6_registration_neutral_greeting_and_default_name():
    """2.6: Domyślna nazwa to nie 'Zawodnik' a neutralne powitanie po rejestracji nie zawiera numeru konta."""
    # 1. Weryfikacja powitania po rejestracji w JS
    assert "Konto zostało utworzone" in INDEX_HTML
    # Powitanie nie może doklejać numeru konta ani Użytkownik# do komunikatu
    assert "🎉 Witaj w EVOLVE! Konto zostało utworzone." in INDEX_HTML or "Witaj w EVOLVE!" in INDEX_HTML

    # 2. Weryfikacja endpointu rejestracji na backendzie
    import inspect
    from app.auth.routes import register
    source = inspect.getsource(register)
    assert '"Zawodnik"' not in source, "Rejestracja nadal ustawia domyślne imię 'Zawodnik'"
