# EVOLVE — Production Deployment Checklist

Niniejszy dokument stanowi oficjalną listę kontrolną wdrożenia produkcyjnego systemu EVOLVE (gałąź `feat/strength-mvp`).

---

## 1. Wymagane Zmienne Środowiskowe (Produkcja)

W środowisku produkcyjnym aplikacja działa w trybie **fail-closed** (`get_env() == "production"`). Brak lub niepoprawność poniższych zmiennych skutkuje natychmiastowym przerwaniem procesu (`sys.exit(1)`):

| Zmienna | Wymóg | Opis / Zachowanie |
|---|---|---|
| `ENV` | `production` | Wymusza wyłączenie dokumentacji Swagger (`/docs`, `/redoc`), wyłączenie demo tokenów, rygorystyczny CORS i blokadę bazy SQLite. |
| `DATABASE_URL` | `postgresql+psycopg://...` | Musi wskazywać na bazę PostgreSQL (np. Render PostgreSQL). SQLite w produkcji jest bezwzględnie odrzucane. Schemat normalizowany automatycznie do psycopg. |
| `JWT_SECRET_KEY` | Min. 32 znaki / 256-bit hex | Tajny klucz do podpisywania tokenów JWT (HS256). W produkcji brak klucza blokuje start aplikacji (brak fallbacku losowego). |
| `CRON_SECRET` | Min. 16 znaków | Sekret autoryzacji zadań cyklicznych (endpointy cron / background worker). W produkcji brak klucza blokuje start. |
| `CORS_ORIGINS` | Dokładny adres URL (np. `https://evolve.onrender.com`) | W produkcji nie może być puste ani `*`. Musi zawierać domenę frontendu. |

---

## 2. Flagi Pomocnicze i Bezpieczeństwo

### Całkowite Usunięcie Demo-Loginu (Iteracja 5)
- Endpointy `/auth/demo-token` i `/auth/demo-login` oraz mechanizm automatycznego logowania `evolve-auto-auth` zostały **trwale i bezwarunkowo usunięte** z backendu oraz frontendu.
- Flaga `ALLOW_DEMO_LOGIN` została wycofana z konfiguracji. Aplikacja nie posiada kont współdzielonych ani demo.
- Sprawdzenie: żądanie do `/auth/demo-token` lub `/auth/demo-login` w każdym środowisku zwraca standardowy kod **404 Not Found**.

### `LOG_RESET_TOKENS`
- **Domyślnie:** `false`.
- **Działanie:** Jeśli `true`, tokeny resetowania hasła są wypisywane w logach serwera (używane wyłącznie lokalnie w celach deweloperskich/diagnostycznych, gdy serwer SMTP nie jest podłączony).
- **W produkcji:** Musi być ustawione na `false` (lub pominięte). Tokeny resetu muszą trafiać wyłącznie na e-mail użytkownika.

### `RATE_LIMIT_ENABLED`
- **Domyślnie:** `true`.
- **Działanie:** Aktywuje ochronę przed brute-force przez SlowAPI (`5/hour` na rejestrację i reset hasła, `10/min` na logowanie). W testach E2E/lokalnych może być ustawione na `false`.

---

## 3. Postępowanie z Kontem #01 i Rotacja Kluczy Po Wdrożeniu

### KROK 1: Kopia zapasowa bazy danych PRZED wdrożeniem
Przed rozpoczęciem deployu należy wykonać pełny zrzut bazy produkcyjnej:
```bash
python scripts/backup_postgres.py --output backups/pre_iteration5_backup.sql
```

### KROK 2: Rotacja `JWT_SECRET_KEY` (KRYTYCZNE)
Ze względu na to, że w starszych wersjach token konta #01 mógł wyciec do przeglądarek przez automatyczne wstrzykiwanie w HTML, po wdrożeniu należy **natychmiast zrotować klucz JWT**:
1. Wygeneruj nowy, kryptograficznie bezpieczny klucz 32-bajtowy:
   ```bash
   openssl rand -hex 32
   ```
2. Zaktualizuj zmienną środowiskową `JWT_SECRET_KEY` w panelu Render (Environment).
3. Zrestartuj usługę — rotacja klucza natychmiast unieważni wszystkie wcześniej wygenerowane tokeny JWT (żaden stary token nie zadziała).

### KROK 3: Założenie własnego konta właściciela
1. Otwórz stronę produkcyjną w przeglądarce.
2. Zarejestruj własne, dedykowane konto właściciela za pomocą formularza rejestracji (`POST /auth/register`).
3. Uzupełnij profil i wygeneruj spersonalizowany plan siłowy.

### KROK 4: Decyzja i obsługa konta #01 (Współdzielone konto demo)
Konto #01 mogło zawierać przypadkowe serie treningowe wprowadzone przez odwiedzających.
Aby zabezpieczyć lub wyczyścić konto #01, uruchom z linii poleceń skrypt administracyjny:
```bash
# 1. Podgląd powiązanych rekordów (tryb bezpieczny dry-run):
python scripts/reset_shared_demo_account.py --email shared01@example.com --dry-run
# lub po numerze:
python scripts/reset_shared_demo_account.py --user-number 1 --dry-run

# 2. Opcja A: Zerowanie danych treningowych i ustawienie nowego hasła:
python scripts/reset_shared_demo_account.py --email shared01@example.com --reset-data --password "NoweSilneHaslo123!" --execute

# 2. Opcja B: Usunięcie kaskadowe konta #01:
python scripts/reset_shared_demo_account.py --email shared01@example.com --cascade-delete --execute
```

### KROK 5: Procedura wycofania (Rollback)
W razie konieczności wycofania zmian:
1. Przywróć poprzedni commit w repozytorium na gałęzi produkcyjnej.
2. W razie potrzeby przywróć bazę z backupu:
   ```bash
   psql "$DATABASE_URL" < backups/pre_iteration5_backup.sql
   ```
3. Przywróć poprzedni `JWT_SECRET_KEY` (jeśli zachodzi konieczność podtrzymania sesji).

---

## 3. Procedura Backup i Przywracania Bazy Danych

### Backup PostgreSQL (Render / Zewnętrzny serwer)
```bash
# Wykonanie zrzutu bazy do skompresowanego pliku
pg_dump -h <HOST> -U <USER> -d <DATABASE> -F c -b -v -f evolve_backup_$(date +%Y%m%d_%H%M%S).dump
```

### Przywracanie bazy (Restore)
```bash
# Odtworzenie bazy ze zrzutu
pg_restore -h <HOST> -U <USER> -d <DATABASE> -v --clean --if-exists evolve_backup_YYYYMMDD_HHMMSS.dump
```

### Migracja ze SQLite do PostgreSQL
Jeśli zachodzi potrzeba migracji z dotychczasowej bazy SQLite:
```bash
python -m app.scripts.migrate_sqlite_to_postgres --sqlite-path ./fitai.db --postgres-url "$DATABASE_URL"
```

---

## 4. Uruchamianie Testów w Czystym Środowisku

Testy jednostkowe, integracyjne i E2E nie mogą zależeć od lokalnego pliku `.env`.

### Na systemie Linux / macOS:
```bash
env -i \
  PATH="$PATH" \
  DATABASE_URL="sqlite:///./ci_test.db" \
  ENV="development" \
  JWT_SECRET_KEY="ci-jwt-secret-key-32-bytes-minimum-for-tests" \
  CRON_SECRET="ci-cron-secret" \
  RATE_LIMIT_ENABLED="false" \
  pytest -v
```

### Na systemie Windows (PowerShell):
```powershell
if (Test-Path .env) { Rename-Item .env .env.bak }
try {
    $env:DATABASE_URL = "sqlite:///./ci_test.db"
    $env:ENV = "development"
    $env:JWT_SECRET_KEY = "ci-jwt-secret-key-32-bytes-minimum-for-tests"
    $env:CRON_SECRET = "ci-cron-secret"
    $env:RATE_LIMIT_ENABLED = "false"
    python -m pytest -v
} finally {
    if (Test-Path .env.bak) { Rename-Item .env.bak .env }
}
```

---

## 5. Ręczna Lista Kontrolna dla Właściciela przed Wejściem na Produkcję

1. [ ] Sprawdzić zakładkę **GitHub Actions** — wszystkie joby w workflow `EVOLVE tests` są zielone.
2. [ ] W panelu Render sprawdzić, na jaką bazę wskazuje `DATABASE_URL` — upewnić się, że to stabilna instancja PostgreSQL, a nie plan wygasający (Render free PostgreSQL wygasa po 30 dniach).
3. [ ] Włączyć automatyczne backupy bazy w panelu dostawcy.
4. [ ] Ustawić `ENV=production`.
5. [ ] Ustawić `CORS_ORIGINS` na rzeczywistą domenę aplikacji (np. `https://evolve.onrender.com`).
6. [ ] Po pierwszym wdrożeniu zmienić `JWT_SECRET_KEY` na unikalny, wygenerowany ciąg znaków (`openssl rand -hex 32`) i zaktualizować hasło administratora.
7. [ ] Sprawdzić w przeglądarce / curl, że `GET /auth/demo-token` zwraca kod `404 Not Found`.
8. [ ] Skonfigurować dostawcę poczty e-mail, jeśli resetowanie hasła ma wysyłać maile do użytkowników.
9. [ ] Przejść 30-minutowy test manualny na telefonie i komputerze (rejestracja, trening, zapis serii, podsumowanie).

