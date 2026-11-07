# Procedura Tworzenia i Odtwarzania Kopii Zapasowej (EVOLVE)

Niniejszy dokument opisuje procedurę odzyskiwania bazy danych produkcyjnej aplikacji EVOLVE.

---

## 1. Tworzenie kopii zapasowej

Kopię zapasową tworzy skrypt `scripts/backup_db.sh`:

```bash
# Ustawienie zmiennej produkcyjnej (lub odczyt z konfiguracji serwera)
export DATABASE_URL="postgresql://user:password@host:port/dbname"

# Wywołanie skryptu z katalogu głównego projektu
chmod +x scripts/backup_db.sh
./scripts/backup_db.sh ./backups
```

Skrypt wygeneruje plik `backups/evolve_backup_YYYYMMDD_HHMMSS.sql.gz` wraz z sumą kontrolną `.sha256`.

---

## 2. Procedura odtwarzania (Restore) krok po kroku

### Krok 1: Weryfikacja integralności pliku
```bash
sha256sum -c backups/evolve_backup_YYYYMMDD_HHMMSS.sql.gz.sha256
```
Upewnij się, że suma kontrolna pliku zgadza się z wyliczoną w momencie tworzenia kopii.

### Krok 2: Zatrzymanie ruchu użytkowników
Przed odtworzeniem bazy zaleca się chwilowe zatrzymanie usługi webowej na Renderze (Suspend Service lub Maintenance page), aby zapobiec zapisywaniu nowych danych w trakcie odtwarzania.

### Krok 3: Odtworzenie bazy danych do PostgreSQL
```bash
# Oczyszczenie adresu z ewentualnego prefiksu SQLAlchemy dialektu (+psycopg)
CLEAN_URL="${DATABASE_URL/postgresql+psycopg:\/\//postgresql:\/\/}"

# Odtworzenie bazy przez strumień psql
gunzip -c backups/evolve_backup_YYYYMMDD_HHMMSS.sql.gz | psql "${CLEAN_URL}"
```

### Krok 4: Weryfikacja schematu i migracji Alembic
Po załadowaniu dumpa należy uruchomić weryfikację spójności schematu:
```bash
python -m alembic current --check-heads
python -m alembic check
```

### Krok 5: Weryfikacja działania aplikacji
Uruchom aplikację i sprawdź endpoint zdrowia:
```bash
curl -f https://<TWOJA_DOMENA_RENDER>/health/
```
Odpowiedź powinna zawierać `"database": "connected"`.

---

## 3. Zarządzanie bazą w panelu Render (Instrukcja dla Właściciela)

> [!NOTE]
> Ta sekcja wymaga bezpośredniego dostępu do konta w [dashboard.render.com](https://dashboard.render.com). Ze względów bezpieczeństwa agent nie posiada i nie żąda uprawnień do panelu chmurowego (oznaczone jako BLOCKED do ręcznej weryfikacji przez właściciela).

1. **Sprawdzenie typu bazy danych i planu:**
   - Zaloguj się na [dashboard.render.com](https://dashboard.render.com).
   - W sekcji **PostgreSQL** odszukaj instancję bazy powiązaną z `fitai-api` / `evolve`.
   - Sprawdź pole **Plan**:
     - *Darmowy (Free PostgreSQL):* Baza wygasa po 30 dniach od utworzenia! Jeśli korzystasz z planu darmowego, dane mogą zostać usunięte przez Render.
     - *Płatny (Starter / Standard):* Trwały dysk SSD, brak automatycznego wygasania.
2. **Sprawdzenie i pobranie automatycznych kopii Render:**
   - W widoku instancji bazy PostgreSQL przejdź do zakładki **Backups**.
   - Render w planach płatnych wykonuje automatyczne codzienne kopie zapasowe.
   - Możesz kliknąć **Download** obok najnowszej kopii, aby pobrać dump bazy bezpośrednio na swój dysk.
3. **Pobranie connection string (DATABASE_URL):**
   - W zakładce **Info** odszukaj **Internal Database URL** (dla usług wewnątrz Rendera) lub **External Database URL** (do wykonywania lokalnego backupu skryptem `backup_db.sh`).
