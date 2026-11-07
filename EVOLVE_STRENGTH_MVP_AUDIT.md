# EVOLVE — AUDYT ŚCIEŻKI SIŁOWEJ (ETAP 0)

**Data audytu:** 2026-11-07  
**Gałąź:** `feat/strength-mvp`  
**Środowisko testowe:** Python 3.14.3, pytest 9.0.3, Playwright 1.64.1 (Chromium v1248 headless)  
**Cel:** Kompletna, empiryczna weryfikacja stanu ścieżki treningu siłowego, bezpieczeństwa, trwałości danych oraz responsywności UI na urządzeniach mobilnych, tabletach i komputerach.

---

## 1. WYNIKI URUCHOMIENIA PEŁNEGO ZESTAWU TESTÓW (CI REGRESSION)

Uruchomiono pełny zestaw testów z `.github/workflows/tests.yml` (job `current-regression`):
```bash
.venv\Scripts\python.exe -m pytest -q test_training_execution.py test_training_ui.py test_assessment_ui.py test_training_set_validation.py test_training_today.py test_core_foundation.py test_core_planning_contract.py test_frontend_hosting.py test_goals.py test_goals_api.py test_nutrition_foundation.py test_training_result_provenance.py test_pre_stage6_audit.py test_stage0_5_cross_user_isolation.py test_stage5_final_integration.py test_recovery_response.py test_plan_performance_signals.py test_training_evaluation.py test_training_evaluation_api.py test_training_adaptation.py test_training_next_effective_plan.py test_training_adaptive_audit.py tests/test_goal_training_state.py test_goal_training_state_api.py tests/test_decision_engine.py tests/test_decision_training_integration.py tests/test_decision_api.py tests/test_today.py tests/test_today_api.py tests/test_training_history.py tests/test_training_progress.py tests/test_progress_explanation.py tests/test_progress_routes.py tests/test_progress_hostile.py tests/test_progress_explanation_hostile.py tests/test_plan_progress_integration.py tests/test_plan_rolling.py test_database_config.py test_database_init.py test_migrate_sqlite_to_postgres.py
```

### Wynik zestawu:
- **Łącznie testów:** 398
- **Zaliczone (PASSED):** 382
- **Niepowodzenia (FAILED):** 12
- **Pominięte (SKIPPED):** 4
- **Ostrzeżenia (WARNINGS):** 292
- **Czas wykonania:** 52.07s

### Szczegółowa lista niepowodzeń (12 błędów bazowych):
1. `test_pre_stage6_audit.py::test_migration_chain_has_single_head_after_stage_18_availability`:
   - *Błąd:* `AssertionError: ['evolve31authhardening'] != ['evolve25userkey']`
   - *Przyczyna:* Test ma zahardkodowany stary head migracji Alembic.
2. `test_pre_stage6_audit.py::test_no_duplicate_http_method_and_path_routes_are_registered`:
   - *Błąd:* `AssertionError: Duplicate FastAPI routes registered: [('POST', '/app/goals'), ('GET', '/app/stats')]`
   - *Przyczyna:* Zduplikowane deklaracje endpointów w `app/goals/routes.py` vs `app/fitness/routes.py` oraz `app/legacy_routes.py`.
3. `test_pre_stage6_audit.py::test_stage_0_5_api_route_contracts_are_declared_and_auth_scoped`:
   - *Błąd:* `AssertionError: Missing auth dependency: app.plan.routes /app/plan/equipment-catalog`
   - *Przyczyna:* Endpoint `/app/plan/equipment-catalog` nie ma wstrzykniętej zależności autoryzacji `get_current_user`.
4. `tests/test_plan_progress_integration.py::test_progress_evidence_prioritizes_continuity_without_adaptation`:
   - *Błąd:* `AttributeError: 'types.SimpleNamespace' object has no attribute 'training_locations_json'` w `app/plan/deterministic.py:142`.
5. `tests/test_plan_progress_integration.py::test_insufficient_or_missing_progress_does_not_change_base_order`:
   - *Błąd:* `AttributeError: 'types.SimpleNamespace' object has no attribute 'training_locations_json'`.
6. `tests/test_plan_progress_integration.py::test_progress_cannot_inject_adaptation_or_recovery_decisions`:
   - *Błąd:* `AttributeError: 'types.SimpleNamespace' object has no attribute 'training_locations_json'`.
7. `tests/test_plan_progress_integration.py::test_progress_aware_planner_is_deterministic_for_identical_inputs`:
   - *Błąd:* `AttributeError: 'types.SimpleNamespace' object has no attribute 'training_locations_json'`.
8. `test_database_config.py::test_production_with_postgres_url_is_accepted`:
   - *Błąd:* `SystemExit: 1` z `KRYTYCZNY BŁĄD: CRON_SECRET nie jest ustawiony w produkcji!` w `app/config.py:92`.
9. `test_database_config.py::test_production_with_postgresql_url_is_accepted`:
   - *Błąd:* `SystemExit: 1` z powodu brakującego `CRON_SECRET` w teście.
10. `test_database_config.py::test_production_with_explicit_psycopg2_driver_is_accepted`:
    - *Błąd:* `SystemExit: 1` z powodu brakującego `CRON_SECRET` w teście.
11. `test_migrate_sqlite_to_postgres.py::test_foreign_keys_are_derived_from_model_metadata`:
    - *Błąd:* `AssertionError: Extra items in the left set: 'refresh_tokens', 'sport_attempts'`.
12. `test_migrate_sqlite_to_postgres.py::test_import_order_satisfies_all_model_foreign_keys`:
    - *Błąd:* `AssertionError` przy kolejności tabel migracyjnych (dodatkowe tabele `refresh_tokens`, `user_number_sequence`).

---

## 2. AUDYT ŚCIEŻKI SIŁOWEJ KROK PO KROKU

### KROK 1: Rejestracja i logowanie (Auth)
- **Endpointy:** `POST /auth/register`, `POST /auth/token`, `POST /auth/login`, `GET /auth/me`, `POST /auth/refresh-access`, `POST /auth/logout`, `GET /auth/demo-token` (krytyczna luka), `POST /auth/demo-login`.
- **Tabele DB:** `users` (`UserDB`), `user_number_sequence` (`UserNumberSequenceDB`), `refresh_tokens` (`RefreshTokenDB`).
- **Funkcje frontendu (`index.html`):** `handleRegister()`, `handleLogin()`, `logoutUser()`, `checkAuth()`.
- **Istniejące testy:** `test_auth_account_hardening.py`, `test_core_foundation.py`.
- **Zidentyfikowane luki i błędy:**
  1. **CRITICAL BUG (Desynchronizacja sekwencji rejestracji):** W `app/database.py:98-116` funkcja `_ensure_legacy_sqlite_columns` próbuje synchronizować `user_number_sequence` dla starych kont. Przy napotkaniu `demo@evolve.app` o zahardkodowanym `user_number=999999` rzuca `sqlite3.IntegrityError: UNIQUE constraint failed: user_number_sequence.id`. Transakcja pada, a sekwencja zatrzymuje się na `1000219`, podczas gdy tabela `users` ma już rekordy do `1000240`. Skutek: **każda nowa rejestracja rzuca HTTP 500 (`IntegrityError: UNIQUE constraint failed: users.user_key`)**.
  2. **CRITICAL SECURITY (Demo login bypass):** `GET /auth/demo-token` i `POST /auth/demo-login` w trybie braku użytkownika demo pobierają `select(UserDB).first()` (czyli pierwszego prawdziwego użytkownika w bazie) i wydają na niego pełny token JWT z uprawnieniami właściciela.
  3. **Brak walidacji biometrycznej:** Rejestracja przyjmuje dowolne, w tym ujemne lub zerowe wartości wieku, wzrostu i wagi, a w przypadku ich braku cicho zgaduje parametry (25 lat, 170 cm, 70 kg) i błędnie liczy cele kaloryczne.
  4. **Brak unieważniania tokenów po zmianie hasła:** Brak mechanizmu `token_version` weryfikowanego przy każdym zapytaniu.
  5. **Brak opcji „wyloguj wszędzie” w UI** oraz brak widocznego formularza resetu hasła jednorazowym tokenem.

---

### KROK 2: Profil i ocena początkowa (Baseline)
- **Endpointy:** `GET /app/profile`, `PUT /app/profile`, `GET /app/assessment`, `POST /app/assessment`, `GET /app/assessment/latest`.
- **Tabele DB:** `users`, `assessments` (`AssessmentDB`).
- **Funkcje frontendu (`index.html`):** `loadEvolveAssessment()`, `generatePlanFromAssessment()`, `loadProfile()`, `saveProfile()`.
- **Istniejące testy:** `test_assessment_ui.py`.
- **Zidentyfikowane luki i błędy:**
  1. Brak zabezpieczenia przed deficytem kalorycznym dla osób niepełnoletnich: `calc_calories` dla celu `redukcja` odejmuje 400 kcal nawet dla użytkowników w wieku < 18 lat.
  2. Brak limitów rozmiaru payloadu w `PUT /app/profile` (możliwość przesłania gigantycznych obiektów JSON).
  3. Pola liczbowe w profilu na telefonie nie wymuszają numerycznej klawiatury (`inputmode="numeric"` / `inputmode="decimal"`).

---

### KROK 3: Kreator planu (Inteligentny i Indywidualny)
- **Endpointy:** `GET /app/plan/current`, `PUT /app/plan/current`, `POST /app/plan/generate`, `POST /app/plan/swap`, `GET /app/plan/equipment-catalog`, `GET /app/plan/availability`, `PUT /app/plan/availability`, `GET /app/plan/rolling`.
- **Tabele DB:** `users` (kolumny `weekly_plan_json`, `training_locations_json`, `training_availability_json`).
- **Funkcje frontendu (`index.html`):** `generatePlanFromAssessment()`, `generatePlanAI()` (stara funkcja AI), `/app/plan/ui`.
- **Istniejące testy:** `test_core_planning_contract.py`, `test_plan_rolling.py`, `tests/test_plan_progress_integration.py`.
- **Zidentyfikowane luki i błędy:**
  1. `/app/plan/equipment-catalog` nie ma autoryzacji (fails w teście `test_pre_stage6_audit.py`).
  2. Kreator w `index.html` polega na starym `generatePlanAI()`, który odwołuje się do nieistniejących endpointów tekstowych AI, zamiast spójnego generatora deterministycznego.
  3. Brak widoku podglądu planu obok kreatora na dużym ekranie (komputer ≥ 1025 px).
  4. Brak edytora ręcznego (dodawanie/usuwanie ćwiczenia, modyfikacja serii/powtórzeń/RPE) bez niszczenia powiązanej historii treningowej.

---

### KROK 4: Plan na dziś (Today Hub & /app#my-day)
- **Endpointy:** `GET /app/today`, `GET /app/training/today`, `GET /app/decision/today`.
- **Tabele DB:** `users`, `training_sessions`, `training_set_results`, `daily_logs`.
- **Funkcje frontendu (`index.html`):** `loadEvolveTodayHub()`, `tab-my-day`, `injectMyDayShell()` w `app/__init__.py`.
- **Istniejące testy:** `test_training_today.py`, `tests/test_today.py`, `tests/test_today_api.py`.
- **Zidentyfikowane luki i błędy:**
  1. **BŁĄD STREFY CZASOWEJ:** W `app/training/routes.py:792` `get_training_today` używa `date.today()`, czyli czasu UTC serwera (Render). W godzinach wieczornych i wczesnoporannych użytkownik w Polsce (Europe/Warsaw) widzi zły dzień treningowy.
  2. **Brak stanu „zrobiony”:** `get_training_today` sprawdza tylko `status == 'active'`. Jeśli dzisiejsza sesja została zakończona (`status == 'completed'`), endpoint zwraca `can_start: true` i sugeruje rozpoczęcie nowego treningu zamiast czytelnego stanu „Dzisiejszy trening ukończony!”.
  3. Dzień wolny od treningu nie jest prezentowany jako czytelny, pełnoprawny stan odpoczynku i regeneracji.

---

### KROK 5: Aktywna sesja treningowa (Workout Execution)
- **Endpointy:** `POST /app/training/sessions/start`, `POST /app/training/sessions/{session_id}/sets`, `POST /app/training/sessions/{session_id}/complete`, `GET /app/training/session-ui`.
- **Tabele DB:** `training_sessions` (`TrainingSessionDB`), `training_set_results` (`TrainingSetResultDB`).
- **Funkcje frontendu (`index.html`):** `window.evolveStartTraining()`, `window.openLiveWorkoutModal(session)`.
- **Istniejące testy:** `test_training_execution.py`, `test_training_ui.py`, `test_training_set_validation.py`.
- **Zidentyfikowane luki i błędy:**
  1. **ZDUPLIKOWANA FUNKCJA:** `window.evolveStartTraining` jest zdefiniowana dwukrotnie w `index.html` (linia 33224 oraz linia 33819) z różnymi implementacjami!
  2. **Brak odporności na brak zasięgu (Offline queue):** Ani frontend, ani backend nie obsługują idempotencji opartej na `client_id` dla serii treningowych. Zerwanie połączenia w piwnicy siłowni powoduje błąd fetch i utratę serii.
  3. **Sztywna blokada liczby serii:** W `app/training/routes.py:1021` backend odrzuca serię, jeśli `set_number > planned_sets` (`HTTP 422: Numer serii wykracza poza zaplanowaną liczbę serii`). Użytkownik nie może wykonać dodatkowej serii w trakcie treningu!
  4. **Brak przycisku „Coś mnie boli”:** Brak możliwości bezpiecznej zamiany/pominięcia ćwiczenia w trakcie sesji z notatką.
  5. **Brak przycisków dodawania/usuwania serii w bieżącej sesji.**
  6. **Absurdalne limity walidacji:** `actual_weight_kg` dopuszcza do 10000 kg w `app/schemas.py:527`.

---

### KROK 6: Zakończenie sesji treningowej
- **Endpoint:** `POST /app/training/sessions/{session_id}/complete`.
- **Tabele DB:** `training_sessions`, `exercise_results` (`ExerciseResultDB`).
- **Funkcje frontendu (`index.html`):** `btnFinishWorkout` w `openLiveWorkoutModal`.
- **Istniejące testy:** `test_training_execution.py`.
- **Zidentyfikowane luki i błędy:**
  1. `complete_training_session` nie wylicza ani nie zwraca ustrukturyzowanego podsumowania sesji (łączna objętość w kg, czas trwania sesji, pobite rekordy ciężaru/1RM, liczba serii).
  2. Frontend po kliknięciu „Zakończ” po prostu zamyka modal, nie prezentując ekranu podsumowania wykonanej pracy.

---

### KROK 7: Historia i postępy (Siłowe)
- **Endpointy:** `GET /app/training/history`, `GET /app/progress/evidence/{exercise_key}`, `GET /app/stats`.
- **Tabele DB:** `exercise_results`, `training_sessions`, `training_set_results`.
- **Funkcje frontendu (`index.html`):** `loadHistory()`, `renderProgressCharts()`.
- **Istniejące testy:** `tests/test_training_history.py`, `tests/test_training_progress.py`.
- **Zidentyfikowane luki i błędy:**
  1. W `index.html` w zakładce Postępy wykresy są zdominowane przez metryki koszykarskie (skuteczność rzutów z 5 stref, wyskok) i wagę ciała, brakuje dedykowanego widoku siłowego: szacowane 1RM (np. wzór Brzyckiego / Epleya), objętość tygodniowa per partia mięśniowa oraz lista osobistych rekordów (PR).
  2. Brak oznaczenia „mało danych” dla ćwiczeń z historią poniżej 3 sesji.
  3. Na komputerze (≥ 1025 px) brak układu dwukolumnowego: lista sesji po lewej + podgląd szczegółów wybranej sesji po prawej.

---

## 3. AUDYT RESPONSYWNOŚCI (VIEWPORTY: 390×844, 820×1180, 1440×900)

Badanie przeprowadzono za pomocą Playwright Chromium w skrypcie `scratch/audit_responsiveness.py`.

### A. Telefon (390×844 px)
- **KRYTYCZNY BŁĄD NAWIGACJI:** `aside#sidebar` ma klasę `hidden md:flex`. Na ekranie telefonu (390 px) pasek boczny jest całkowicie ukryty. Jednocześnie w `#dashboardPage` **nie istnieje dolny pasek nawigacyjny ani menu hamburgerowe**! Zalogowany użytkownik na telefonie jest uwięziony na aktualnej zakładce i nie może przejść do Treningu, Planu, Postępów ani Profilu!
- **Elementy dotykowe < 44×44 px:**
  - `todayStartWorkoutBtn` ma wysokość zaledwie 36 px (powinno być min. 44 px).
  - Przycisk `mobileMenuBtn`: 38×38 px.
  - Przyciski nawigacji profilu i wylogowania: wysokość 16–34 px.
- **Przepełnienie poziome (Overflow):** Zidentyfikowano element rozszerzający się do 413 px przy szerokości okna 390 px (karty dashboardu ze stałymi marginesami).

### B. Tablet (820×1180 px)
- Pasek boczny pojawia się (breakpoint `md:` na 768 px), ale zajmuje 256 px, co na tablecie w układzie pionowym (820 px) pozostawia zaledwie 564 px na główny kontent, powodując ciasnotę i ucinanie etykiet w kartach metryk.
- Przyciski zapisu serii w modalach runnera mają małe targety dotykowe.

### C. Komputer (1440×900 px)
- Aktywna sesja treningowa oraz nagłówki dashboardu rozciągają się na pełną szerokość `main` bez `max-width`, co utrudnia czytanie i skupienie podczas treningu.
- Kreator planu oraz historia sesji nie wykorzystują dostępnej szerokości ekranu na układ dwukolumnowy (lista po lewej, podgląd/szczegóły po prawej).

---

## 4. ELEMENTY INTERFEJSU POZA ZAKRESEM MVP SIŁOWEGO (DO UKRYCIA FLAGĄ)

Zgodnie z wymaganiami, moduły te **nie mogą być usunięte z kodu**, lecz ukryte za flagą `STRENGTH_MVP_MODE = true`:

1. **Główna nawigacja sidebar:**
   - `🏀 2. Sport` (data-tab: `basketball`)
   - `🥗 4. Odżywianie` (data-tab: `diet`)
   - `🔋 5. Regeneracja` (data-tab: `recovery`)
   - Zduplikowany przycisk `← Strona główna` (wywołujący `exitDashboard()`).
2. **Karty na ekranie Dziś (`#tab-my-day`):**
   - Karta koszykówki (`🏀 Koszykówka & Motoryka`, Shot Tracker, Atlas Drilli, pasek 50 rzutów).
   - Karta diety (`🥗 Dieta na dziś`, spalone/spożyte kalorie, paski białko/węgle/tłuszcz).
   - Karta porannego check-inu regeneracji (5 suwaków zmęczenia/DOMS/snu).
3. **Zakładki aplikacji:**
   - `#tab-sport` / `#tab-basketball` (Shot Map, selektor stref boiska, katalog drillów koszykarskich).
   - `#tab-diet` (biblioteka przepisów, posiłki, skala makro).
   - `#tab-recovery` (wykresy snu, gotowości).
4. **Modale i funkcje poboczne:**
   - Modal Kuchni AI (`kuchniaAIModal`).
   - Skaner kodów kreskowych EAN-13 (`scannerModal`).
   - Przycisk i interfejs Voice Coach / asystenta AI.

---

## 5. PLIKI DUPLIKATÓW I ŚMIECIOWE DO USUNIĘCIA (ETAP 5)

1. **Kanoniczny plik:**
   - `index.html` w katalogu głównym (2 528 939 bajtów) — to ten plik jest serwowany przez `STATIC_DIR` w `app/__init__.py:1299`.
2. **Duplikaty do bezpiecznego usunięcia (po weryfikacji braku referencji):**
   - `app/index.html` (1 920 623 bajtów — nieużywana stara kopia).
   - `app/index_new.html` (1 918 579 bajtów — nieużywana stara kopia).
   - `original_app.html` (19 990 bajtów — archiwalny prototyp z kwietnia 2026).
   - `fitai_dashboard.html` (126 762 bajtów — używany wyłącznie jako fallback gdyby `index.html` był pusty; po weryfikacji można usunąć lub zostawić jako stub).
3. **Plik śmieciowy:**
   - `et --hard 473527c` w katalogu głównym (błędnie utworzony plik z polecenia gita).

---

## 6. BEZPIECZEŃSTWO I INFRASTRUKTURA (RENDER & BAZA DANYCH)

1. **CORS:** Domyślnie `*` z `allow_credentials=True` w `app/config.py:110` i `app/__init__.py:67` — w produkcji niedopuszczalne.
2. **Dokumentacja API:** `/docs`, `/redoc` i `/openapi.json` są otwarte w trybie produkcyjnym.
3. **Rate Limiter za proxy Rendera:** `_rate_limit_key` korzysta z `slowapi.util.get_remote_address(request)`, który zwraca `request.client.host`. Bez `--proxy-headers` uvicorn widzi wewnętrzne IP proxy Rendera, co oznacza, że wszyscy użytkownicy współdzielą jeden limit żądań!
4. **Konfiguracja `render.yaml`:**
   - Usługa nazywa się `fitai-api`.
   - Brak definicji bazy danych PostgreSQL.
   - Brak zmiennych `DATABASE_URL` i `CRON_SECRET` w konfiguracji envVars.
   - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT` bez `--proxy-headers`.

---

## PODSUMOWANIE AUDYTU
Ścieżka siłowa posiada solidne fundamenty backendowe (modele `TrainingSessionDB`, `TrainingSetResultDB`, silnik adaptacji deterministycznej), ale jest zablokowana przez:
1. Awarię rejestracji użytkowników (błąd unikalności sekwencji numeru konta).
2. Poważne luki bezpieczeństwa (demo token, CORS `*`, otwarte `/docs`, wspólne limity proxy).
3. Całkowity brak nawigacji w dashboardzie na telefonie (brak dolnego paska).
4. Brak odporności na brak sieci podczas sesji treningowej (brak kolejki offline i idempotencji `client_id`).
5. Przeładowanie interfejsu modułami koszykówki, diety i AI, które rozpraszają i zaciemniają ścieżkę siłową.

Wszystkie powyższe kwestie zostaną metodycznie naprawione w etapach 1–5 na gałęzi `feat/strength-mvp`.
