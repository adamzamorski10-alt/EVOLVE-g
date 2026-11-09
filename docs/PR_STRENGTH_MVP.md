# Pull Request: Strength MVP (EVOLVE v3.0)

**Branch docelowy:** `main`  
**Branch źródłowy:** `feat/strength-mvp`  
**Status:** Ready for Review (DO NOT MERGE AUTOMATICALLY)

---

## 1. Co zawiera gałąź (Podsumowanie zmian)

Gałąź `feat/strength-mvp` implementuje kompletny fundament silnika treningu siłowego (Strength MVP) w architekturze Tech Noir dla EVOLVE, usuwa podatności bezpieczeństwa, stabilizuje CI na Linuxie oraz dodaje pełny pakiet testów przeglądarkowych Playwright na 3 viewportach (telefon, tablet, komputer).

### Główne funkcjonalności i ulepszenia:
1. **Live Workout Runner & Offline Queue:**
   - Zapis serii na żywo z obsługą przerw (`startRestTimer` domyślnie 90s, zmienialny, +30s, pomiń).
   - Pełna odporność na brak sieci na siłowni: lokalna kolejka `FitAIOfflineQueue` w `localStorage` z `client_id` (UUIDv4) gwarantująca idempotencję i brak duplikatów przy ponawianiu.
   - Izolacja kolejek per użytkownik (`fitai_set_queue_<user_id>`) zapobiegająca przeciekowi serii między kontami na tym samym urządzeniu.
   - Paski postępu sesji i walidacja danych wejściowych (`inputmode="decimal"` dla kg, `numeric` dla powtórzeń/RPE, powiększone pole ciężaru mieszczące min. 6 znaków).
2. **Bezpieczeństwo & Fail-Closed Configuration:**
   - Domyślny tryb fail-closed w produkcji (`ENV=production`): blokada startu na SQLite, wymóg PostgreSQL, wyłączenie endpointów Swagger (`/docs`, `/redoc`), trwałe usunięcie endpointów demo (`/auth/demo-token` i `/auth/demo-login` zwracają 404).
   - Całkowite usunięcie skryptu `evolve-auto-auth` oraz automatycznego logowania — każdy użytkownik zakłada i używa własnego konta.
   - Narzędzie administracyjne `scripts/reset_shared_demo_account.py` do bezpiecznej obsługi konta #01.
   - Ochrona rate-limiting (SlowAPI): rate limits na `/auth/register` (5/godz), `/auth/login` (10/min), z bezpieczną detekcją IP przez reverse proxy i flagą `RATE_LIMIT_ENABLED` dla środowisk testowych.
   - Ochrona przed XSS: bezpieczne renderowanie nazw ćwiczeń, planów i notatek w UI bez podatności na wstrzyknięcie kodu HTML/JS.
3. **Spójność UX & Nawigacja:**
   - Usunięto prefiksy numeryczne z nawigacji bocznej na desktopie (czyste nazwy: Dziś, Plan, Trening, Postępy, Profil).
   - Ukryto moduły spoza MVP siłowego (`#sport`, `#nutrition`, `#recovery`, `assessment`) pod flagą `FEATURE_FLAGS` z przekierowaniem do Dziś.
   - Uporządkowano nagłówek (brak nachodzenia numeru użytkownika `#01` na nazwę, ukrywanie marketingowych linków landing page po zalogowaniu).
   - Wskaźniki „Twój fundament": obliczanie kalorii i makro tylko na podstawie kompletnych danych użytkownika (brak zgadywania biometrii, brak danych = `—`).
4. **Zielone CI & Pełny pakiet testów:**
   - Weryfikacja PostgreSQL i SQLite, migracje Alembic, integralność indeksów częściowych (`uq_training_active_user_day`).
   - Pełny zestaw E2E Playwright: 13 testów sprawdzających layout, dotyk (min. 44x44px), brak scrolla poziomego, obsługę klawiaturą, synchronizację cross-device, przełączanie kont i symulację offline.

---

## 2. Zmiany w Schemacie Bazy Danych i Migracje Alembic

Migracje w gałęzi `feat/strength-mvp` rozszerzają schemat o idempotencję serii oraz utwardzenie uwierzytelniania:

1. **`evolve30restorelegacyfields`**: Przywrócenie pól logów dziennych wymaganych przez legacy API.
2. **`evolve31authhardening`**:
   - `token_version` (INT, default 1) w tabeli `users` umożliwiający natychmiastowe unieważnienie sesji przy zmianie hasła lub wylogowaniu.
   - Tabela `refresh_tokens` do bezpiecznej rotacji sesji.
   - Tabela `password_resets` do bezpiecznego resetowania hasła z tokenami o ograniczonym czasie ważności.
   - `users.email` jako jawny indeks unikalny (`uq_users_email`).
   - Pola biometryczne nullable (wsparcie rejestracji minimalistycznej sam email + hasło bez wymuszonej biometrii).
3. **`evolve32trainingsetclientid`** (HEAD):
   - Kolumna `client_id` (VARCHAR(64), nullable, indexed) w tabeli `training_set_results`.
   - Zapewnia idempotencję zapisu serii w Live Workout Runner — serwer deduplikuje powtórzone pakiety z kolejki offline na podstawie `client_id`.

**Kolejność uruchamiania migracji:**
```bash
python -m alembic upgrade head
```

---

## 3. Ryzyka przy Wdrożeniu

| Ryzyko | Poziom | Środki mitygujące |
|---|---|---|
| Baza SQLite na produkcji | Wysokie | Aplikacja w trybie `ENV=production` sprawdza URL bazy i kończy proces z błędem w razie wykrycia SQLite. Należy upewnić się, że `DATABASE_URL` w Render/produkcji wskazuje na PostgreSQL. |
| Brakujące zmienne środowiskowe (`JWT_SECRET_KEY`, `CRON_SECRET`, `CORS_ORIGINS`) | Wysokie | Start aplikacji jest fail-closed — proces nie wystartuje bez wymaganych zmiennych. Zmienne muszą być skonfigurowane w panelu hostingu przed startem. |
| Wygaśnięcie instancji PostgreSQL (darmowy tier Render) | Średnie | Darmowe bazy PostgreSQL na Render wygasają po 30 dniach. Produkcja musi korzystać ze stabilnego planu z włączonymi backupami. |
| Niezsynchronizowane serie offline u użytkowników | Niskie | Kolejka `FitAIOfflineQueue` jest trwała w `localStorage` per użytkownik i automatycznie wznawia synchronizację po wykryciu połączenia online. |

---

## 4. Procedura Wycofania (Rollback)

W przypadku problemów po wdrożeniu:

### Krok 1: Wycofanie kodu aplikacji
Przełączenie serwisu na poprzedni stabilny commit lub obraz kontenera:
```bash
git checkout main
# lub w panelu Render: 'Rollback to previous deploy'
```

### Krok 2: Wycofanie migracji bazy danych
Jeśli nowa wersja bazy nie jest kompatybilna z poprzednim kodem:
```bash
# Cofnięcie migracji do stanu sprzed gałęzi feat/strength-mvp:
python -m alembic downgrade evolve29sportattempts
```

### Krok 3: Odtworzenie bazy ze zrzutu (w razie awarii krytycznej)
```bash
pg_restore -h <HOST> -U <USER> -d <DATABASE> -v --clean --if-exists <PRE_DEPLOY_BACKUP>.dump
```

