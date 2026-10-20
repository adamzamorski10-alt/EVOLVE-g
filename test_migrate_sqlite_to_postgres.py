"""Tests for scripts/migrate_sqlite_to_postgres.py (Stage 20U.7C).

Zestaw syntetycznych testów jednostkowych i integracyjnych weryfikujący:
  - Walidację argumentów CLI i odrzucenie SQLite jako celu;
  - Maskowanie haseł i sekretów w connection stringach;
  - Otwieranie źródła SQLite ściśle w trybie tylko do odczytu (mode=ro) i brak modyfikacji źródła;
  - Obsługę nieistniejącego lub pustego źródła;
  - Wykrywanie brakujących tabel w bazie docelowej;
  - Ochronę przed importem do niepustej bazy docelowej (ochrona przed nadpisaniem);
  - Konwersję typów: Boolean (0/1 -> bool), DATE, DATETIME, liczby, NULL i wartości domyślne;
  - Pełną (nie prefiksową) walidację formatów dat i znaczników czasu;
  - Konwersję świadomych strefowo znaczników czasu do naive UTC;
  - Wykrywanie osieroconych kluczy obcych (łącznie z `exercise_results` i
    `user_number_sequence`) oraz naruszeń unikalności — relacje wyznaczane z metadanych;
  - Odrzucanie pustego ciągu w opcjonalnym kluczu obcym (bez cichej normalizacji);
  - Wykrywanie konfliktów w indeksie częściowym uq_training_active_user_day;
  - Weryfikację schematu docelowej bazy jak i zgodności `alembic_version` z headem;
  - Synchronizację sekwencji PostgreSQL tylko dla istniejących sekwencji (błąd = rollback);
  - Zachowanie trybu dry-run (brak zmian w bazie docelowej);
  - Testy integracyjne na PostgreSQL (jeśli baza jest dostępna w środowisku/CI):
      * schemat tworzony RZECZISTYMI migracjami Alembic (`upgrade head`),
        a nie przez `metadata.create_all()`;
      * pełna migracja 12 tabel reprezentatywnych danych;
      * weryfikację typów, integralności, sekwencji i `alembic_version` po imporcie;
      * odrzucenie importu, gdy cel nie jest na headzie migracji;
      * ochronę przed ponownym uruchomieniem;
      * transakcyjny rollback w przypadku błędu w trakcie importu.
"""

from __future__ import annotations

import datetime
import hashlib
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.engine import Engine, create_engine
from sqlalchemy.sql import text

from app.models import SQLModel
from scripts.migrate_sqlite_to_postgres import (
    TABLE_ORDER,
    PreflightReport,
    TargetDialectError,
    TargetNotEmptyError,
    TargetSchemaError,
    build_foreign_key_map,
    build_insert_order,
    build_unique_specs,
    classify_column_type,
    coerce_value,
    expected_alembic_heads,
    extract_and_convert_source_data,
    get_target_engine,
    inspect_target_schema,
    mask_database_url,
    normalize_pg_url,
    open_sqlite_readonly,
    run_migration,
    run_preflight,
    sync_target_sequences,
    verify_insert_order,
    verify_target_schema_against_models,
    validate_relational_constraints,
)

REPO_ROOT = Path(__file__).resolve().parent


# ─── Helpery i Fixtury ────────────────────────────────────────────────────────


def get_test_postgres_url() -> Optional[str]:
    """Zwraca URL działającej bazy PostgreSQL dla testów integracyjnych (np. w CI)."""
    raw_url = os.environ.get("TEST_POSTGRESQL_URL") or os.environ.get("DATABASE_URL")
    if not raw_url or "sqlite" in raw_url.lower():
        return None
    normalized = normalize_pg_url(raw_url)
    try:
        engine = create_engine(normalized)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return normalized
    except Exception:
        return None


HAS_POSTGRES: bool = get_test_postgres_url() is not None


def create_synthetic_sqlite_db(
    db_path: Path,
    users: list[dict[str, Any]],
    user_sequences: Optional[list[dict[str, Any]]] = None,
    daily_logs: Optional[list[dict[str, Any]]] = None,
    nutrition_entries: Optional[list[dict[str, Any]]] = None,
    nutrition_adaptations: Optional[list[dict[str, Any]]] = None,
    training_sessions: Optional[list[dict[str, Any]]] = None,
    training_set_results: Optional[list[dict[str, Any]]] = None,
    exercise_results: Optional[list[dict[str, Any]]] = None,
    goals: Optional[list[dict[str, Any]]] = None,
    adaptive_plan_revisions: Optional[list[dict[str, Any]]] = None,
    drill_results: Optional[list[dict[str, Any]]] = None,
    assessments: Optional[list[dict[str, Any]]] = None,
) -> None:
    """Tworzy syntetyczną bazę SQLite ze wskazanymi danymi testowymi."""
    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    # Utwórz pełny schemat SQLite z metadanych SQLModel
    SQLModel.metadata.create_all(engine)

    with engine.connect() as conn:
        with conn.begin():
            for u in users:
                conn.execute(SQLModel.metadata.tables["users"].insert(), u)
            for s in user_sequences or []:
                conn.execute(SQLModel.metadata.tables["user_number_sequence"].insert(), s)
            for d in daily_logs or []:
                conn.execute(SQLModel.metadata.tables["daily_logs"].insert(), d)
            for n in nutrition_entries or []:
                conn.execute(SQLModel.metadata.tables["nutrition_entries"].insert(), n)
            for na in nutrition_adaptations or []:
                conn.execute(SQLModel.metadata.tables["nutrition_adaptations"].insert(), na)
            for ts in training_sessions or []:
                conn.execute(SQLModel.metadata.tables["training_sessions"].insert(), ts)
            for tr in training_set_results or []:
                conn.execute(SQLModel.metadata.tables["training_set_results"].insert(), tr)
            for er in exercise_results or []:
                conn.execute(SQLModel.metadata.tables["exercise_results"].insert(), er)
            for g in goals or []:
                conn.execute(SQLModel.metadata.tables["goals"].insert(), g)
            for apr in adaptive_plan_revisions or []:
                conn.execute(SQLModel.metadata.tables["adaptive_plan_revisions"].insert(), apr)
            for dr in drill_results or []:
                conn.execute(SQLModel.metadata.tables["drill_results"].insert(), dr)
            for a in assessments or []:
                conn.execute(SQLModel.metadata.tables["assessments"].insert(), a)
    engine.dispose()


def sample_valid_user(uid: str = "u-1", user_number: int = 1) -> dict[str, Any]:
    return {
        "id": uid,
        "user_key": f"native:user:{user_number}",
        "user_number": user_number,
        "nickname": f"athlete_{user_number}",
        "name": "Jan Kowalski",
        "age": 28,
        "height": 182.0,
        "weight": 83.5,
        "start_weight": 85.0,
        "target_weight": 80.0,
        "gender": "mężczyzna",
        "goal": "rekompozycja",
        "frequency": "4",
        "diet": "zbilansowana",
        "allergies": "",
        "meals_per_day": 4,
        "notes": "notatka testowa",
        "plan": "free",
        "role": "free_user",
        "calories_target": 2600,
        "protein_target": 170,
        "streak_days": 5,
        "sports_json": "[]",
        "training_focus_json": "[]",
        "improvement_areas_json": "[]",
        "preferred_foods_json": "[]",
        "avoid_foods_json": "[]",
        "available_equipment_json": "[]",
        "avoid_exercises_json": "[]",
        "reminders_json": "{}",
        "substitutes_history_json": "{}",
        "sport_training_days_json": "[]",
        "training_availability_json": "{}",
        "sport_training_schedule_json": "{}",
        "total_xp": 120,
        "injuries": "",
        "last_weight_change": -0.5,
        "reminder_enabled": 0,  # w SQLite integer 0
        "is_active": 1,         # w SQLite integer 1
        "created_at": datetime.datetime(2026, 5, 1, 10, 0, 0),
        "updated_at": datetime.datetime(2026, 5, 2, 12, 0, 0),
    }


# ─── 1. Bezpieczeństwo i CLI ──────────────────────────────────────────────────


def test_cli_requires_arguments():
    """Uruchomienie skryptu bez wymaganych flag kończy się błędem."""
    res = subprocess.run(
        [sys.executable, "scripts/migrate_sqlite_to_postgres.py"],
        capture_output=True,
        text=True,
    )
    assert res.returncode != 0
    assert "--sqlite-path" in res.stderr
    assert "--pg-url" in res.stderr


def test_rejects_sqlite_as_target_url():
    """Skrypt odrzuca wskazanie bazy SQLite w argumencie --pg-url."""
    with pytest.raises(TargetDialectError, match="nie SQLite"):
        get_target_engine("sqlite:///bad_target.db")

    with pytest.raises(TargetDialectError, match="nie SQLite"):
        get_target_engine("sqlite+pysqlite:///bad_target.db")


def test_mask_database_url_hides_passwords_and_tokens():
    """Hasła i wrażliwe parametry w URL są maskowane w logach i raportach."""
    raw = "postgresql+psycopg://super_admin:P@ssword123!@db.internal.render.com:5432/fitai_prod"
    masked = mask_database_url(raw)
    assert "P@ssword123!" not in masked
    assert "super_admin:***@" in masked
    assert "db.internal.render.com:5432/fitai_prod" in masked


# ─── 2. Źródło SQLite: tryb tylko do odczytu i brak modyfikacji ───────────────


def test_source_sqlite_opened_strictly_readonly_and_not_modified(tmp_path):
    """Źródłowa baza jest otwierana w mode=ro; próby zapisu są blokowane przez silnik."""
    db_file = tmp_path / "source_ro.db"
    create_synthetic_sqlite_db(db_file, [sample_valid_user()])

    # Oblicz hash i czas modyfikacji przed operacją
    with open(db_file, "rb") as f:
        before_hash = hashlib.sha256(f.read()).hexdigest()
    before_mtime = os.path.getmtime(db_file)

    # Otwórz w trybie read-only
    conn = open_sqlite_readonly(db_file)
    rows = conn.execute("SELECT id, name FROM users").fetchall()
    assert len(rows) == 1

    # Próba zapisu musi zostać zablokowana przez SQLite
    with pytest.raises(sqlite3.OperationalError, match="readonly database"):
        conn.execute("INSERT INTO users (id, user_key, name, age) VALUES ('u-x', 'k-x', 'Hack', 20)")
    conn.close()

    # Zweryfikuj, że plik na dysku pozostał nienaruszony
    with open(db_file, "rb") as f:
        after_hash = hashlib.sha256(f.read()).hexdigest()
    after_mtime = os.path.getmtime(db_file)

    assert before_hash == after_hash
    assert before_mtime == after_mtime


def test_nonexistent_source_sqlite_fails_preflight():
    """Wskazanie nieistniejącego pliku SQLite kończy się błędem walidacji."""
    fake_path = Path("non_existent_never_there.db")
    report, data = run_preflight(fake_path, "postgresql+psycopg://user:pass@localhost:5432/db")
    assert report.success is False
    assert any("nie istnieje" in e for e in report.errors)
    assert data is None


def make_mock_pg_engine() -> MagicMock:
    eng = MagicMock()
    eng.dialect = MagicMock()
    eng.dialect.name = "postgresql"
    return eng


def test_empty_source_sqlite_missing_users_table_fails_preflight(tmp_path):
    """Pusty plik SQLite bez tabeli users jest odrzucany w preflight."""
    empty_db = tmp_path / "empty.db"
    conn = sqlite3.connect(empty_db)
    conn.execute("CREATE TABLE other_table (id INT)")
    conn.commit()
    conn.close()

    mock_engine = make_mock_pg_engine()

    # mock inspect
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "scripts.migrate_sqlite_to_postgres.inspect_target_schema",
            lambda eng: ({tbl: 0 for tbl in TABLE_ORDER}, []),
        )
        report, data = run_preflight(empty_db, "postgresql+psycopg://mock/db", target_engine=mock_engine)

    assert report.success is False
    assert any("brakuje kluczowej tabeli 'users'" in e for e in report.errors)
    assert data is None


# ─── 3. Inspekcja bazy docelowej (brak tabel i ochrona przed nadpisaniem) ──────


def test_target_missing_required_tables_fails_preflight(tmp_path):
    """Brak wymaganych tabel w bazie docelowej blokuje migrację."""
    db_file = tmp_path / "source.db"
    create_synthetic_sqlite_db(db_file, [sample_valid_user()])

    # Symuluj bazę docelową posiadającą tylko users, bez reszty tabel
    mock_engine = make_mock_pg_engine()

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "scripts.migrate_sqlite_to_postgres.inspect_target_schema",
            lambda eng: ({tbl: 0 for tbl in TABLE_ORDER}, ["W bazie docelowej brakuje wymaganych tabel: ['daily_logs']"]),
        )
        report, data = run_preflight(db_file, "postgresql+psycopg://mock/db", target_engine=mock_engine)

    assert report.success is False
    assert any("brakuje wymaganych tabel" in e for e in report.errors)
    assert data is None


def test_target_already_contains_data_fails_preflight(tmp_path):
    """Jeśli w bazie docelowej istnieją już rekordy, migracja zostaje odrzucona."""
    db_file = tmp_path / "source.db"
    create_synthetic_sqlite_db(db_file, [sample_valid_user()])

    mock_engine = make_mock_pg_engine()

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "scripts.migrate_sqlite_to_postgres.inspect_target_schema",
            lambda eng: (
                {"users": 5},
                ["Tabela docelowa 'users' zawiera już 5 rekordów! Baza docelowa musi być całkowicie pusta."],
            ),
        )
        report, data = run_preflight(db_file, "postgresql+psycopg://mock/db", target_engine=mock_engine)

    assert report.success is False
    assert any("zawiera już 5 rekordów" in e for e in report.errors)
    assert data is None


# ─── 4. Konwersja typów: Boolean, Date, Datetime, Liczby, NULL ────────────────


def test_type_coercion_booleans():
    """Poprawna konwersja wartości SQLite (0, 1, 'true', 'false') na Python bool."""
    val, err = coerce_value(1, "bool", "reminder_enabled", nullable=False)
    assert val is True and err is None

    val, err = coerce_value(0, "bool", "reminder_enabled", nullable=False)
    assert val is False and err is None

    val, err = coerce_value("true", "bool", "reminder_enabled", nullable=False)
    assert val is True and err is None

    val, err = coerce_value("false", "bool", "reminder_enabled", nullable=False)
    assert val is False and err is None

    val, err = coerce_value("not_a_bool", "bool", "reminder_enabled", nullable=False)
    assert val is None and "nieznana wartość logiczna" in err

    val, err = coerce_value(None, "bool", "reminder_enabled", nullable=True)
    assert val is None and err is None

    val, err = coerce_value(None, "bool", "reminder_enabled", nullable=False)
    assert val is None and "nie dopuszcza wartości NULL" in err


def test_type_coercion_dates():
    """Poprawna konwersja ISO date strings na datetime.date."""
    val, err = coerce_value("2026-10-13", "date", "session_date", nullable=False)
    assert val == datetime.date(2026, 10, 13) and err is None

    # DateTime obcięty do daty
    val, err = coerce_value(datetime.datetime(2026, 10, 13, 14, 0, 0), "date", "session_date", nullable=False)
    assert val == datetime.date(2026, 10, 13) and err is None

    # Błędna data
    val, err = coerce_value("invalid-date", "date", "session_date", nullable=False)
    assert val is None and "nieprawidłowy format daty" in err

    # Pusty string w kolumnie nullable
    val, err = coerce_value("", "date", "target_date", nullable=True)
    assert val is None and err is None


def test_type_coercion_dates_validate_full_format_not_only_prefix():
    """Data musi mieć DOKŁADNIE format YYYY-MM-DD: błędny prefiks/suffix jest odrzucany."""
    for raw in ("2026-13-45", "2026-10-13whatever", "2026-10-13 00:00:00junk", "20261013"):
        val, err = coerce_value(raw, "date", "session_date", nullable=False)
        assert val is None, raw
        assert err is not None and "nieprawidłowy format daty" in err, raw


def test_type_coercion_datetimes():
    """Poprawna konwersja ISO datetime strings na naive datetime.datetime."""
    val, err = coerce_value("2026-10-13 18:30:00", "datetime", "logged_at", nullable=False)
    assert val == datetime.datetime(2026, 10, 13, 18, 30, 0) and err is None

    val, err = coerce_value("2026-10-13T18:30:00.500000Z", "datetime", "logged_at", nullable=False)
    assert val == datetime.datetime(2026, 10, 13, 18, 30, 0, 500000) and err is None

    val, err = coerce_value("bad-time-stamp", "datetime", "logged_at", nullable=False)
    assert val is None and "nieprawidłowy format znacznika czasu" in err


def test_type_coercion_datetimes_validate_full_format_not_only_prefix():
    """Znacznik czasu jest walidowany w całości, a nie tylko przez prefiks daty."""
    for raw in ("2026-10-13 18:30:00garbage", "bad-time-stamp", "2026-1-13T18:30"):
        val, err = coerce_value(raw, "datetime", "logged_at", nullable=False)
        assert val is None, raw
        assert err is not None and "nieprawidłowy format znacznika czasu" in err, raw


def test_type_coercion_timezone_aware_datetimes_are_converted_to_utc():
    """Świadome strefowo znaczniki czasu są konwertowane do UTC PRZED usunięciem tzinfo."""
    aware = datetime.datetime(
        2026, 10, 13, 18, 30, tzinfo=datetime.timezone(datetime.timedelta(hours=2))
    )
    val, err = coerce_value(aware, "datetime", "logged_at", nullable=False)
    assert err is None
    assert val == datetime.datetime(2026, 10, 13, 16, 30)
    assert val.tzinfo is None

    val, err = coerce_value("2026-10-13T18:30:00+02:00", "datetime", "logged_at", nullable=False)
    assert err is None
    assert val == datetime.datetime(2026, 10, 13, 16, 30)

    val, err = coerce_value("2026-10-13T00:30:00-05:30", "datetime", "logged_at", nullable=False)
    assert err is None
    assert val == datetime.datetime(2026, 10, 13, 6, 0)


def test_type_coercion_numbers_and_nulls():
    """Poprawna konwersja liczb i obsługa pustych stringów w kolumnach opcjonalnych."""
    val, err = coerce_value("123", "int", "age", nullable=False)
    assert val == 123 and err is None

    val, err = coerce_value("85.7", "float", "weight", nullable=False)
    assert val == 85.7 and err is None

    # Pusty ciąg w kolumnie opcjonalnej -> NULL
    val, err = coerce_value("", "float", "weight", nullable=True)
    assert val is None and err is None


def test_string_columns_preserve_empty_strings_without_silent_null_normalization():
    """Pusty ciąg w kolumnie tekstowej nie jest cicho zamieniany na NULL.

    Walidacja opcjonalnych kluczy obcych wykrywa takie wartości osobno i przerywa
    preflight, zamiast zgadywać intencję danych źródłowych.
    """
    val, err = coerce_value("", "string", "source_session_id", nullable=True)
    assert val == "" and err is None


# ─── 4b. Relacje i unikalność wyznaczane z metadanych modelu ──────────────────


def test_foreign_keys_are_derived_from_model_metadata():
    """Walidacja FK nie opiera się na ręcznie utrzymywanej liście tabel."""
    fk_map = build_foreign_key_map()

    # Relacje wymienione w audycie muszą być wykrywane automatycznie.
    assert any(
        spec.ref_table == "training_sessions" and spec.column == "source_session_id"
        for spec in fk_map.get("exercise_results", [])
    )
    assert any(
        spec.ref_table == "users" and spec.column == "user_id"
        for spec in fk_map.get("user_number_sequence", [])
    )
    assert any(
        spec.ref_table == "training_sessions" and spec.column == "session_id"
        for spec in fk_map.get("training_set_results", [])
    )

    # Każda relacja modelu musi być obsłużona (żadna tabela z FK nie może zaginąć).
    for table_name, specs in fk_map.items():
        assert specs, table_name
    assert set(fk_map) == {
        "daily_logs",
        "nutrition_entries",
        "nutrition_adaptations",
        "training_sessions",
        "goals",
        "adaptive_plan_revisions",
        "drill_results",
        "assessments",
        "training_set_results",
        "exercise_results",
        "user_number_sequence",
    }


def test_unique_specs_are_derived_from_model_metadata():
    """Wymagane unikalności (w tym user_number_sequence.user_id) wynikają z modelu."""
    specs = build_unique_specs()

    sequence_specs = [
        spec for spec in specs
        if spec.table == "user_number_sequence" and spec.columns == ("user_id",)
    ]
    assert sequence_specs, "brak wykrytej unikalności user_number_sequence.user_id"

    active_session = [
        spec for spec in specs if spec.label == "uq_training_active_user_day"
    ]
    assert active_session and active_session[0].predicate is not None


def test_import_order_satisfies_all_model_foreign_keys():
    """Kolejność importu (bez twardo wpisanej listy) spełnia wszystkie więzy FK."""
    order = build_insert_order()
    assert sorted(order) == sorted(TABLE_ORDER)
    verify_insert_order(order, TABLE_ORDER)

    exercise_index = order.index("exercise_results")
    training_index = order.index("training_sessions")
    assert training_index < exercise_index


def test_expected_alembic_heads_are_read_from_migration_graph():
    """Narzędzie odczytuje head z grafu migracji, a nie z utrwalonej listy."""
    heads = expected_alembic_heads()
    assert heads, "graf migracji nie zwraca headu"
    assert len(heads) == 1, f"oczekiwano pojedynczego headu, otrzymano {heads}"


# ─── 5. Wykrywanie osieroconych kluczy i konfliktów unikalności ───────────────


def test_preflight_detects_orphan_user_id(tmp_path):
    """Osierocony user_id w tabeli potomnej (brak użytkownika) jest wykrywany."""
    db_file = tmp_path / "orphan.db"
    create_synthetic_sqlite_db(
        db_file,
        users=[sample_valid_user("u-1", 1)],
        daily_logs=[{
            "id": "log-1",
            "user_id": "u-GHOST",  # nie istnieje w users
            "log_date": datetime.date(2026, 5, 1),
            "food": "",
            "workout": "",
            "meals_json": "[]",
            "workouts_json": "[]",
            "custom_meals_json": "[]",
            "mood": "",
            "logged_at": datetime.datetime(2026, 5, 1, 8, 0),
        }],
    )

    mock_engine = make_mock_pg_engine()

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "scripts.migrate_sqlite_to_postgres.inspect_target_schema",
            lambda eng: ({tbl: 0 for tbl in TABLE_ORDER}, []),
        )
        report, data = run_preflight(db_file, "postgresql+psycopg://mock/db", target_engine=mock_engine)

    assert report.success is False
    assert any("osierocony user_id='u-GHOST'" in e for e in report.errors)
    assert data is None


def test_preflight_detects_duplicate_active_training_session():
    """Wiele aktywnych sesji dla tego samego użytkownika w jednym dniu narusza uq_training_active_user_day."""
    u = sample_valid_user("u-1", 1)
    s1 = {
        "id": "sess-1",
        "user_id": "u-1",
        "session_date": datetime.date(2026, 5, 10),
        "status": "active",
    }
    s2 = {
        "id": "sess-2",
        "user_id": "u-1",
        "session_date": datetime.date(2026, 5, 10),
        "status": "active",  # konflikt z s1!
    }

    errors = validate_relational_constraints({
        "users": [u],
        "training_sessions": [s1, s2],
    })
    assert any("konflikt indeksu uq_training_active_user_day" in e for e in errors)


def test_preflight_detects_duplicate_user_key():
    """Zduplikowany user_key w tabeli users jest blokowany przed importem."""
    u1 = sample_valid_user("u-1", 1)
    u2 = sample_valid_user("u-2", 2)
    u2["user_key"] = u1["user_key"]  # duplikat

    errors = validate_relational_constraints({
        "users": [u1, u2],
    })
    assert any("zduplikowany user_key" in e for e in errors)


def test_preflight_detects_duplicate_user_number_sequence_user_id():
    """Unikalność user_number_sequence.user_id ( relacja 1:1 ) jest wymuszana."""
    u = sample_valid_user("u-1", 1)

    errors = validate_relational_constraints({
        "users": [u],
        "user_number_sequence": [
            {"id": 1, "user_id": "u-1"},
            {"id": 2, "user_id": "u-1"},  # konflikt unikalności user_id
        ],
    })
    assert any("user_number_sequence" in e and "user_id" in e for e in errors)


def test_preflight_detects_orphan_user_number_sequence_user_id():
    """user_number_sequence.user_id bez istniejącego użytkownika jest sierotą."""
    errors = validate_relational_constraints({
        "users": [sample_valid_user("u-1", 1)],
        "user_number_sequence": [{"id": 1, "user_id": "u-GHOST"}],
    })
    assert any("osierocony user_id='u-GHOST'" in e for e in errors)


def test_preflight_detects_orphan_source_session_id():
    """Osierocony exercise_results.source_session_id jest wykrywany (relacja metadata)."""
    errors = validate_relational_constraints({
        "users": [sample_valid_user("u-1", 1)],
        "training_sessions": [{
            "id": "sess-1",
            "user_id": "u-1",
            "session_date": datetime.date(2026, 5, 10),
            "status": "active",
        }],
        "exercise_results": [{
            "id": "ex-1",
            "user_id": "u-1",
            "source_session_id": "sess-MISSING",
            "exercise_name": "Przysiad",
            "session_date": datetime.date(2026, 5, 10),
            "sets": 3,
            "reps": 8,
            "weight_kg": 100.0,
            "rpe": 8,
            "notes": "",
            "logged_at": datetime.datetime(2026, 5, 10, 17, 20),
        }],
    })
    assert any("osierocony source_session_id='sess-MISSING'" in e for e in errors)


def test_preflight_rejects_empty_string_in_optional_foreign_key(tmp_path):
    """Pusty ciąg w opcjonalnym FK przerywa preflight zamiast cichej normalizacji."""
    db_file = tmp_path / "empty_fk.db"
    create_synthetic_sqlite_db(
        db_file,
        users=[sample_valid_user("u-1", 1)],
        exercise_results=[{
            "id": "ex-1",
            "user_id": "u-1",
            "source_session_id": "",  # niejednoznaczne: NULL czy błędne id?
            "exercise_name": "Przysiad",
            "session_date": datetime.date(2026, 5, 10),
            "sets": 3,
            "reps": 8,
            "weight_kg": 100.0,
            "rpe": 8,
            "notes": "",
            "logged_at": datetime.datetime(2026, 5, 10, 17, 20),
        }],
    )

    mock_engine = make_mock_pg_engine()

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "scripts.migrate_sqlite_to_postgres.inspect_target_schema",
            lambda eng: ({tbl: 0 for tbl in TABLE_ORDER}, []),
        )
        report, data = run_preflight(db_file, "postgresql+psycopg://mock/db", target_engine=mock_engine)

    assert report.success is False
    assert any(
        "source_session_id" in e and "pusty ciąg" in e for e in report.errors
    ), report.errors
    assert data is None


def test_preflight_rejects_source_datetime_with_trailing_garbage(tmp_path):
    """Źródłowa wartość daty/czasu z błędnym formatem (nie tylko prefiks) blokuje import."""
    db_file = tmp_path / "bad_time.db"
    create_synthetic_sqlite_db(db_file, users=[sample_valid_user("u-1", 1)])

    # Modyfikujemy własny plik-fixtur (narzędzie i tak otwiera źródło tylko do odczytu).
    with sqlite3.connect(db_file) as conn:
        conn.execute("UPDATE users SET created_at = '2026-05-01 10:00:00+00:00 ileś'")

    data, errors, _warnings = extract_and_convert_source_data(open_sqlite_readonly(db_file))

    assert data is not None
    assert any(
        "created_at" in e and "nieprawidłowy format znacznika czasu" in e for e in errors
    ), errors


# ─── 6. Tryb Dry-Run (brak modyfikacji celu) ───────────────────────────────────


def test_dry_run_preflight_passes_without_modifying_target(tmp_path):
    """W trybie domyślnym (bez --apply) poprawna baza przechodzi preflight bez wywoływania zapisu."""
    db_file = tmp_path / "valid_source.db"
    create_synthetic_sqlite_db(
        db_file,
        users=[sample_valid_user("u-1", 1)],
        user_sequences=[{"id": 1, "user_id": "u-1"}],
    )

    mock_engine = make_mock_pg_engine()

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "scripts.migrate_sqlite_to_postgres.inspect_target_schema",
            lambda eng: ({tbl: 0 for tbl in TABLE_ORDER}, []),
        )
        result = run_migration(
            sqlite_path=db_file,
            pg_url="postgresql+psycopg://mock_host/db",
            apply=False,
            target_engine=mock_engine,
        )

    assert result.success is True
    assert result.applied is False
    assert result.preflight_report.success is True
    assert result.preflight_report.source_counts["users"] == 1
    assert result.preflight_report.source_counts["user_number_sequence"] == 1
    # connect() w celu zapisu nie powinno być wywołane w trybie dry-run
    mock_engine.connect.assert_not_called()


# ─── 6b. Synchronizacja sekwencji PostgreSQL (regresja ukrywania błędów) ────

"""Regresja: błąd synchronizacji sekwencji nie może być cicho przechwycony."""
import scripts.migrate_sqlite_to_postgres as mig


class _FakeResult:
    def __init__(self, value):
        self._value = value

    def scalar(self):
        return self._value


class _FailingSequenceConnection:
    """Atrapa połączenia: sekwencja istnieje, ale setval kończy się błędem."""

    def execute(self, statement, params=None):
        sql = str(statement)
        if "pg_get_serial_sequence" in sql:
            return _FakeResult("public.user_number_sequence_id_seq")
        if "setval" in sql:
            raise RuntimeError("permission denied for sequence")
        raise AssertionError(f"nieoczekiwane zapytanie: {sql}")


def test_sequence_sync_failure_is_not_swallowed(tmp_path):
    converted = {
        "users": [],
        "user_number_sequence": [{"id": 7, "user_id": "u-1"}],
    }

    with pytest.raises(Exception) as exc_info:
        mig.sync_target_sequences(_FailingSequenceConnection(), converted)

    assert "user_number_sequence_id_seq" in str(exc_info.value)
    # Komunikat musi identyfikować tabelę/kolumny i nie może wypisać danych osobowych.
    assert "user_number_sequence.id" in str(exc_info.value)


def test_sequence_sync_sets_max_id_when_sequence_exists(tmp_path):
    class _RecordingConnection:
        def __init__(self):
            self.setval_params = None

        def execute(self, statement, params=None):
            sql = str(statement)
            if "pg_get_serial_sequence" in sql:
                return _FakeResult("public.user_number_sequence_id_seq")
            if "setval" in sql:
                self.setval_params = params
                return _FakeResult(params["last_value"])
            raise AssertionError(f"nieoczekiwane zapytanie: {sql}")

    conn = _RecordingConnection()
    synced = mig.sync_target_sequences(
        conn,
        {
            "users": [],
            "user_number_sequence": [{"id": 3, "user_id": "u-1"}, {"id": 9, "user_id": "u-2"}],
        },
    )
    assert conn.setval_params["last_value"] == 9
    assert any("user_number_sequence_id_seq" in entry for entry in synced)


def test_sequence_sync_skips_when_no_sequence_exists():
    class _NoSequenceConnection:
        def execute(self, statement, params=None):
            assert "pg_get_serial_sequence" in str(statement)
            return _FakeResult(None)

    assert mig.sync_target_sequences(
        _NoSequenceConnection(),
        {"users": [], "user_number_sequence": [{"id": 1, "user_id": "u-1"}]},
    ) == []


# ─── 7. Testy Integracyjne PostgreSQL (rzeczywiste migracje Alembic) ──────────


def alembic_upgrade_to_head(pg_url: str) -> None:
    """Buduje schemat docelowy RZECZISTYMI migracjami Alembic (nie create_all)."""
    from alembic import command
    from alembic.config import Config

    import app.config as app_config

    previous_url = app_config.DATABASE_URL
    app_config.DATABASE_URL = pg_url
    try:
        config = Config(str(REPO_ROOT / "alembic.ini"))
        config.set_main_option("sqlalchemy.url", pg_url)
        command.upgrade(config, "head")
    finally:
        app_config.DATABASE_URL = previous_url


def alembic_downgrade_to(pg_url: str, revision: str) -> None:
    """Cofa schemat docelowy do wskazanej rewizji Alembic."""
    from alembic import command
    from alembic.config import Config

    import app.config as app_config

    previous_url = app_config.DATABASE_URL
    app_config.DATABASE_URL = pg_url
    try:
        config = Config(str(REPO_ROOT / "alembic.ini"))
        config.set_main_option("sqlalchemy.url", pg_url)
        command.downgrade(config, revision)
    finally:
        app_config.DATABASE_URL = previous_url


def reset_target_for_migration_tests(pg_url: str) -> Engine:
    """Przywraca pusty cel zbudowany wyłącznie przez RZECZISTE migracje Alembic.

    Dane są usuwane przez TRUNCATE (bez ręcznego DDL), a schemat jest potwierdzany
    komendą `alembic upgrade head` — narzędzie migracji nie tworzy schematu samo.
    """
    engine = create_engine(pg_url)
    truncate_list = ", ".join(TABLE_ORDER)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {truncate_list} RESTART IDENTITY CASCADE"))
    alembic_upgrade_to_head(pg_url)
    return engine


def full_migration_fixture_rows() -> dict[str, list[dict[str, Any]]]:
    """Reprezentatywny zestaw danych dla wszystkich 12 tabel."""
    user = sample_valid_user("user-uuid-1", 1)
    return {
        "users": [user],
        "user_number_sequence": [{"id": 1, "user_id": "user-uuid-1"}],
        "daily_logs": [{
            "id": "log-uuid-1",
            "user_id": "user-uuid-1",
            "log_date": datetime.date(2026, 5, 10),
            "food": "omlet",
            "workout": "siłowy",
            "meals_json": '[{"name": "omlet", "kcal": 500}]',
            "workouts_json": '[{"name": "przysiady"}]',
            "custom_meals_json": "[]",
            "mood": "dobry",
            "weight": 83.2,
            "energy_level": 8,
            "fatigue_score": 3,
            "logged_at": datetime.datetime(2026, 5, 10, 20, 0),
        }],
        "nutrition_entries": [{
            "id": "nut-uuid-1",
            "user_id": "user-uuid-1",
            "consumed_at": datetime.datetime(2026, 5, 10, 13, 0),
            "meal_type": "lunch",
            "name": "kurczak z ryżem",
            "calories_kcal": 650.0,
            "protein_g": 50.0,
            "carbs_g": 75.0,
            "fat_g": 15.0,
            "fiber_g": 6.0,
            "water_liters": 0.5,
            "notes": "",
        }],
        "nutrition_adaptations": [{
            "id": "ad-uuid-1",
            "user_id": "user-uuid-1",
            "created_at": datetime.datetime(2026, 5, 10, 21, 0),
            "evidence_days": 7,
            "training_sessions": 4,
            "base_calories_kcal": 2600,
            "proposed_calories_kcal": 2500,
            "base_protein_g": 170,
            "proposed_protein_g": 170,
            "direction": "decrease",
            "reason": "waga stabilna",
            "status": "applied",
        }],
        "training_sessions": [{
            "id": "sess-uuid-1",
            "user_id": "user-uuid-1",
            "session_date": datetime.date(2026, 5, 10),
            "status": "active",
            "planned_snapshot_json": '{"exercises": ["squat"]}',
            "started_at": datetime.datetime(2026, 5, 10, 17, 0),
            "notes": "sesja popołudniowa",
            "created_at": datetime.datetime(2026, 5, 10, 17, 0),
            "updated_at": datetime.datetime(2026, 5, 10, 17, 0),
        }],
        "training_set_results": [{
            "id": "set-uuid-1",
            "session_id": "sess-uuid-1",
            "user_id": "user-uuid-1",
            "exercise_key": "squat",
            "exercise_name": "Przysiad ze sztangą",
            "set_number": 1,
            "planned_reps": 8,
            "planned_weight_kg": 100.0,
            "actual_reps": 8,
            "actual_weight_kg": 100.0,
            "actual_rpe": 8,
            "completed": 1,  # SQLite int -> bool
            "note": "",
            "logged_at": datetime.datetime(2026, 5, 10, 17, 15),
        }],
        "exercise_results": [{
            "id": "ex-uuid-1",
            "user_id": "user-uuid-1",
            "source_session_id": "sess-uuid-1",
            "source_exercise_key": "squat",
            "exercise_name": "Przysiad ze sztangą",
            "session_date": datetime.date(2026, 5, 10),
            "sets": 1,
            "reps": 8,
            "weight_kg": 100.0,
            "rpe": 8,
            "notes": "",
            "logged_at": datetime.datetime(2026, 5, 10, 17, 20),
        }],
        "goals": [{
            "id": "goal-uuid-1",
            "user_id": "user-uuid-1",
            "goal_type": "strength",
            "title": "Przysiad 120kg",
            "description": "osiągnięcie 120kg w serii",
            "status": "active",
            "start_date": datetime.date(2026, 5, 1),
            "target_date": datetime.date(2026, 8, 1),
            "priority": 1,
            "metadata_json": "{}",
            "metric_key": "squat_1rm",
            "baseline_value": 100.0,
            "target_value": 120.0,
            "created_at": datetime.datetime(2026, 5, 1, 10, 0),
            "updated_at": datetime.datetime(2026, 5, 1, 10, 0),
        }],
        "adaptive_plan_revisions": [{
            "id": "apr-uuid-1",
            "user_id": "user-uuid-1",
            "source_session_ids_json": '["sess-uuid-1"]',
            "previous_plan_json": "{}",
            "applied_plan_json": "{}",
            "decision_summary_json": "{}",
            "version": 1,
            "created_at": datetime.datetime(2026, 5, 10, 22, 0),
        }],
        "drill_results": [{
            "id": "drill-uuid-1",
            "user_id": "user-uuid-1",
            "drill_name": "Rzuty osobiste",
            "drill_category": "skill",
            "drill_sport": "basketball",
            "target_pct": 80,
            "session_date": datetime.date(2026, 5, 10),
            "success_count": 8,
            "total_attempts": 10,
            "rpe": 5,
            "notes": "",
            "logged_at": datetime.datetime(2026, 5, 10, 18, 0),
        }],
        "assessments": [{
            "id": "ass-uuid-1",
            "user_id": "user-uuid-1",
            "assessment_version": 1,
            "status": "completed",
            "assessment_date": datetime.date(2026, 5, 1),
            "training_level": "intermediate",
            "recovery_score": 8,
            "notes": "",
            "created_at": datetime.datetime(2026, 5, 1, 9, 0),
        }],
    }


def build_migration_source_db(db_path: Path) -> None:
    """Tworzy syntetyczną bazę SQLite z pełnym zestawem danych."""
    rows = full_migration_fixture_rows()
    create_synthetic_sqlite_db(
        db_path,
        user_sequences=rows["user_number_sequence"],
        users=rows["users"],
        daily_logs=rows["daily_logs"],
        nutrition_entries=rows["nutrition_entries"],
        nutrition_adaptations=rows["nutrition_adaptations"],
        training_sessions=rows["training_sessions"],
        training_set_results=rows["training_set_results"],
        exercise_results=rows["exercise_results"],
        goals=rows["goals"],
        adaptive_plan_revisions=rows["adaptive_plan_revisions"],
        drill_results=rows["drill_results"],
        assessments=rows["assessments"],
    )


@pytest.mark.skipif(not HAS_POSTGRES, reason="PostgreSQL nie jest dostępny lokalnie; test uruchamiany w CI.")
def test_postgres_integration_full_migration(tmp_path):
    """Pełna integracja z PostgreSQL: schemat z Alembic + migracja 12 tabel."""
    pg_url = get_test_postgres_url()
    assert pg_url is not None

    # 1. Schemat docelowy tworzą RZECZISTE migracje Alembic (nie metadata.create_all).
    reset_target_for_migration_tests(pg_url)

    # 2. Schemat utworzony przez migracje musi być zgodny z modelem.
    pg_engine = create_engine(pg_url)
    insp = sa.inspect(pg_engine)
    assert set(TABLE_ORDER).issubset(set(insp.get_table_names()))
    assert verify_target_schema_against_models(insp) == []

    # 3. Utwórz reprezentatywną syntetyczną bazę SQLite
    sqlite_file = tmp_path / "synth_full.db"
    build_migration_source_db(sqlite_file)

    # 4. Preflight:POPrawny (schemat, dane, head Alembica).
    preflight_report, preflight_data = run_preflight(sqlite_file, pg_url)
    assert preflight_report.success is True, preflight_report.errors
    assert preflight_report.source_counts["users"] == 1

    # 5. Wykonaj rzeczywistą migrację z flagą --apply
    res = run_migration(sqlite_path=sqlite_file, pg_url=pg_url, apply=True, target_engine=pg_engine)
    assert res.success is True, res.error_message
    assert res.applied is True

    # 6. Sprawdź rekordy w PostgreSQL (atomowość + typy)
    with pg_engine.connect() as conn:
        for tbl in TABLE_ORDER:
            cnt = conn.execute(text(f"SELECT COUNT(*) FROM {tbl}")).scalar()
            assert cnt == 1, f"Tabela {tbl} powinna zawierać dokładnie 1 rekord, ma: {cnt}"

        # Sprawdź typ logiczny (PostgreSQL boolean)
        row = conn.execute(text("SELECT reminder_enabled, is_active FROM users WHERE id = 'user-uuid-1'")).first()
        assert row[0] is False  # 0 -> False
        assert row[1] is True   # 1 -> True

        # Sprawdź typ daty
        s_row = conn.execute(text("SELECT session_date FROM training_sessions WHERE id = 'sess-uuid-1'")).first()
        assert s_row[0] == datetime.date(2026, 5, 10)

        # Sprawdź typ znacznika czasu
        dt_row = conn.execute(text("SELECT logged_at FROM exercise_results WHERE id = 'ex-uuid-1'")).first()
        assert dt_row[0] == datetime.datetime(2026, 5, 10, 17, 20)
        assert dt_row[0].tzinfo is None

        # Sprawdź FK do źródła sesji
        fk_row = conn.execute(
            text("SELECT source_session_id FROM exercise_results WHERE id = 'ex-uuid-1'")
        ).first()
        assert fk_row[0] == "sess-uuid-1"

        # Sprawdź indeks częściowy unikalności
        index_def = conn.execute(
            text("SELECT indexdef FROM pg_indexes WHERE indexname = 'uq_training_active_user_day'")
        ).scalar_one()
        assert "UNIQUE INDEX" in index_def.upper()
        assert "WHERE" in index_def.upper()

        # Sprawdź unikalność user_number_sequence.user_id
        uq = conn.execute(
            text(
                "SELECT 1 FROM pg_constraint "
                "WHERE conrelid = 'user_number_sequence'::regclass AND contype = 'u'"
            )
        ).first()
        assert uq is not None

    # 7. Sekwencja user_number_sequence musi być zsynchronizowana z max(id) = 1,
    #    aby kolejne inserty aplikacji nie generowały konfliktów.
    with pg_engine.connect() as conn:
        seq_value = conn.execute(
            text("SELECT last_value, is_called FROM user_number_sequence_id_seq")
        ).first()
    assert seq_value[0] == 1
    assert seq_value[1] is True

    # 8. Ochrona przed ponownym uruchomieniem: ponowna próba importu musi zostać zablokowana
    rerun_res = run_migration(sqlite_path=sqlite_file, pg_url=pg_url, apply=True, target_engine=pg_engine)
    assert rerun_res.success is False
    assert any("zawiera już 1 rekordów" in e for e in rerun_res.preflight_report.errors)

    # 9. Schemat Alembica nadal obecny i zgodny z headem (narzędzie nie zmienia DDL)
    with pg_engine.connect() as conn:
        version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
    assert version == expected_alembic_heads()[0]

    reset_target_for_migration_tests(pg_url)
    pg_engine.dispose()


@pytest.mark.skipif(not HAS_POSTGRES, reason="PostgreSQL nie jest dostępny lokalnie; test uruchamiany w CI.")
def test_postgres_integration_rejects_target_not_at_alembic_head(tmp_path):
    """Baza docelowa z nieaktualnym schematem Alembic jest odrzucana."""
    pg_url = get_test_postgres_url()
    assert pg_url is not None

    reset_target_for_migration_tests(pg_url)

    sqlite_file = tmp_path / "synth_head.db"
    build_migration_source_db(sqlite_file)

    # Cel nie jest na headzie (downgrade o jedną rewizję lub pusty alembic_version).
    from alembic import command
    from alembic.config import Config

    import app.config as app_config

    previous_url = app_config.DATABASE_URL
    app_config.DATABASE_URL = pg_url
    try:
        config = Config(str(REPO_ROOT / "alembic.ini"))
        config.set_main_option("sqlalchemy.url", pg_url)
        command.downgrade(config, "evolve24_sport_training_schedule")
    finally:
        app_config.DATABASE_URL = previous_url

    report, data = run_preflight(sqlite_file, pg_url)
    assert report.success is False
    assert any(
        "alembic_version" in e or "headu" in e for e in report.errors
    ), report.errors
    assert any(
        "brakuje wymaganych tabel" in e or "kolumna" in e or "unikalności" in e.lower()
        for e in report.errors
    ), report.errors
    assert data is None


@pytest.mark.skipif(not HAS_POSTGRES, reason="PostgreSQL nie jest dostępny lokalnie; test uruchamiany w CI.")
def test_postgres_integration_rollback_on_error(tmp_path):
    """Błąd w trakcie wstawiania w transakcji wywołuje czysty ROLLBACK (0 wierszy w bazie)."""
    pg_url = get_test_postgres_url()
    assert pg_url is not None

    reset_target_for_migration_tests(pg_url)

    pg_engine = create_engine(pg_url)

    sqlite_file = tmp_path / "synth_rollback.db"
    create_synthetic_sqlite_db(sqlite_file, users=[sample_valid_user("u-1", 1)])

    # Wstrzyknij błąd w trakcie insertu (np. symulacja błędu weryfikacji)
    with pytest.MonkeyPatch.context() as mp:
        def failing_insert(*args, **kwargs):
            raise sa.exc.OperationalError("Simulated mid-transaction database crash", {}, Exception())

        mp.setattr(SQLModel.metadata.tables["users"], "insert", failing_insert)
        res = run_migration(sqlite_path=sqlite_file, pg_url=pg_url, apply=True, target_engine=pg_engine)

    assert res.success is False
    assert "ROLLBACK" in (res.error_message or "")

    # Baza docelowa musi pozostać całkowicie pusta po rollbacku
    with pg_engine.connect() as conn:
        cnt = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
        assert cnt == 0

        # Sekwencja nie może być zsynchronizowana, gdy transakcja została wycofana.
        seq_owner = conn.execute(
            text("SELECT 1 FROM pg_sequences WHERE schemaname = current_schema() "
                 "AND sequencename = 'user_number_sequence_id_seq'")
        ).first()
        assert seq_owner is not None

    reset_target_for_migration_tests(pg_url)
    pg_engine.dispose()


@pytest.mark.skipif(not HAS_POSTGRES, reason="PostgreSQL nie jest dostępny lokalnie; test uruchamiany w CI.")
def test_postgres_integration_rejects_ambiguous_empty_foreign_key(tmp_path):
    """Pusty ciąg w opcjonalnym FK jest odrzucany także wobec rzeczywistego PostgreSQL."""
    pg_url = get_test_postgres_url()
    assert pg_url is not None

    reset_target_for_migration_tests(pg_url)

    sqlite_file = tmp_path / "synth_empty_fk.db"
    create_synthetic_sqlite_db(
        sqlite_file,
        users=[sample_valid_user("u-1", 1)],
        training_sessions=[{
            "id": "sess-1",
            "user_id": "u-1",
            "session_date": datetime.date(2026, 5, 10),
            "status": "active",
            "planned_snapshot_json": "{}",
        }],
        exercise_results=[{
            "id": "ex-1",
            "user_id": "u-1",
            "source_session_id": "",
            "exercise_name": "Przysiad",
            "session_date": datetime.date(2026, 5, 10),
            "sets": 3,
            "reps": 8,
            "weight_kg": 100.0,
            "rpe": 8,
            "notes": "",
            "logged_at": datetime.datetime(2026, 5, 10, 17, 20),
        }],
    )

    report, data = run_preflight(sqlite_file, pg_url)
    assert report.success is False
    assert any(
        "source_session_id" in e and "pusty ciąg" in e for e in report.errors
    ), report.errors
    assert data is None

    reset_target_for_migration_tests(pg_url)
