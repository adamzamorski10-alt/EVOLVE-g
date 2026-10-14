# EVOLVE -- Offline SQLite -> PostgreSQL Migration Tool (Stage 20U.7C)

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
2. **Uwierzytelnienie wersji schematu:**
   Schemat docelowy musi odpowiadać rzeczywistememu headowi grafu migracji Alembic
   (obecnie `evolve25userkey`). Narzędzie odczytuje head dynamicznie z
   `alembic.ini`/`versions/` — nie zakłada wpisanej na twardo rewizji — i porównuje
   go z zawartością tabeli `alembic_version` bazy docelowej. Brak zgodności blokuje import.
3. **Pusta baza docelowa:**
   Wszystkie 12 tabel docelowych (`users`, `user_number_sequence`, `daily_logs`, `nutrition_entries`, `nutrition_adaptations`, `training_sessions`, `goals`, `adaptive_plan_revisions`, `drill_results`, `assessments`, `training_set_results`, `exercise_results`) muszą być puste (`COUNT(*) == 0`). Skrypt odrzuca import, jeśli cel zawiera już dane (ochrona przed nadpisaniem).
4. **Plik źródłowy SQLite:**
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
* zgodności schematu w PostgreSQL z metadanymi SQLModel,
* zgodności wersji schematu (kolumna `alembic_version`) z headem grafu migracji,
* ewentualnych błędach konwersji (np. niepoprawne formaty dat, osierocone klucze obce, konflikty unikalności).

### Krok 2: Faktyczny import danych (`--apply`)

Gdy preflight zakończy się sukcesem (`PASS`), dodanie flagi `--apply` wykonuje atomowy import w pojedynczej transakcji PostgreSQL:

```bash
python scripts/migrate_sqlite_to_postgres.py \
  --sqlite-path /sciezka/do/zrodla.db \
  --pg-url postgresql+psycopg://user:password@host:5432/dbname \
  --apply
```

Po zakończeniu skrypt weryfikuje zgodność liczby zaimportowanych wierszy oraz synchronizuje
sekwencje PostgreSQL. W przypadku jakiegokolwiek błędu cała transakcja jest natychmiast wycofywana
(`ROLLBACK`), a baza docelowa pozostaje czysta.

---

## Gwarancje bezpieczeństwa

1. **Brak wartości domyślnych:** Obydwa parametry (`--sqlite-path` oraz `--pg-url`) są obowiązkowe. Skrypt nigdy nie przyjmuje domyślnie `fitai.db` ani zmiennej środowiskowej produkcji Render.
2. **Odrzucanie SQLite jako celu:** Próba wskazania URL `sqlite://...` jako `--pg-url` jest natychmiast blokowana błędem `TargetDialectError`. Niedozwolone jest także wskazanie niepustej bazy docelowej.
3. **Maskowanie sekretów:** Wszelkie hasła i tokeny w URL połączenia są maskowane (`user:***@host...`) we wszystkich logach, komunikatach i raportach. Wartości danych osobowych (np. `nickname`, `email`) nie są wypisywane w komunikatach o konfliktach unikalności.
4. **Konwersja typów danych:**
   * Wartości logiczne (`0`, `1`, `'true'`, `'false'`) są konwertowane na natywny typ PostgreSQL `BOOLEAN`.
   * Daty są walidowane w całości (dokładny format `YYYY-MM-DD`), a znaczniki czasu w formacie `YYYY-MM-DD[ T]HH:MM[:SS[.ffffff]][Z|±HH:MM]`. Weryfikowany jest pełny format, nie tylko prefiks.
   * Model zakłada czas UTC bez strefy. Świadome strefowo znaczniki czasu (np. `2026-10-13T18:30:00+02:00`) są konwertowane do UTC, a dopiero potem pozbawiane informacji o strefie. Pusta wartość w polu opcjonalnym jest mapowana na `NULL`.
   * Pusty ciąg w opcjonalnym kluczu obcym (np. `exercise_results.source_session_id`) jest traktowany jako dana niejednoznaczna i **przerywa preflight**. Narzędzie nie normalizuje automatycznie pustych ciągów do `NULL`, bo kontrakt danych rozróżnia `NULL` (brak relacji).
   * Klucze główne (identyfikatory UUID oraz numery sekwencji) są ściśle zachowywane.
5. **Relacje i integralność (metadane, nie lista):**
   Wszystkie klucze obce i ograniczenia unikalności są wyznaczane z metadanych SQLModel, dlatego
   narzędzie nie może pominąć relacji dodanych później. Pełny zakres walidacji obejmuje:
   * klucze obce wszystkich tabel — w tym `exercise_results.user_id`, `exercise_results.source_session_id`,
     `training_set_results.session_id` oraz `user_number_sequence.user_id`;
   * unikalność kluczy głównych i wymagane ograniczenia unikalności — w tym `users.user_key`,
     `users.user_number`, `users.nickname`, `user_number_sequence.user_id`,
     `uq_assessments_user_version`, `uq_adaptive_plan_revision_user_version`;
   * indeks częściowy `uq_training_active_user_day` (unikalność pary `user_id`, `session_date` dla `status = 'active'`).
6. **Kolejność zależności (wyznaczona topologicznie):**
   Kolejność importu wynika z grafu zależności FK w metadanych (nie jest wpisana na twardo), dlatego
   rekordy rodzica są zawsze wstawiane przed rekordami potomnymi.
7. **Schemat docelowy (pełna weryfikacja):**
   Przed importem narzędzie porównuje cel z modelem SQLModel: tabele, kolumny, typy, nullability,
   klucze główne, klucze obce, ograniczenia unikalności oraz wymagane indeksy (łącznie z częściowym
   `uq_training_active_user_day`). Narzędzie **nie tworzy** schematu i nie wywołuje
   `SQLModel.metadata.create_all()` — schematem zarządza Alembic.
8. **Sekwencje PostgreSQL:**
   Synchronizowane są wyłącznie istniejące sekwencje (`pg_get_serial_sequence`) wymagające
   aktualizacji. `user_number_sequence.id` był importerem AUTOINCREMENT w SQLite, więc w PostgreSQL
   sekwencja `user_number_sequence_id_seq` jest ustawiana na maksymalne zaimportowane `id`
   (`setval(..., is_called = TRUE)`), aby kolejne rejestracje nie generowały konfliktów kluczy.
   Brak sekwencji jest raportowany jako ostrzeżenie, a każdy błąd synchronizacji jest krytyczny
   i przerywa transakcję (brak cichego kontynuowania).
9. **Ochrona przed ponownym importem:**
   Ponowne uruchomienie narzędzia na wypełnionej bazie docelowej kończy się błędem `TargetNotEmptyError`, zapobiegając duplikacji danych i błędom kluczy unikalnych.

---

## Uwaga dotycząca kont użytkowników po migracji

W SQLite `user_number_sequence.id` było nadawane przez `INTEGER PRIMARY KEY AUTOINCREMENT`.
W migracjach Alembic kolumna ta jest zdefiniowana z sekwencją PostgreSQL
(`user_number_sequence_id_seq`), która jest synchronizowana po imporcie. Przed uruchomieniem
migracji warto upewnić się, że w docelowym schemacie ta sekwencja faktycznie istnieje
(`SELECT pg_get_serial_sequence('user_number_sequence', 'id')`); brak sekwencji jest raportowany
jako ostrzeżenie preflight, ale wtedy kolejne rejestracje kont wymagałyby jawnego podania `id`.
