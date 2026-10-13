"""Tests for scripts/migrate_sqlite_to_postgres.py (Stage 20U.7A).

Zestaw syntetycznych testów jednostkowych i integracyjnych weryfikujący:
  - Walidację argumentów CLI i odrzucenie SQLite jako celu;
  - Maskowanie haseł i sekretów w connection stringach;
  - Otwieranie źródła SQLite ściśle w trybie tylko do odczytu (mode=ro) i brak modyfikacji źródła;
  - Obsługę nieistniejącego lub pustego źródła;
  - Wykrywanie brakujących tabel w bazie docelowej;
  - Ochronę przed importem do niepustej bazy docelowej (ochrona przed nadpisaniem);
  - Konwersję typów: Boolean (0/1 -> bool), DATE, DATETIME, liczby, NULL i wartości domyślne;
  - Wykrywanie błędnych formatów dat i znaczników czasu;
  - Wykrywanie osieroconych kluczy obcych i naruszeń unikalności;
  - Wykrywanie konfliktów w indeksie częściowym uq_training_active_user_day;
  - Zachowanie trybu dry-run (brak zmian w bazie docelowej);
  - Testy integracyjne na PostgreSQL (jeśli baza jest dostępna w środowisku/CI):
      * pełna migracja 12 tabel reprezentatywnych danych;
      * weryfikacja typów i integralności po imporcie;
      * ochrona przed ponownym uruchomieniem;
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
    classify_column_type,
    coerce_value,
    extract_and_convert_source_data,
    get_target_engine,
    inspect_target_schema,
    mask_database_url,
    normalize_pg_url,
    open_sqlite_readonly,
    run_migration,
    run_preflight,
    validate_relational_constraints,
)


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


def test_type_coercion_datetimes():
    """Poprawna konwersja ISO datetime strings na naive datetime.datetime."""
    val, err = coerce_value("2026-10-13 18:30:00", "datetime", "logged_at", nullable=False)
    assert val == datetime.datetime(2026, 10, 13, 18, 30, 0) and err is None

    val, err = coerce_value("2026-10-13T18:30:00.500000Z", "datetime", "logged_at", nullable=False)
    assert val == datetime.datetime(2026, 10, 13, 18, 30, 0, 500000) and err is None

    val, err = coerce_value("bad-time-stamp", "datetime", "logged_at", nullable=False)
    assert val is None and "nieprawidłowy format znacznika czasu" in err


def test_type_coercion_numbers_and_nulls():
    """Poprawna konwersja liczb i obsługa pustych stringów w kolumnach opcjonalnych."""
    val, err = coerce_value("123", "int", "age", nullable=False)
    assert val == 123 and err is None

    val, err = coerce_value("85.7", "float", "weight", nullable=False)
    assert val == 85.7 and err is None

    # Pusty ciąg w kolumnie opcjonalnej -> NULL
    val, err = coerce_value("", "float", "weight", nullable=True)
    assert val is None and err is None


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


# ─── 7. Testy Integracyjne PostgreSQL (aktywne w środowisku z bazą/CI) ─────────


@pytest.mark.skipif(not HAS_POSTGRES, reason="PostgreSQL nie jest dostępny lokalnie; test uruchamiany w CI.")
def test_postgres_integration_full_migration(tmp_path):
    """Pełna integracja z rzeczywistym PostgreSQL: migracja danych reprezentatywnych dla 12 tabel."""
    pg_url = get_test_postgres_url()
    assert pg_url is not None

    pg_engine = create_engine(pg_url)

    # 1. Przygotuj czysty schemat w PostgreSQL za pomocą SQLModel metadata
    SQLModel.metadata.drop_all(pg_engine)
    SQLModel.metadata.create_all(pg_engine)

    # 2. Utwórz reprezentatywną syntetyczną bazę SQLite
    sqlite_file = tmp_path / "synth_full.db"
    u1 = sample_valid_user("user-uuid-1", 1)
    seq1 = {"id": 1, "user_id": "user-uuid-1"}
    log1 = {
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
    }
    nut1 = {
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
    }
    nut_ad1 = {
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
    }
    sess1 = {
        "id": "sess-uuid-1",
        "user_id": "user-uuid-1",
        "session_date": datetime.date(2026, 5, 10),
        "status": "active",
        "planned_snapshot_json": '{"exercises": ["squat"]}',
        "started_at": datetime.datetime(2026, 5, 10, 17, 0),
        "notes": "sesja popołudniowa",
        "created_at": datetime.datetime(2026, 5, 10, 17, 0),
        "updated_at": datetime.datetime(2026, 5, 10, 17, 0),
    }
    set1 = {
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
    }
    ex_res1 = {
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
    }
    goal1 = {
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
    }
    apr1 = {
        "id": "apr-uuid-1",
        "user_id": "user-uuid-1",
        "source_session_ids_json": '["sess-uuid-1"]',
        "previous_plan_json": "{}",
        "applied_plan_json": "{}",
        "decision_summary_json": "{}",
        "version": 1,
        "created_at": datetime.datetime(2026, 5, 10, 22, 0),
    }
    drill1 = {
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
    }
    ass1 = {
        "id": "ass-uuid-1",
        "user_id": "user-uuid-1",
        "assessment_version": 1,
        "status": "completed",
        "assessment_date": datetime.date(2026, 5, 1),
        "training_level": "intermediate",
        "recovery_score": 8,
        "notes": "",
        "created_at": datetime.datetime(2026, 5, 1, 9, 0),
    }

    create_synthetic_sqlite_db(
        sqlite_file,
        users=[u1],
        user_sequences=[seq1],
        daily_logs=[log1],
        nutrition_entries=[nut1],
        nutrition_adaptations=[nut_ad1],
        training_sessions=[sess1],
        training_set_results=[set1],
        exercise_results=[ex_res1],
        goals=[goal1],
        adaptive_plan_revisions=[apr1],
        drill_results=[drill1],
        assessments=[ass1],
    )

    # 3. Wykonaj rzeczywistą migrację z flagą --apply
    res = run_migration(sqlite_path=sqlite_file, pg_url=pg_url, apply=True, target_engine=pg_engine)
    assert res.success is True
    assert res.applied is True

    # 4. Sprawdź rekordy w PostgreSQL
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

    # 5. Ochrona przed ponownym uruchomieniem: ponowna próba importu musi zostać zablokowana
    rerun_res = run_migration(sqlite_path=sqlite_file, pg_url=pg_url, apply=True, target_engine=pg_engine)
    assert rerun_res.success is False
    assert any("zawiera już 1 rekordów" in e for e in rerun_res.preflight_report.errors)

    # Posprzątaj po teście
    SQLModel.metadata.drop_all(pg_engine)
    pg_engine.dispose()


@pytest.mark.skipif(not HAS_POSTGRES, reason="PostgreSQL nie jest dostępny lokalnie; test uruchamiany w CI.")
def test_postgres_integration_rollback_on_error(tmp_path):
    """Błąd w trakcie wstawiania w transakcji wywołuje czysty ROLLBACK (0 wierszy w bazie)."""
    pg_url = get_test_postgres_url()
    assert pg_url is not None

    pg_engine = create_engine(pg_url)
    SQLModel.metadata.drop_all(pg_engine)
    SQLModel.metadata.create_all(pg_engine)

    sqlite_file = tmp_path / "synth_rollback.db"
    create_synthetic_sqlite_db(sqlite_file, users=[sample_valid_user("u-1", 1)])

    # Wstrzyknij błąd w trakcie insertu (np. symulacja błędu weryfikacji)
    with pytest.MonkeyPatch.context() as mp:
        original_insert = SQLModel.metadata.tables["users"].insert

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

    SQLModel.metadata.drop_all(pg_engine)
    pg_engine.dispose()
