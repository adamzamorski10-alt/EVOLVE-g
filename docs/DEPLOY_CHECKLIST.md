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

### `ALLOW_DEMO_LOGIN`
- **Domyślnie:** `false` (w produkcji).
- **Działanie:** Jeśli włączone (`true`) oraz `ENV != "production"`, endpoint `/auth/demo-token` zwraca token konta demo dla celów testowych/prezentacyjnych.
- **Bezpieczeństwo produkcyjne:** W produkcji (`ENV=production`) endpoint `/auth/demo-token` ZAWSZE zwraca **404 Not Found**, a wstrzykiwanie tokenu demo w HTML jest całkowicie zablokowane niezależnie od wartości flagi.

### `LOG_RESET_TOKENS`
- **Domyślnie:** `false`.
- **Działanie:** Jeśli `true`, tokeny resetowania hasła są wypisywane w logach serwera (używane wyłącznie lokalnie w celach deweloperskich/diagnostycznych, gdy serwer SMTP nie jest podłączony).
- **W produkcji:** Musi być ustawione na `false` (lub pominięte). Tokeny resetu muszą trafiać wyłącznie na e-mail użytkownika.

### `RATE_LIMIT_ENABLED`
- **Domyślnie:** `true`.
- **Działanie:** Aktywuje ochronę przed brute-force przez SlowAPI (`5/hour` na rejestrację i reset hasła, `10/min` na logowanie). W testach E2E/lokalnych może być ustawione na `false`.

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

