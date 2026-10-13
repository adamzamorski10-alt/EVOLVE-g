# EVOLVE -- Offline SQLite -> PostgreSQL Migration Tool (Stage 20U.7A)

Narzędzie offline do bezpiecznego, atomowego przenoszenia danych z lokalnego pliku bazy SQLite do bazy PostgreSQL.

## Kluczowa zasada: Rozdział schematu od danych

* **Alembic zarządza schematem (DDL):** Migracje schematu (`alembic upgrade head`) tworzą tabele, kolumny, klucze obce oraz indeksy w docelowej bazie PostgreSQL. Narzędzie migracji danych **nie modyfikuje schematu**.
* **Skrypt przenosi rekordy (DML):** `scripts/migrate_sqlite_to_postgres.py` odpowiada wyłącznie za walidację, konwersję typów i atomowy transfer rekordów do istniejących tabel przygotowanych przez Alembic.

---

## Wymagania wstępne

1. **Przygotowanie bazy docelowej PostgreSQL:**
   Docelowa baza PostgreSQL (np. Render PostgreSQL Starter $7/mies. lub dedykowana baza staging) musi być zainicjalizowana przez Alembic:
   ```bash
   DATABASE_URL="postgresql+psycopg://user:password@host:5432/dbname" alembic upgrade head
   ```
2. **Pusta baza docelowa:**
   Wszystkie 12 tabel docelowych (`users`, `user_number_sequence`, `daily_logs`, `nutrition_entries`, `nutrition_adaptations`, `training_sessions`, `goals`, `adaptive_plan_revisions`, `drill_results`, `assessments`, `training_set_results`, `exercise_results`) muszą być puste (`COUNT(*) == 0`). Skrypt odrzuca import, jeśli cel zawiera już dane (ochrona przed nadpisaniem).
3. **Plik źródłowy SQLite:**
   Źródłowy plik (np. `fitai_backup.db`) musi być dostępny lokalnie. Skrypt otwiera go w trybie tylko do odczytu (`mode=ro`) i nie modyfikuje go w żadnym stopniu.

---

## Sposób użycia

### Krok 1: Walidacja wstępna (Preflight / Dry-Run -- tryb domyślny)

Domyślne uruchomienie wykonuje pełną inspekcję schematu, spójności relacyjnej, typów danych i unikalności **bez wykonywania żadnych zapisów**:

```bash
python scripts/migrate_sqlite_to_postgres.py \
  --sqlite-path /sciezka/do/zrodla.db \
  --pg-url postgresql+psycopg://user:password@host:5432/dbname
```

Wynik raportu informuje o:
* liczbie rekordów w poszczególnych tabelach SQLite,
* zgodności schematu w PostgreSQL,
* ewentualnych błędach konwersji (np. niepoprawne formaty dat, osierocone klucze obce, konflikty unikalności).

### Krok 2: Faktyczny import danych (`--apply`)

Gdy preflight zakończy się sukcesem (`PASS`), dodanie flagi `--apply` wykonuje atomowy import w pojedynczej transakcji PostgreSQL:

```bash
python scripts/migrate_sqlite_to_postgres.py \
  --sqlite-path /sciezka/do/zrodla.db \
  --pg-url postgresql+psycopg://user:password@host:5432/dbname \
  --apply
```

Po zakończeniu skrypt weryfikuje zgodność liczby zaimportowanych wierszy. W przypadku jakiegokolwiek błędu cała transakcja jest natychmiast wycofywana (`ROLLBACK`), a baza docelowa pozostaje czysta.

---

## Gwarancje bezpieczeństwa

1. **Brak wartości domyślnych:** Obydwa parametry (`--sqlite-path` oraz `--pg-url`) są obowiązkowe. Skrypt nigdy nie przyjmuje domyślnie `fitai.db` ani zmiennej środowiskowej produkcji Render.
2. **Odrzucenie SQLite jako celu:** Próba wskazania URL `sqlite://...` jako `--pg-url` jest natychmiast blokowana błędem `TargetDialectError`.
3. **Maskowanie sekretów:** Wszelkie hasła i tokeny w URL połączenia są maskowane (`user:***@host...`) we wszystkich logach, komunikatach i raportach.
4. **Konwersja typów danych:**
   * Wartości logiczne (`0`, `1`, `'true'`, `'false'`) są konwertowane na natywny typ PostgreSQL `BOOLEAN`.
   * Daty i znaczniki czasu są parsowane do typów `datetime.date` oraz `datetime.datetime` (bez strefy czasowej), a puste ciągi w polach opcjonalnych zamieniane na `NULL`.
   * Klucze główne (identyfikatory UUID oraz numery sekwencji) są ściśle zachowywane.
5. **Kolejność zależności (Topological Order):**
   Rekordy są wstawiane z zachowaniem więzów integralności:
   `users` -> `user_number_sequence`, `daily_logs`, `nutrition_entries`, `nutrition_adaptations`, `training_sessions`, `goals`, `adaptive_plan_revisions`, `drill_results`, `assessments` -> `training_set_results`, `exercise_results`.
6. **Ochrona przed ponownym importem:**
   Ponowne uruchomienie narzędzia na wypełnionej bazie docelowej kończy się błędem `TargetNotEmptyError`, zapobiegając duplikacji danych i błędom kluczy unikalnych.
