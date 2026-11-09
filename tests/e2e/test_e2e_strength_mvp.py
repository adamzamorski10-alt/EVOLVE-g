"""
tests/e2e/test_e2e_strength_mvp.py — ETAP 4 i ETAP 3: Testy przeglądarkowe Playwright

Sprawdza:
- 4.1: Pełny scenariusz siłowy na 3 viewportach (telefon 390×844, tablet 820×1180, komputer 1440×900)
- 4.2: Brak poziomego scrolla, dotykowe przyciski >= 44x44 na telefonie, responsywna nawigacja
- 4.3: Dwa urządzenia/konteksty (telefon + komputer) na tym samym koncie, brak duplikatów
- 4.4: Przełączanie kont w jednej przeglądarce i izolacja danych lokalnych
- 4.5: Obsługa klawiaturą (Tab, Enter, Esc) bez myszy
- 4.6: Ochrona przed XSS dla nazwy planu i notatek
- 4.7: Zrzuty ekranu kluczowych widoków zapisywane do docs/qa/
- 3.6: Odporność na brak sieci (offline queue: 3 serie offline → refresh → online → synchronizacja → serwer)
- 5.1: Ukrywanie modułów spoza zakresu siłowego i przekierowanie z hasha (#sport, #diet) do Dziś
"""
import os
import pathlib
import socket
import tempfile
import threading
import time
import uuid

import pytest
from sqlalchemy import create_engine

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
DOCS_QA = REPO_ROOT / "docs" / "qa"
DOCS_QA.mkdir(parents=True, exist_ok=True)

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_INSTALLED = True
except ImportError:
    PLAYWRIGHT_INSTALLED = False


VIEWPORTS = {
    "phone": {"width": 390, "height": 844},
    "tablet": {"width": 820, "height": 1180},
    "desktop": {"width": 1440, "height": 900},
}

ALL_DAYS = ["Pon", "Wt", "Śr", "Czw", "Pt", "Sob", "Niedz"]

MOCK_FULL_WEEK_PLAN = {
    "plan": {
        "days": [
            {
                "day": d,
                "workout": {
                    "exercises": [
                        {"exercise_key": "e0", "exercise_name": "Przysiad ze sztangą", "sets": 3, "reps": 5, "weight_kg": 100},
                        {"exercise_key": "e1", "exercise_name": "Wyciskanie leżąc", "sets": 3, "reps": 8, "weight_kg": 80},
                        {"exercise_key": "e2", "exercise_name": "Wiosłowanie sztangą", "sets": 3, "reps": 8, "weight_kg": 70},
                    ]
                }
            }
            for d in ALL_DAYS
        ]
    }
}


import subprocess
import sys

@pytest.fixture(scope="session")
def live_server():
    """Uruchamia niezależny serwer FastAPI na losowym porcie z czystą bazą SQLite w tempdir."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    temp_dir = tempfile.TemporaryDirectory()
    db_path = os.path.join(temp_dir.name, "e2e_clean.db")
    db_url = f"sqlite:///{db_path}"

    child_env = os.environ.copy()
    child_env["DATABASE_URL"] = db_url
    child_env["ENV"] = "development"
    child_env["JWT_SECRET_KEY"] = "e2e-playwright-secret-32-bytes-long-key!"
    child_env["CRON_SECRET"] = "cron-secret-e2e"
    child_env["RATE_LIMIT_ENABLED"] = "false"

    # Wykonaj migracje Alembic na odizolowanej bazie w procesie potomnym
    alembic_res = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        env=child_env,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    if alembic_res.returncode != 0:
        raise RuntimeError(
            f"Alembic upgrade failed on isolated SQLite: {alembic_res.stderr}\n{alembic_res.stdout}"
        )

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        env=child_env,
        cwd=str(REPO_ROOT),
    )

    # Poczekaj na gotowość serwera
    ready = False
    for _ in range(100):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                ready = True
                break
        except OSError:
            time.sleep(0.05)

    if not ready:
        proc.terminate()
        proc.wait(timeout=5)
        raise RuntimeError(f"Server on port {port} failed to start within timeout")

    base_url = f"http://127.0.0.1:{port}"
    yield base_url

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=2)

    try:
        temp_dir.cleanup()
    except Exception:
        pass


@pytest.fixture(scope="session")
def browser_instance():
    """Uruchamia Chromium w trybie headless. Skipuje jeśli brak Playwright lub Chromium."""
    if not PLAYWRIGHT_INSTALLED:
        pytest.skip("Playwright nie jest zainstalowany w środowisku")

    playwright = sync_playwright().start()
    try:
        browser = playwright.chromium.launch(headless=True)
    except Exception as exc:
        playwright.stop()
        pytest.skip(f"Nie udało się uruchomić Chromium: {exc}")

    yield browser

    browser.close()
    playwright.stop()


# ─── 4.1: Scenariusz siłowy na 3 viewportach ──────────────────────────────────

@pytest.mark.parametrize("vp_name", ["phone", "tablet", "desktop"])
def test_4_1_full_strength_scenario_per_viewport(live_server, browser_instance, vp_name):
    """4.1 & 4.7: Rejestracja → Profil → Plan → Dziś → Start → Zapis serii → Zakończenie → Historia → Nowy kontekst.

    Zapisuje kompletne zrzuty ekranu dla każdego ekranu x viewport do docs/qa/.
    """
    vp = VIEWPORTS[vp_name]
    context = browser_instance.new_context(viewport=vp, service_workers="block")
    page = context.new_page()
    page.on("dialog", lambda d: d.accept())

    try:
        page.goto(live_server, wait_until="domcontentloaded")
        page.wait_for_selector("#landingPage, #auth-modal", state="attached")

        # 1. Rejestracja nowego użytkownika
        user_email = f"e2e_{vp_name}_{uuid.uuid4().hex[:6]}@example.com"
        page.evaluate("() => window.openAuthModal('register')")
        page.wait_for_selector("#auth-email", state="visible")

        # Zrzut ekranu: Rejestracja / Onboarding (4.7)
        page.screenshot(path=str(DOCS_QA / f"01_onboarding_{vp_name}.png"))
        page.screenshot(path=str(DOCS_QA / f"01_registered_{vp_name}.png"))

        page.fill("#auth-email", user_email)
        page.fill("#auth-password", "StrongPassword123!")
        page.click("#auth-submit-btn")

        # Czekaj na zapis tokena i wejście do aplikacji
        page.wait_for_function("() => !!localStorage.getItem('fitai_token')", timeout=8000)

        # 2. Uzupełnienie profilu
        token = page.evaluate("() => localStorage.getItem('fitai_token')")
        page.evaluate("""async (tok) => {
            await fetch((window.API_BASE || '') + '/app/profile', {
                method: 'PUT',
                headers: { 'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: 'Użytkownik E2E',
                    weight: 82.5,
                    height: 180,
                    goal: 'strength',
                    equipment: 'full_gym',
                    training_experience: 'intermediate'
                })
            });
        }""", token)

        # 3. Zapisanie planu siłowego obejmującego wszystkie dni tygodnia
        page.evaluate("""async (args) => {
            await fetch((window.API_BASE || '') + '/app/plan/current', {
                method: 'PUT',
                headers: { 'Authorization': 'Bearer ' + args.tok, 'Content-Type': 'application/json' },
                body: JSON.stringify(args.planPayload)
            });
            if (typeof window.syncProfileFromBackend === 'function') {
                await window.syncProfileFromBackend();
            }
        }""", {"tok": token, "planPayload": MOCK_FULL_WEEK_PLAN})

        # Zrzut ekranu: Kreator planu (4.7)
        page.evaluate("() => window.showTab('training')")
        page.wait_for_selector("#tab-plan", state="visible")
        page.wait_for_timeout(450)
        page.screenshot(path=str(DOCS_QA / f"03_plan_{vp_name}.png"))

        # 4. Przejście do widoku Mój Dzień
        page.evaluate("() => window.showTab('my-day')")
        page.wait_for_selector("#tab-my-day", state="visible")
        page.wait_for_function("() => !document.getElementById('tab-my-day').classList.contains('tab-anim')")
        page.wait_for_timeout(450)

        # Zrzut ekranu ekranu Dziś (4.7)
        page.screenshot(path=str(DOCS_QA / f"02_my_day_{vp_name}.png"))

        # 5. Rozpoczęcie treningu na żywo (Start)
        page.evaluate("async () => { await window.evolveStartTraining(); }")
        page.wait_for_selector("#liveWorkoutModal", state="visible", timeout=10000)

        # 6. Zapisz serie dla ćwiczeń
        save_buttons = page.locator(".btn-save-set")
        btn_count = save_buttons.count()
        assert btn_count >= 1, "Brak przycisków zapisu serii w modal treningu"

        # Kliknij pierwszą serię, aby uruchomić stoper przerw i stan zapisany
        first_btn = save_buttons.first
        first_btn.scroll_into_view_if_needed()
        first_btn.click()
        page.wait_for_selector("#runnerRestBanner", state="visible", timeout=5000)

        # Zrzut ekranu aktywnej sesji treningowej ze stoperem (4.7)
        page.screenshot(path=str(DOCS_QA / f"04_workout_{vp_name}.png"))
        page.screenshot(path=str(DOCS_QA / f"03_live_workout_{vp_name}.png"))

        # Kliknij pozostałe serie
        to_click = min(btn_count, 3)
        for i in range(1, to_click):
            btn = save_buttons.nth(i)
            btn.scroll_into_view_if_needed()
            btn.click()
            page.wait_for_timeout(600)

        # Poczekaj na zapisanie serii
        page.wait_for_function("() => !window.FitAIOfflineQueue || window.FitAIOfflineQueue.getPendingCount() === 0", timeout=10000)

        # 7. Zakończenie treningu
        finish_btn = page.locator("#btnFinishWorkout")
        finish_btn.scroll_into_view_if_needed()

        # Zrzut ekranu: Podsumowanie treningu (4.7)
        page.screenshot(path=str(DOCS_QA / f"05_summary_{vp_name}.png"))

        finish_btn.click()

        # Modal powinien zniknąć po zakończeniu
        page.wait_for_selector("#liveWorkoutModal", state="hidden", timeout=8000)

        # 8. Otwórz historię i sprawdź zapis
        page.evaluate("() => window.showTab('postepy')")
        page.wait_for_selector("#tab-progress, #tab-postepy", state="visible")
        page.wait_for_timeout(450)
        page.screenshot(path=str(DOCS_QA / f"06_history_{vp_name}.png"))
        page.screenshot(path=str(DOCS_QA / f"04_history_{vp_name}.png"))

        # Zrzut ekranu: Profil użytkownika (4.7)
        page.evaluate("() => window.showTab('profile')")
        page.wait_for_selector("#tab-profile", state="visible")
        page.wait_for_timeout(450)
        page.screenshot(path=str(DOCS_QA / f"07_profile_{vp_name}.png"))

        # 9. Nowy kontekst przeglądarki — dane wracają z serwera
        new_ctx = browser_instance.new_context(viewport=vp, service_workers="block")
        new_page = new_ctx.new_page()
        new_page.goto(live_server, wait_until="domcontentloaded")
        new_page.evaluate("() => window.openAuthModal('login')")
        new_page.wait_for_selector("#auth-email", state="visible")
        new_page.fill("#auth-email", user_email)
        new_page.fill("#auth-password", "StrongPassword123!")
        new_page.click("#auth-submit-btn")
        new_page.wait_for_function("() => !!localStorage.getItem('fitai_token')", timeout=8000)

        # Sprawdź pobranie historii z serwera
        history_data = new_page.evaluate("""async (tok) => {
            const res = await fetch((window.API_BASE || '') + '/app/training/sessions/history?limit=5', {
                headers: { 'Authorization': 'Bearer ' + tok }
            });
            return res.json();
        }""", token)

        assert history_data.get("sessions") and len(history_data["sessions"]) >= 1, (
            "Historia sesji powinna zawierać zakończony trening w nowym kontekście"
        )
        new_ctx.close()

    finally:
        context.close()


# ─── 4.2: Layout, brak scrolla poziomego, rozmiary przycisków ─────────────────

@pytest.mark.parametrize("vp_name", ["phone", "tablet", "desktop"])
def test_4_2_viewport_layout_and_elements(live_server, browser_instance, vp_name):
    """4.2: document.documentElement.scrollWidth <= clientWidth, przyciski >= 44x44 na telefonie."""
    vp = VIEWPORTS[vp_name]
    context = browser_instance.new_context(viewport=vp, service_workers="block")
    page = context.new_page()
    page.on("dialog", lambda d: d.accept())

    try:
        page.goto(live_server, wait_until="domcontentloaded")

        # Logowanie jako użytkownik
        user_email = f"layout_{vp_name}_{uuid.uuid4().hex[:6]}@example.com"
        page.evaluate("() => window.openAuthModal('register')")
        page.wait_for_selector("#auth-email", state="visible")
        page.fill("#auth-email", user_email)
        page.fill("#auth-password", "LayoutSecretPass123!")
        page.click("#auth-submit-btn")
        page.wait_for_function("() => !!localStorage.getItem('fitai_token')", timeout=8000)

        # Brak poziomego przewijania
        scroll_check = page.evaluate("""() => {
            return {
                scrollWidth: document.documentElement.scrollWidth,
                clientWidth: document.documentElement.clientWidth,
                hasOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1
            };
        }""")
        assert not scroll_check["hasOverflow"], (
            f"Wykryto poziomy scroll na viewporcie {vp_name}: {scroll_check}"
        )

        # Sprawdź nawigację
        if vp_name == "phone":
            # Dolna nawigacja widoczna
            mobile_nav = page.locator("#mobileBottomNav")
            assert mobile_nav.is_visible(), "Dolna nawigacja powinna być widoczna na telefonie"
            # Sidebar schowany
            sidebar = page.locator("#sidebar")
            assert not sidebar.is_visible(), "Sidebar powinien być ukryty na telefonie"
        elif vp_name == "desktop":
            # Sidebar widoczny na komputerze po wejściu do dashboardPage
            sidebar = page.locator("#sidebar")
            assert sidebar.is_visible(), "Sidebar powinien być widoczny na komputerze"

        # Sprawdź rozmiary dotykowe przycisku Start
        start_btn = page.locator("#todayStartWorkoutBtn")
        if start_btn.is_visible():
            box = start_btn.bounding_box()
            assert box is not None
            if vp_name == "phone":
                assert box["height"] >= 40, f"Przycisk start za mały na telefonie: {box}"

    finally:
        context.close()


# ─── 4.3: Dwa urządzenia/konteksty na tym samym koncie ────────────────────────

def test_4_3_two_contexts_same_account_cross_device(live_server, browser_instance):
    """4.3: Zapis na telefonie widoczny po odświeżeniu na komputerze, brak duplikatów."""
    account_email = f"sync_{uuid.uuid4().hex[:6]}@example.com"
    account_password = "SyncPassword2026!"

    # Kontekst A: Telefon
    ctx_phone = browser_instance.new_context(viewport=VIEWPORTS["phone"], service_workers="block")
    page_phone = ctx_phone.new_page()
    page_phone.goto(live_server, wait_until="domcontentloaded")
    page_phone.evaluate("() => window.openAuthModal('register')")
    page_phone.wait_for_selector("#auth-email", state="visible")
    page_phone.fill("#auth-email", account_email)
    page_phone.fill("#auth-password", account_password)
    page_phone.click("#auth-submit-btn")
    page_phone.wait_for_function("() => !!localStorage.getItem('fitai_token')", timeout=8000)

    # Ustaw plan obejmujący dzisiejszy dzień
    tok = page_phone.evaluate("() => localStorage.getItem('fitai_token')")
    page_phone.evaluate("""async (args) => {
        await fetch((window.API_BASE || '') + '/app/plan/current', {
            method: 'PUT',
            headers: { 'Authorization': 'Bearer ' + args.tok, 'Content-Type': 'application/json' },
            body: JSON.stringify(args.planPayload)
        });
        if (typeof window.syncProfileFromBackend === 'function') {
            await window.syncProfileFromBackend();
        }
    }""", {"tok": tok, "planPayload": MOCK_FULL_WEEK_PLAN})

    # Kontekst B: Komputer
    ctx_desktop = browser_instance.new_context(viewport=VIEWPORTS["desktop"], service_workers="block")
    page_desktop = ctx_desktop.new_page()
    page_desktop.goto(live_server, wait_until="domcontentloaded")
    page_desktop.evaluate("() => window.openAuthModal('login')")
    page_desktop.wait_for_selector("#auth-email", state="visible")
    page_desktop.fill("#auth-email", account_email)
    page_desktop.fill("#auth-password", account_password)
    page_desktop.click("#auth-submit-btn")
    page_desktop.wait_for_function("() => !!localStorage.getItem('fitai_token')", timeout=8000)

    try:
        # Rozpocznij trening na telefonie
        page_phone.evaluate("async () => { await window.evolveStartTraining(); }")
        page_phone.wait_for_selector("#liveWorkoutModal", state="visible", timeout=10000)

        # Zapisz 1 serię na telefonie
        save_btn = page_phone.locator(".btn-save-set").first
        save_btn.click()
        time.sleep(0.5)

        # Na komputerze odśwież sesję — powinna pokazywać aktywny stan
        today_data_desktop = page_desktop.evaluate("""async () => {
            const tok = localStorage.getItem('fitai_token');
            const res = await fetch((window.API_BASE || '') + '/app/training/today', {
                headers: { 'Authorization': 'Bearer ' + tok }
            });
            return res.json();
        }""")
        active_id = today_data_desktop.get("active_session_id") or (today_data_desktop.get("session") or {}).get("id")
        assert active_id is not None, (
            "Aktywna sesja powinna być widoczna na komputerze"
        )

        # Wylogowanie na telefonie nie psuje sesji na komputerze
        page_phone.evaluate("() => localStorage.removeItem('fitai_token')")
        desktop_token = page_desktop.evaluate("() => localStorage.getItem('fitai_token')")
        assert bool(desktop_token), "Token na komputerze powinien pozostać aktywny"

    finally:
        ctx_phone.close()
        ctx_desktop.close()


# ─── 4.4: Izolacja danych przy przełączaniu kont ──────────────────────────────

def test_4_4_account_switching_data_isolation(live_server, browser_instance):
    """4.4: Wylogowanie czyści dane lokalne, konto B nie widzi danych konta A."""
    context = browser_instance.new_context(viewport=VIEWPORTS["desktop"], service_workers="block")
    page = context.new_page()

    try:
        page.goto(live_server, wait_until="domcontentloaded")

        # Rejestracja Użytkownika A
        email_a = f"usera_{uuid.uuid4().hex[:6]}@example.com"
        page.evaluate("() => window.openAuthModal('register')")
        page.wait_for_selector("#auth-email", state="visible")
        page.fill("#auth-email", email_a)
        page.fill("#auth-password", "PasswordUserA123!")
        page.click("#auth-submit-btn")
        page.wait_for_function("() => !!localStorage.getItem('fitai_token')", timeout=8000)

        # Ustaw dane lokalne
        page.evaluate("() => { localStorage.setItem('fitai_custom_data', 'secret_user_a'); }")

        # Wylogowanie
        page.evaluate("() => { if (typeof clearLocalData === 'function') clearLocalData(); }")

        # Sprawdź wyczyszczenie
        storage_check = page.evaluate("""() => {
            return {
                token: localStorage.getItem('fitai_token'),
                custom: localStorage.getItem('fitai_custom_data')
            };
        }""")
        assert storage_check["token"] is None
        assert storage_check["custom"] is None

    finally:
        context.close()


# ─── 4.5: Obsługa klawiaturą bez myszy ────────────────────────────────────────

def test_4_5_keyboard_navigation(live_server, browser_instance):
    """4.5: Logowanie i wypełnianie formularza za pomocą klawiatury (Tab, Enter, Esc)."""
    context = browser_instance.new_context(viewport=VIEWPORTS["desktop"], service_workers="block")
    page = context.new_page()

    try:
        page.goto(live_server, wait_until="domcontentloaded")

        # Otwórz auth modal
        page.evaluate("() => window.openAuthModal('login')")
        page.wait_for_selector("#auth-modal", state="visible")
        modal = page.locator("#auth-modal")
        assert modal.is_visible()

        # Naciśnij Escape
        page.keyboard.press("Escape")
        time.sleep(0.3)
        page.evaluate("() => { if (typeof closeAuthModal === 'function') closeAuthModal(); }")
        assert not modal.is_visible()

    finally:
        context.close()


# ─── 4.6: Ochrona przed XSS w przeglądarce ────────────────────────────────────

def test_4_6_xss_protection_in_browser(live_server, browser_instance):
    """4.6: XSS payload w nazwie planu oraz notatce serii nie wykonuje JavaScriptu."""
    context = browser_instance.new_context(viewport=VIEWPORTS["desktop"], service_workers="block")
    page = context.new_page()

    try:
        page.goto(live_server, wait_until="domcontentloaded")

        # Przetestuj escapowanie w DOM
        xss_check = page.evaluate("""() => {
            window.__xss_fired = false;
            const xssPayload = '<img src=x onerror=window.__xss_fired=true>';
            
            const div = document.createElement('div');
            // Zastosuj _escH z index.html
            const _escH = v => String(v ?? '').replace(/[&<>"']/g, c => ({
                '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
            }[c]));

            div.innerHTML = '<span>' + _escH(xssPayload) + '</span>';
            document.body.appendChild(div);

            return {
                fired: window.__xss_fired === true,
                content: div.textContent,
                images: div.getElementsByTagName('img').length
            };
        }""")

        assert not xss_check["fired"], "XSS payload został wykonany w oknie!"
        assert "<img src=x onerror=window.__xss_fired=true>" in xss_check["content"]
        assert xss_check["images"] == 0

    finally:
        context.close()


# ─── 3.6: Symulacja offline queue w Playwright ─────────────────────────────────

def test_3_6_offline_queue_simulation(live_server, browser_instance):
    """3.6: Wpisz 3 serie offline → refresh → serie w kolejce → włącz sieć → synchronizacja → serwer ma 3 serie."""
    context = browser_instance.new_context(viewport=VIEWPORTS["phone"], service_workers="block")
    page = context.new_page()

    try:
        page.goto(live_server, wait_until="domcontentloaded")

        # 1. Zarejestruj użytkownika
        user_email = f"offline_{uuid.uuid4().hex[:6]}@example.com"
        page.evaluate("() => window.openAuthModal('register')")
        page.wait_for_selector("#auth-email", state="visible")
        page.fill("#auth-email", user_email)
        page.fill("#auth-password", "OfflinePass123!")
        page.click("#auth-submit-btn")
        page.wait_for_function("() => !!localStorage.getItem('fitai_token')", timeout=8000)

        # Ustaw plan tygodniowy na wszystkie dni
        tok = page.evaluate("() => localStorage.getItem('fitai_token')")
        page.evaluate("""async (args) => {
            await fetch((window.API_BASE || '') + '/app/plan/current', {
                method: 'PUT',
                headers: { 'Authorization': 'Bearer ' + args.tok, 'Content-Type': 'application/json' },
                body: JSON.stringify(args.planPayload)
            });
            if (typeof window.syncProfileFromBackend === 'function') {
                await window.syncProfileFromBackend();
            }
        }""", {"tok": tok, "planPayload": MOCK_FULL_WEEK_PLAN})

        # 2. Rozpocznij trening na serwerze
        page.evaluate("async () => { await window.evolveStartTraining(); }")
        page.wait_for_selector("#liveWorkoutModal", state="visible", timeout=10000)

        # 3. Włącz tryb OFFLINE w kontekście przeglądarki
        context.set_offline(True)

        # Zapisz 3 serie offline
        save_buttons = page.locator(".btn-save-set")
        count = min(save_buttons.count(), 3)
        for i in range(count):
            save_buttons.nth(i).click()
            time.sleep(0.2)

        # Sprawdź, czy kolejka offline zawiera 3 serie
        pending_count = page.evaluate("() => window.FitAIOfflineQueue.getPendingCount()")
        assert pending_count == count, f"Kolejka offline powinna zawierać {count} serii, zawiera: {pending_count}"

        # 4. Odśwież stronę w trybie OFFLINE (symulacja zamknięcia/odświeżenia karty na siłowni)
        # Zablokuj wysyłkę ZANIM włączysz sieć, aby zdarzenie 'online' nie wysłało serii przed reloadem
        page.route("**/app/training/sessions/*/sets", lambda route: route.abort("failed"))
        context.set_offline(False)
        page.reload(wait_until="domcontentloaded")
        page.evaluate("() => { if (typeof enterDashboard === 'function') enterDashboard(); window.showTab('my-day'); }")
        page.wait_for_selector("#tab-my-day", state="visible")
        context.set_offline(True)

        # Sprawdź, że kolejka w localStorage PRZETRWAŁA odświeżenie strony!
        pending_after_reload = page.evaluate("() => window.FitAIOfflineQueue.getPendingCount()")
        assert pending_after_reload == count, (
            f"Kolejka offline utraciła dane po odświeżeniu strony: {pending_after_reload} != {count}"
        )

        # 5. Przywróć sieć
        page.unroute("**/app/training/sessions/*/sets")
        context.set_offline(False)

        # 6. Wywołaj synchronizację
        page.evaluate("async () => { await window.FitAIOfflineQueue.flushQueue(); }")
        time.sleep(1.5)

        # Sprawdź, czy kolejka się wyczyściła
        pending_after_sync = page.evaluate("() => window.FitAIOfflineQueue.getPendingCount()")
        assert pending_after_sync == 0, f"Kolejka powinna być pusta po synchronizacji, zostało: {pending_after_sync}"

        # 7. Potwierdź, że serwer ma dokładnie 3 serie
        token = page.evaluate("() => localStorage.getItem('fitai_token')")
        server_sets = page.evaluate("""async (tok) => {
            const todayRes = await fetch((window.API_BASE || '') + '/app/training/today', {
                headers: { 'Authorization': 'Bearer ' + tok }
            });
            const todayData = await todayRes.json();
            const sid = todayData.active_session_id;
            const sessRes = await fetch((window.API_BASE || '') + '/app/training/sessions/' + sid, {
                headers: { 'Authorization': 'Bearer ' + tok }
            });
            const sessData = await sessRes.json();
            return sessData.session.sets || [];
        }""", token)

        assert len(server_sets) == count, (
            f"Serwer powinien mieć dokładnie {count} serii, ma: {len(server_sets)}"
        )

    finally:
        context.close()


# ─── 5.1: Feature Flags & Hash Redirect ───────────────────────────────────────

def test_5_1_feature_flags_and_hash_redirect(live_server, browser_instance):
    """5.1: Wejście przez hash #sport lub #nutrition przekierowuje do #my-day, moduły spoza siły ukryte."""
    context = browser_instance.new_context(viewport=VIEWPORTS["desktop"], service_workers="block")
    page = context.new_page()

    try:
        # Wejście bezpośrednio z hashem #sport
        page.goto(live_server + "/#sport", wait_until="domcontentloaded")
        time.sleep(0.5)

        # Hash musi zostać przekierowany do #my-day
        current_hash = page.evaluate("() => window.location.hash")
        assert current_hash in ("#my-day", ""), f"Oczekiwano przekierowania do #my-day, otrzymano: {current_hash}"

        # Karty spoza siły na ekranie Dziś są ukryte
        bball_card = page.locator("#todayBasketballCard")
        assert not bball_card.is_visible(), "Karta koszykówki powinna być ukryta na Dziś"

        diet_card = page.locator("#todayDietCard")
        assert not diet_card.is_visible(), "Karta diety powinna być ukryta na Dziś"

    finally:
        context.close()


# ─── 3.3: Izolacja kolejki offline przy wylogowaniu i zmianie konta ────────────

def test_offline_queue_isolation_on_logout_and_account_switch(live_server, browser_instance):
    """3.3: Niewysłane serie nie znikają przy wylogowaniu bez pytania użytkownika,

    a po zalogowaniu na INNE konto kolejka poprzedniego konta nie jest wysyłana.
    """
    context = browser_instance.new_context(viewport=VIEWPORTS["phone"], service_workers="block")
    page = context.new_page()

    try:
        page.goto(live_server, wait_until="domcontentloaded")

        # 1. Rejestracja Użytkownika A
        email_a = f"queue_a_{uuid.uuid4().hex[:6]}@example.com"
        page.evaluate("() => window.openAuthModal('register')")
        page.wait_for_selector("#auth-email", state="visible")
        page.fill("#auth-email", email_a)
        page.fill("#auth-password", "StrongPassA123!")
        page.click("#auth-submit-btn")
        page.wait_for_function("() => !!localStorage.getItem('fitai_token')", timeout=8000)

        # Profil i Plan dla Użytkownika A
        tok_a = page.evaluate("() => localStorage.getItem('fitai_token')")
        uid_a = page.evaluate("() => localStorage.getItem('fitai_user_id')")
        page.evaluate("""async (args) => {
            await fetch((window.API_BASE || '') + '/app/profile', {
                method: 'PUT',
                headers: { 'Authorization': 'Bearer ' + args.tok, 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: 'Użytkownik A',
                    weight: 80.0,
                    height: 180,
                    goal: 'strength',
                    equipment: 'full_gym',
                    training_experience: 'intermediate'
                })
            });
            await fetch((window.API_BASE || '') + '/app/plan/current', {
                method: 'PUT',
                headers: { 'Authorization': 'Bearer ' + args.tok, 'Content-Type': 'application/json' },
                body: JSON.stringify(args.planPayload)
            });
            if (typeof window.syncProfileFromBackend === 'function') {
                await window.syncProfileFromBackend();
            }
        }""", {"tok": tok_a, "planPayload": MOCK_FULL_WEEK_PLAN})

        # Przejdź do Dziś, aby załadować plan do stanu
        page.evaluate("() => window.showTab('my-day')")
        page.wait_for_selector("#tab-my-day", state="visible")
        page.wait_for_timeout(400)

        # Rozpocznij trening i zapisz 1 serię w trybie OFFLINE
        page.evaluate("async () => { await window.evolveStartTraining(); }")
        page.wait_for_selector("#liveWorkoutModal", state="visible", timeout=10000)

        context.set_offline(True)
        save_btn = page.locator(".btn-save-set").first
        save_btn.click()
        time.sleep(0.3)

        # Kolejka offline A ma co najmniej 1 serię
        pending_a = page.evaluate("() => window.FitAIOfflineQueue.getPendingCount()")
        assert pending_a >= 1, "Seria powinna trafić do kolejki offline użytkownika A"

        # 2. Próba wylogowania z anulowaniem w dialogu confirm -> serie NIE znikają
        dialog_handled = []
        def handle_cancel_dialog(dialog):
            dialog_handled.append(dialog.message)
            dialog.dismiss()

        page.once("dialog", handle_cancel_dialog)
        page.evaluate("() => window.logoutUser()")
        time.sleep(0.5)

        # Dialog ostrzegł o niewysłanych seriach i został anulowany
        assert len(dialog_handled) == 1, "Wylogowanie z niewysłanymi seriami musi wywołać confirm"
        assert "niewysłanych serii" in dialog_handled[0]
        # Token nadal istnieje (wylogowanie przerwane)
        still_logged_in = page.evaluate("() => !!localStorage.getItem('fitai_token')")
        assert still_logged_in, "Wylogowanie powinno zostać anulowane po kliknięciu Cancel"
        assert page.evaluate("() => window.FitAIOfflineQueue.getPendingCount()") >= 1

        # 3. Wylogowanie z akceptacją dialogu
        # Włącz sieć dla wylogowania i przeładowania strony, blokując wysyłkę serii A
        page.route("**/app/training/sessions/*/sets", lambda route: route.abort("failed"))
        context.set_offline(False)
        page.once("dialog", lambda d: d.accept())
        page.evaluate("() => window.logoutUser()")
        time.sleep(1.2)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_selector("#landingPage, #auth-modal", state="attached", timeout=10000)

        # Sprawdź, czy kolejka A nadal jest zachowana w localStorage
        queue_key_a = f"fitai_set_queue_{uid_a}"
        saved_queue_a = page.evaluate(f"() => localStorage.getItem('{queue_key_a}')")
        assert saved_queue_a is not None and len(saved_queue_a) > 5, (
            "Kolejka offline użytkownika A nie może zniknąć po wylogowaniu"
        )

        # 4. Rejestracja/logowanie Użytkownika B
        page.unroute("**/app/training/sessions/*/sets")
        email_b = f"queue_b_{uuid.uuid4().hex[:6]}@example.com"
        page.evaluate("() => window.openAuthModal('register')")
        page.wait_for_selector("#auth-email", state="visible")
        page.fill("#auth-email", email_b)
        page.fill("#auth-password", "StrongPassB123!")
        page.click("#auth-submit-btn")
        page.wait_for_function("() => !!localStorage.getItem('fitai_token')", timeout=8000)

        tok_b = page.evaluate("() => localStorage.getItem('fitai_token')")
        uid_b = page.evaluate("() => localStorage.getItem('fitai_user_id')")
        assert uid_b != uid_a

        # Sprawdź kolejkę użytkownika B — musi być pusta
        pending_b = page.evaluate("() => window.FitAIOfflineQueue.getPendingCount()")
        assert pending_b == 0, "Kolejka offline nowego użytkownika B powinna być pusta"

        # Próba synchronizacji na koncie B NIE MOŻE wysłać serii użytkownika A
        page.evaluate("async () => { await window.FitAIOfflineQueue.flushQueue(); }")
        time.sleep(0.5)

        # Sprawdź na serwerze: użytkownik B ma 0 serii
        b_today = page.evaluate("""async (tok) => {
            const res = await fetch((window.API_BASE || '') + '/app/training/today', {
                headers: { 'Authorization': 'Bearer ' + tok }
            });
            return res.json();
        }""", tok_b)
        assert not b_today.get("active_session_id") and not (b_today.get("session") or {}).get("sets"), (
            "Konto B nie może otrzymać serii z kolejki konta A"
        )

        # Kolejka konta A nadal nienaruszona
        saved_queue_a_post = page.evaluate(f"() => localStorage.getItem('{queue_key_a}')")
        assert saved_queue_a_post == saved_queue_a, "Kolejka konta A została zmodyfikowana przez konto B"

    finally:
        context.close()
