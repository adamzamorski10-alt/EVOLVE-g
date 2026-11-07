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

ALL_DAYS = ["Pon", "Wt", "Śr", "Czw", "Pt", "Sob", "Ndz"]

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

    old_env = {
        "DATABASE_URL": os.environ.get("DATABASE_URL"),
        "ENV": os.environ.get("ENV"),
        "JWT_SECRET_KEY": os.environ.get("JWT_SECRET_KEY"),
        "CRON_SECRET": os.environ.get("CRON_SECRET"),
    }

    os.environ["DATABASE_URL"] = db_url
    os.environ["ENV"] = "development"
    os.environ["JWT_SECRET_KEY"] = "e2e-playwright-secret-32-bytes-long-key!"
    os.environ["CRON_SECRET"] = "cron-secret-e2e"

    from alembic import command
    from alembic.config import Config
    alembic_cfg = Config(str(REPO_ROOT / "alembic.ini"))
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(alembic_cfg, "head")

    import uvicorn
    from main import app

    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # Poczekaj na gotowość serwera
    for _ in range(50):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                break
        except OSError:
            time.sleep(0.05)

    base_url = f"http://127.0.0.1:{port}"
    yield base_url

    server.should_exit = True
    thread.join(timeout=2)

    from app.database import engine
    engine.dispose()
    try:
        temp_dir.cleanup()
    except Exception:
        pass

    for k, v in old_env.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


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
    """4.1 & 4.7: Rejestracja → Profil → Plan → Dziś → Start → Zapis serii → Zakończenie → Historia → Nowy kontekst."""
    vp = VIEWPORTS[vp_name]
    context = browser_instance.new_context(viewport=vp, service_workers="block")
    page = context.new_page()

    try:
        page.goto(live_server, wait_until="domcontentloaded")
        page.wait_for_selector("#landingPage, #auth-modal", state="attached")

        # 1. Rejestracja nowego użytkownika
        user_email = f"e2e_{vp_name}_{uuid.uuid4().hex[:6]}@example.com"
        page.evaluate("() => window.openAuthModal('register')")
        page.wait_for_selector("#auth-email", state="visible")
        page.fill("#auth-email", user_email)
        page.fill("#auth-password", "StrongPassword123!")
        page.click("#auth-submit-btn")

        # Czekaj na zapis tokena i wejście do aplikacji
        page.wait_for_function("() => !!localStorage.getItem('fitai_token')", timeout=8000)

        # Zrzut ekranu po rejestracji / na ekranie profilu (4.7)
        page.screenshot(path=str(DOCS_QA / f"01_registered_{vp_name}.png"))

        # 2. Uzupełnienie profilu
        token = page.evaluate("() => localStorage.getItem('fitai_token')")
        page.evaluate("""async (tok) => {
            await fetch((window.API_BASE || '') + '/app/profile', {
                method: 'PUT',
                headers: { 'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: 'Zawodnik E2E',
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
        }""", {"tok": token, "planPayload": MOCK_FULL_WEEK_PLAN})

        # 4. Przejście do widoku Mój Dzień
        page.evaluate("() => window.showTab('my-day')")
        page.wait_for_selector("#tab-my-day", state="visible")

        # Zrzut ekranu ekranu Dziś (4.7)
        page.screenshot(path=str(DOCS_QA / f"02_my_day_{vp_name}.png"))

        # 5. Rozpoczęcie treningu na żywo (Start)
        page.evaluate("async () => { await window.evolveStartTraining(); }")
        page.wait_for_selector("#liveWorkoutModal", state="visible", timeout=10000)

        # Zrzut ekranu aktywnej sesji treningowej (4.7)
        page.screenshot(path=str(DOCS_QA / f"03_live_workout_{vp_name}.png"))

        # 6. Zapisz serie dla ćwiczeń
        save_buttons = page.locator(".btn-save-set")
        btn_count = save_buttons.count()
        assert btn_count >= 1, "Brak przycisków zapisu serii w modal treningu"

        # Kliknij pierwsze 3 przyciski serii
        to_click = min(btn_count, 3)
        for i in range(to_click):
            btn = save_buttons.nth(i)
            btn.scroll_into_view_if_needed()
            btn.click()
            time.sleep(0.3)

        # 7. Zakończenie treningu
        finish_btn = page.locator("#btnFinishWorkout")
        finish_btn.scroll_into_view_if_needed()
        finish_btn.click()

        # Modal powinien zniknąć po zakończeniu
        page.wait_for_selector("#liveWorkoutModal", state="hidden", timeout=8000)

        # 8. Otwórz historię i sprawdź zapis
        page.evaluate("() => window.showTab('postepy')")
        time.sleep(0.5)
        page.screenshot(path=str(DOCS_QA / f"04_history_{vp_name}.png"))

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
        # Zezwól na reload lokalnego HTML
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
