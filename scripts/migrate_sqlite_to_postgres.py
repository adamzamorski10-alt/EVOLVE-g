#!/usr/bin/env python3
"""Offline SQLite -> PostgreSQL Migration Tool for EVOLVE (Stage 20U.7A).

Bezpieczne, atomowe narzędzie do migracji danych z lokalnego pliku bazy SQLite
do docelowej bazy PostgreSQL z rygorystycznym trybem preflight/dry-run.

Wymagania i zasady działania:
  1. Domyślnie działa WYŁĄCZNIE w trybie preflight (dry-run) -- nie wykonuje żadnych
     zapisów do bazy docelowej bez jawnej flagi `--apply`.
  2. Wymaga jawnego podania ścieżki źródłowej (`--sqlite-path`) oraz docelowego
     URL (`--pg-url`). Nigdy nie przyjmuje domyślnie `fitai.db` ani zmiennej środowiskowej
     bazy produkcyjnej.
  3. Źródłowy plik SQLite otwierany jest w trybie ściśle tylko do odczytu (URI mode=ro).
  4. Nie modyfikuje schematu bazy docelowej -- schemat musi być uprzednio przygotowany
     przez migracje Alembic (`alembic upgrade head`).
  5. Wszystkie hasła i wrażliwe parametry w URL połączenia są maskowane w logach i na wyjściu.
  6. Weryfikuje integralność danych: typy Boolean (0/1 -> True/False), daty (DATE),
     znaczniki czasu (TIMESTAMP), wartości NULL, relacje kluczy obcych (brak sierot)
     oraz unikalność kluczy i częściowych indeksów.
  7. Całość importu w trybie `--apply` realizowana jest w pojedynczej transakcji
     PostgreSQL -- jakikolwiek błąd wywołuje natychmiastowy rollback (all-or-nothing).
  8. Ochrona przed ponownym uruchomieniem: baza docelowa musi być całkowicie pusta;
     skrypt odrzuca import, jeśli w tabelach docelowych istnieją już rekordy.

Użycie:
  # Tryb walidacji / dry-run (domyślny):
  python scripts/migrate_sqlite_to_postgres.py --sqlite-path /path/to/source.db --pg-url postgresql+psycopg://user:pass@host:5432/db

  # Wykonanie rzeczywistej migracji:
  python scripts/migrate_sqlite_to_postgres.py --sqlite-path /path/to/source.db --pg-url postgresql+psycopg://user:pass@host:5432/db --apply
"""

from __future__ import annotations

import argparse
import datetime
import os
import re
import sqlite3
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

# Upewnij się, że katalog główny repozytorium jest w sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Zapobiegaj eager-bootstrapowi aplikacji przy imporcie modeli
os.environ["EVOLVE_ALEMBIC_CONTEXT"] = "1"

import sqlalchemy as sa
from sqlalchemy.engine import Engine, create_engine, make_url
from sqlalchemy.sql import func, select

from app.models import SQLModel

# ─── Stałe i kolejność zależności ─────────────────────────────────────────────

TABLE_ORDER: list[str] = [
    "users",
    "user_number_sequence",
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
]

REQUIRED_SOURCE_TABLES: set[str] = {
    "users",
}


# ─── Wyjątki ───────────────────────────────────────────────────────────────────


class MigrationError(Exception):
    """Bazowy wyjątek migracji."""


class PreflightError(MigrationError):
    """Błąd walidacji preflight."""


class TargetSchemaError(MigrationError):
    """Niezgodność schematu w bazie docelowej."""


class TargetNotEmptyError(MigrationError):
    """Baza docelowa zawiera już dane."""


class TargetDialectError(MigrationError):
    """Nieobsługiwany dialekt bazy docelowej."""


# ─── Struktury raportu ────────────────────────────────────────────────────────


@dataclass
class PreflightReport:
    success: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    source_counts: dict[str, int] = field(default_factory=dict)
    target_counts: dict[str, int] = field(default_factory=dict)
    sqlite_path: str = ""
    masked_pg_url: str = ""

    def summary(self) -> str:
        lines = [
            "=" * 70,
            "  EVOLVE -- Raport Preflight Migracji SQLite -> PostgreSQL",
            "=" * 70,
            f"  Źródło SQLite:  {self.sqlite_path}",
            f"  Cel PostgreSQL: {self.masked_pg_url}",
            f"  Status:         {'PASS' if self.success else 'FAILED'}",
            "",
            "  Rekordy źródłowe w SQLite:",
        ]
        for tbl in TABLE_ORDER:
            cnt = self.source_counts.get(tbl, 0)
            lines.append(f"    - {tbl:<26}: {cnt:>6} rekordów")

        if self.warnings:
            lines.append("\n  Ostrzeżenia:")
            for w in self.warnings:
                lines.append(f"    [WARN] {w}")

        if self.errors:
            lines.append("\n  Błędy walidacji (blokujące migrację):")
            for e in self.errors:
                lines.append(f"    [ERROR] {e}")

        lines.append("=" * 70)
        return "\n".join(lines)


@dataclass
class MigrationResult:
    success: bool
    applied: bool
    preflight_report: PreflightReport
    migrated_counts: dict[str, int] = field(default_factory=dict)
    duration_seconds: float = 0.0
    error_message: Optional[str] = None

    def summary(self) -> str:
        lines = [self.preflight_report.summary()]
        if self.applied:
            lines.extend([
                "",
                "=" * 70,
                "  WYNIK MIGRACJI ATOMOWEJ (APPLIED)",
                "=" * 70,
                f"  Status:    {'SUKCES (Zacommitowano transakcję)' if self.success else 'BŁĄD (Wykonano ROLLBACK)'}",
                f"  Czas:      {self.duration_seconds:.2f} s",
                "",
                "  Przeniesione rekordy:",
            ])
            for tbl in TABLE_ORDER:
                cnt = self.migrated_counts.get(tbl, 0)
                lines.append(f"    - {tbl:<26}: {cnt:>6} zaimportowanych")
            if self.error_message:
                lines.extend(["", f"  Błąd wykonania: {self.error_message}"])
            lines.append("=" * 70)
        else:
            lines.extend([
                "",
                "[INFO]  Tryb PREFLIGHT / DRY-RUN: baza docelowa NIE została zmodyfikowana.",
                "   Aby wykonać atomowy import, uruchom ponownie z flagą `--apply`.",
            ])
        return "\n".join(lines)


# ─── Narzędzia pomocnicze i maskowanie ─────────────────────────────────────────


def mask_database_url(raw_url: str) -> str:
    """Maskuje hasła i wrażliwe dane w URL połączenia bazodanowego."""
    if not raw_url:
        return "<brak URL>"
    try:
        u = make_url(raw_url)
        return u.render_as_string(hide_password=True)
    except Exception:
        # Bezpieczny fallback z regex
        return re.sub(r"://([^:@]+):([^@]+)@", r"://\1:***@", raw_url)


def normalize_pg_url(raw_url: str) -> str:
    """Normalizuje schemat połączenia PostgreSQL do sterownika psycopg."""
    scheme, sep, remainder = raw_url.partition("://")
    if sep and scheme.lower() in {"postgres", "postgresql"}:
        return f"postgresql+psycopg://{remainder}"
    return raw_url


def open_sqlite_readonly(sqlite_path: str | Path) -> sqlite3.Connection:
    """Otwiera bazę SQLite w rygorystycznym trybie tylko do odczytu (mode=ro)."""
    p = Path(sqlite_path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"Źródłowy plik SQLite nie istnieje: {p}")
    if not p.is_file():
        raise ValueError(f"Wskazana ścieżka SQLite nie jest plikiem: {p}")

    uri = f"file:{p.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def get_target_engine(pg_url: str) -> Engine:
    """Tworzy i weryfikuje silnik połączenia docelowej bazy PostgreSQL."""
    if not pg_url or not pg_url.strip():
        raise ValueError("URL bazy docelowej nie może być pusty.")

    lowered = pg_url.lower().strip()
    if lowered.startswith("sqlite:") or "sqlite" in lowered:
        raise TargetDialectError(
            "Docelowy URL musi wskazywać bazę PostgreSQL (np. postgresql+psycopg://...), "
            f"nie SQLite! Podano: {mask_database_url(pg_url)}"
        )

    normalized = normalize_pg_url(pg_url)
    engine = create_engine(normalized)
    if engine.dialect.name != "postgresql":
        raise TargetDialectError(
            f"Docelowy dialekt bazy musi być 'postgresql', otrzymano: '{engine.dialect.name}'"
        )
    return engine


# ─── Klasyfikacja i konwersja typów ───────────────────────────────────────────


def classify_column_type(col_type: Any) -> str:
    """Klasyfikuje typ kolumny SQLAlchemy/SQLModel na kanoniczny typ danych."""
    impl = getattr(col_type, "impl", col_type)
    if isinstance(impl, sa.Boolean):
        return "bool"
    if isinstance(impl, sa.DateTime):
        return "datetime"
    if isinstance(impl, sa.Date):
        return "date"
    if isinstance(impl, sa.Integer):
        return "int"
    if isinstance(impl, (sa.Float, sa.Numeric)):
        return "float"
    if isinstance(impl, (sa.String, sa.Text)):
        return "string"
    return "other"


def coerce_value(
    val: Any,
    col_type_kind: str,
    col_name: str,
    nullable: bool,
    default: Any = None,
) -> tuple[Any, Optional[str]]:
    """Konwertuje i waliduje pojedynczą wartość komórki zgodnie z modelem."""
    # Obsługa braku wartości / pustego ciągu
    if val is None:
        if not nullable:
            if default is not None and not callable(default):
                return default, None
            return None, f"Kolumna '{col_name}' nie dopuszcza wartości NULL, a otrzymano None."
        return None, None

    if col_type_kind == "bool":
        if isinstance(val, bool):
            return val, None
        if isinstance(val, (int, float)):
            if val == 1:
                return True, None
            if val == 0:
                return False, None
            return None, f"Kolumna '{col_name}' (bool): nieprawidłowa liczba: {val}"
        s = str(val).strip().lower()
        if not s:
            if nullable:
                return None, None
            return None, f"Kolumna '{col_name}' (bool): pusty ciąg dla kolumny NOT NULL."
        if s in ("true", "1", "t", "yes"):
            return True, None
        if s in ("false", "0", "f", "no"):
            return False, None
        return None, f"Kolumna '{col_name}' (bool): nieznana wartość logiczna: {val}"

    if col_type_kind == "date":
        if isinstance(val, datetime.date) and not isinstance(val, datetime.datetime):
            return val, None
        if isinstance(val, datetime.datetime):
            return val.date(), None
        s = str(val).strip()
        if not s:
            if nullable:
                return None, None
            return None, f"Kolumna '{col_name}' (date): pusta wartość dla kolumny NOT NULL."
        try:
            return datetime.date.fromisoformat(s[:10]), None
        except Exception:
            return None, f"Kolumna '{col_name}' (date): nieprawidłowy format daty: {val}"

    if col_type_kind == "datetime":
        if isinstance(val, datetime.datetime):
            return val.replace(tzinfo=None), None
        if isinstance(val, datetime.date):
            return datetime.datetime.combine(val, datetime.time.min), None
        s = str(val).strip()
        if not s:
            if nullable:
                return None, None
            return None, f"Kolumna '{col_name}' (datetime): pusta wartość dla kolumny NOT NULL."
        if s.endswith("Z"):
            s = s[:-1]
        try:
            return datetime.datetime.fromisoformat(s).replace(tzinfo=None), None
        except ValueError:
            for fmt in (
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
            ):
                try:
                    return datetime.datetime.strptime(s, fmt), None
                except ValueError:
                    pass
            return None, f"Kolumna '{col_name}' (datetime): nieprawidłowy format znacznika czasu: {val}"

    if col_type_kind == "int":
        if isinstance(val, int) and not isinstance(val, bool):
            return val, None
        s = str(val).strip()
        if not s:
            if nullable:
                return None, None
            return None, f"Kolumna '{col_name}' (int): pusta wartość dla kolumny NOT NULL."
        try:
            return int(float(s)), None
        except Exception:
            return None, f"Kolumna '{col_name}' (int): nieprawidłowa liczba całkowita: {val}"

    if col_type_kind == "float":
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            return float(val), None
        s = str(val).strip()
        if not s:
            if nullable:
                return None, None
            return None, f"Kolumna '{col_name}' (float): pusta wartość dla kolumny NOT NULL."
        try:
            return float(s), None
        except Exception:
            return None, f"Kolumna '{col_name}' (float): nieprawidłowa liczba zmiennoprzecinkowa: {val}"

    if col_type_kind == "string":
        res = str(val)
        return res, None

    return val, None


# ─── Inspekcja i Walidacja Relacyjna ──────────────────────────────────────────


def inspect_target_schema(engine: Engine) -> tuple[dict[str, int], list[str]]:
    """Sprawdza obecność wymaganych tabel i liczbę wierszy w bazie docelowej."""
    insp = sa.inspect(engine)
    existing_tables = set(insp.get_table_names())

    missing = [tbl for tbl in TABLE_ORDER if tbl not in existing_tables]
    errors: list[str] = []
    if missing:
        errors.append(
            f"W bazie docelowej brakuje wymaganych tabel: {missing}. "
            "Uruchom 'alembic upgrade head' na bazie docelowej przed migracją danych."
        )

    # Sprawdź czystość bazy docelowej (brak wcześniejszych danych)
    counts: dict[str, int] = {}
    with engine.connect() as conn:
        for tbl in TABLE_ORDER:
            if tbl in existing_tables:
                cnt = conn.execute(sa.text(f"SELECT COUNT(*) FROM {tbl}")).scalar() or 0
                counts[tbl] = cnt
                if cnt > 0:
                    errors.append(
                        f"Tabela docelowa '{tbl}' zawiera już {cnt} rekordów! "
                        "Baza docelowa musi być całkowicie pusta przed migracją, "
                        "aby zapobiec duplikacji danych i konfliktom kluczy."
                    )
            else:
                counts[tbl] = -1

    return counts, errors


def extract_and_convert_source_data(
    sqlite_conn: sqlite3.Connection,
) -> tuple[dict[str, list[dict[str, Any]]], list[str], list[str]]:
    """Pobiera i konwertuje dane ze źródła SQLite zgodnie z definicją SQLModel."""
    cur = sqlite_conn.cursor()
    src_tables_rows = cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    src_tables = {row[0] for row in src_tables_rows}

    errors: list[str] = []
    warnings: list[str] = []
    data_by_table: dict[str, list[dict[str, Any]]] = {}

    # 1. Sprawdź obecność krytycznych tabel źródłowych
    for req in REQUIRED_SOURCE_TABLES:
        if req not in src_tables:
            errors.append(f"W źródłowej bazie SQLite brakuje kluczowej tabeli '{req}'.")

    if errors:
        return {}, errors, warnings

    # 2. Pobierz kolumny i wiersze dla każdej tabeli z TABLE_ORDER
    for tbl_name in TABLE_ORDER:
        data_by_table[tbl_name] = []
        if tbl_name not in src_tables:
            warnings.append(f"Tabela '{tbl_name}' nie występuje w pliku SQLite -- 0 rekordów do migracji.")
            continue

        target_table = SQLModel.metadata.tables[tbl_name]
        src_cols = {
            r["name"] for r in cur.execute(f"PRAGMA table_info({tbl_name})").fetchall()
        }

        # Sprawdź czy kolumny NOT NULL bez domyślnych istnieją w źródle
        for col in target_table.columns:
            if not col.nullable and col.default is None and col.server_default is None:
                if col.name not in src_cols:
                    errors.append(
                        f"Tabela '{tbl_name}': wymagana kolumna NOT NULL '{col.name}' "
                        "nie istnieje w źródłowej tabeli SQLite."
                    )

        rows = cur.execute(f"SELECT * FROM {tbl_name}").fetchall()
        for idx, row in enumerate(rows, start=1):
            converted_row: dict[str, Any] = {}
            for col in target_table.columns:
                col_name = col.name
                col_type_kind = classify_column_type(col.type)

                raw_val = row[col_name] if col_name in src_cols else None
                default_val = col.default.arg if col.default is not None and not callable(col.default.arg) else None

                val, err = coerce_value(
                    raw_val,
                    col_type_kind,
                    col_name,
                    col.nullable,
                    default_val,
                )
                if err:
                    errors.append(f"[{tbl_name} wiersz {idx}] {err}")
                converted_row[col_name] = val

            data_by_table[tbl_name].append(converted_row)

    if errors:
        return data_by_table, errors, warnings

    # 3. Walidacja relacyjna i ograniczeń unikalności
    rel_errors = validate_relational_constraints(data_by_table)
    errors.extend(rel_errors)

    return data_by_table, errors, warnings


def validate_relational_constraints(
    data_by_table: dict[str, list[dict[str, Any]]],
) -> list[str]:
    """Weryfikuje unikalność kluczy, brak osieroconych kluczy obcych i indeksy częściowe."""
    errors: list[str] = []

    # Users
    users = data_by_table.get("users", [])
    user_ids: set[str] = set()
    user_keys: set[str] = set()
    user_numbers: set[int] = set()
    nicknames: set[str] = set()

    for u in users:
        uid = u.get("id")
        if not uid:
            errors.append("Tabela 'users': rekord z pustym kluczem głównym 'id'.")
        elif uid in user_ids:
            errors.append(f"Tabela 'users': zduplikowany klucz główny id='{uid}'.")
        else:
            user_ids.add(uid)

        uk = u.get("user_key")
        if not uk:
            errors.append(f"Tabela 'users' (id={uid}): brak wartości wymaganej 'user_key'.")
        elif uk in user_keys:
            errors.append(f"Tabela 'users': zduplikowany user_key='{uk}'.")
        else:
            user_keys.add(uk)

        un = u.get("user_number")
        if un is not None:
            if un in user_numbers:
                errors.append(f"Tabela 'users': zduplikowany user_number={un}.")
            else:
                user_numbers.add(un)

        nk = u.get("nickname")
        if nk:
            if nk in nicknames:
                errors.append(f"Tabela 'users': zduplikowany nickname='{nk}'.")
            else:
                nicknames.add(nk)

    # user_number_sequence
    seq_ids: set[int] = set()
    for s in data_by_table.get("user_number_sequence", []):
        sid = s.get("id")
        if sid in seq_ids:
            errors.append(f"Tabela 'user_number_sequence': zduplikowany id={sid}.")
        elif sid is not None:
            seq_ids.add(sid)

        uid = s.get("user_id")
        if uid and uid not in user_ids:
            errors.append(
                f"Tabela 'user_number_sequence' (id={sid}): osierocony user_id='{uid}' nie istnieje w 'users'."
            )

    # Tabele z bezpośrednim kluczem obcym user_id -> users.id
    user_fk_tables = [
        "daily_logs",
        "nutrition_entries",
        "nutrition_adaptations",
        "training_sessions",
        "goals",
        "adaptive_plan_revisions",
        "drill_results",
        "assessments",
    ]
    for tbl in user_fk_tables:
        for r in data_by_table.get(tbl, []):
            rid = r.get("id")
            uid = r.get("user_id")
            if uid and uid not in user_ids:
                errors.append(
                    f"Tabela '{tbl}' (id={rid}): osierocony user_id='{uid}' nie istnieje w 'users'."
                )

    # training_sessions: częściowy unikalny indeks uq_training_active_user_day
    # (user_id, session_date) dla status == 'active'
    active_sessions: set[tuple[str, Any]] = set()
    session_ids: set[str] = set()
    for ts in data_by_table.get("training_sessions", []):
        sid = ts.get("id")
        if sid:
            session_ids.add(sid)
        if ts.get("status") == "active":
            key = (ts.get("user_id"), ts.get("session_date"))
            if key in active_sessions:
                errors.append(
                    f"Tabela 'training_sessions': konflikt indeksu uq_training_active_user_day -- "
                    f"znaleziono wiele aktywnych sesji dla użytkownika '{key[0]}' w dniu {key[1]}."
                )
            else:
                active_sessions.add(key)

    # training_set_results: FK session_id + UQ (session_id, exercise_key, set_number)
    set_identities: set[tuple[str, str, int]] = set()
    for sr in data_by_table.get("training_set_results", []):
        srid = sr.get("id")
        sid = sr.get("session_id")
        uid = sr.get("user_id")
        if sid and sid not in session_ids:
            errors.append(
                f"Tabela 'training_set_results' (id={srid}): osierocony session_id='{sid}' nie istnieje w 'training_sessions'."
            )
        if uid and uid not in user_ids:
            errors.append(
                f"Tabela 'training_set_results' (id={srid}): osierocony user_id='{uid}' nie istnieje w 'users'."
            )
        ident = (sid, sr.get("exercise_key"), sr.get("set_number"))
        if ident in set_identities:
            errors.append(
                f"Tabela 'training_set_results': konflikt unikalności serii -- "
                f"sesja='{ident[0]}', ćwiczenie='{ident[1]}', seria={ident[2]}."
            )
        else:
            set_identities.add(ident)

    # exercise_results: FK source_session_id (nullable)
    for er in data_by_table.get("exercise_results", []):
        erid = er.get("id")
        ssid = er.get("source_session_id")
        if ssid and ssid not in session_ids:
            errors.append(
                f"Tabela 'exercise_results' (id={erid}): osierocony source_session_id='{ssid}' nie istnieje w 'training_sessions'."
            )

    # assessments: UQ (user_id, assessment_version)
    assessment_versions: set[tuple[str, int]] = set()
    for a in data_by_table.get("assessments", []):
        key = (a.get("user_id"), a.get("assessment_version"))
        if key in assessment_versions:
            errors.append(
                f"Tabela 'assessments': zduplikowana wersja assessmentu dla user_id='{key[0]}', wersja={key[1]}."
            )
        else:
            assessment_versions.add(key)

    # adaptive_plan_revisions: UQ (user_id, version)
    adaptive_versions: set[tuple[str, int]] = set()
    for apr in data_by_table.get("adaptive_plan_revisions", []):
        key = (apr.get("user_id"), apr.get("version"))
        if key in adaptive_versions:
            errors.append(
                f"Tabela 'adaptive_plan_revisions': zduplikowana wersja rewizji dla user_id='{key[0]}', wersja={key[1]}."
            )
        else:
            adaptive_versions.add(key)

    return errors


# ─── Główny silnik Preflight i Migracji ────────────────────────────────────────


def run_preflight(
    sqlite_path: str | Path,
    pg_url: str,
    target_engine: Optional[Engine] = None,
) -> tuple[PreflightReport, Optional[dict[str, list[dict[str, Any]]]]]:
    """Wykonuje kompletny preflight walidacji schematu i danych."""
    masked_url = mask_database_url(pg_url)
    report = PreflightReport(
        success=False,
        sqlite_path=str(Path(sqlite_path).resolve() if Path(sqlite_path).exists() else sqlite_path),
        masked_pg_url=masked_url,
    )

    # 1. Połączenie z SQLite (read-only)
    try:
        sqlite_conn = open_sqlite_readonly(sqlite_path)
    except Exception as exc:
        report.errors.append(f"Nie udało się otworzyć źródłowego pliku SQLite w trybie tylko do odczytu: {exc}")
        return report, None

    # 2. Połączenie i inspekcja bazy docelowej PostgreSQL
    engine = target_engine
    engine_created = False
    if engine is None:
        try:
            engine = get_target_engine(pg_url)
            engine_created = True
        except Exception as exc:
            report.errors.append(f"Nieprawidłowa konfiguracja docelowej bazy danych: {exc}")
            sqlite_conn.close()
            return report, None

    try:
        target_counts, schema_errors = inspect_target_schema(engine)
        report.target_counts = target_counts
        if schema_errors:
            report.errors.extend(schema_errors)
    except Exception as exc:
        report.errors.append(f"Błąd podczas inspekcji schematu docelowego PostgreSQL: {exc}")
    finally:
        if engine_created:
            engine.dispose()

    # 3. Ekstrakcja i walidacja danych ze źródła SQLite
    try:
        converted_data, data_errors, warnings = extract_and_convert_source_data(sqlite_conn)
        report.warnings.extend(warnings)
        if data_errors:
            report.errors.extend(data_errors)

        for tbl, rows in converted_data.items():
            report.source_counts[tbl] = len(rows)
    except Exception as exc:
        report.errors.append(f"Nieoczekiwany błąd podczas przetwarzania danych źródłowych: {exc}")
        converted_data = None
    finally:
        sqlite_conn.close()

    report.success = len(report.errors) == 0
    return report, (converted_data if report.success else None)


def run_migration(
    sqlite_path: str | Path,
    pg_url: str,
    apply: bool = False,
    target_engine: Optional[Engine] = None,
) -> MigrationResult:
    """Wykonuje migrację: preflight (domyślnie) lub transakcyjny import (--apply)."""
    t_start = time.perf_counter()

    # 1. Zawsze najpierw uruchom preflight
    report, converted_data = run_preflight(sqlite_path, pg_url, target_engine=target_engine)

    result = MigrationResult(
        success=report.success,
        applied=False,
        preflight_report=report,
    )

    if not report.success or not apply or converted_data is None:
        result.duration_seconds = time.perf_counter() - t_start
        return result

    # 2. Wykonanie w trybie --apply w jednej atomowej transakcji PostgreSQL
    result.applied = True
    engine = target_engine
    engine_created = False
    if engine is None:
        engine = get_target_engine(pg_url)
        engine_created = True

    try:
        with engine.connect() as conn:
            with conn.begin():  # Otwiera pojedynczą atomową transakcję
                # Ponowna weryfikacja czystości tabel wewnątrz transakcji
                for tbl_name in TABLE_ORDER:
                    tbl_obj = SQLModel.metadata.tables[tbl_name]
                    cnt = conn.execute(select(func.count()).select_from(tbl_obj)).scalar() or 0
                    if cnt > 0:
                        raise TargetNotEmptyError(
                            f"Tabela docelowa '{tbl_name}' zawiera {cnt} rekordów! "
                            "Przerwano migrację, aby nie nadpisać danych."
                        )

                # Wstawianie rekordów w kanonicznym porządku zależności
                migrated_counts: dict[str, int] = {}
                for tbl_name in TABLE_ORDER:
                    rows = converted_data.get(tbl_name, [])
                    tbl_obj = SQLModel.metadata.tables[tbl_name]
                    if rows:
                        conn.execute(tbl_obj.insert(), rows)
                    migrated_counts[tbl_name] = len(rows)

                # Weryfikacja liczby wierszy po imporcie (wewnątrz transakcji przed commitem)
                for tbl_name in TABLE_ORDER:
                    tbl_obj = SQLModel.metadata.tables[tbl_name]
                    cnt = conn.execute(select(func.count()).select_from(tbl_obj)).scalar() or 0
                    expected = migrated_counts[tbl_name]
                    if cnt != expected:
                        raise MigrationError(
                            f"Błąd weryfikacji tabeli '{tbl_name}': oczekiwano {expected} rekordów, "
                            f"a w bazie znajduje się {cnt}."
                        )

                # Synchronizacja sekwencji user_number_sequence jeśli istnieje sekwencja w Postgres
                if migrated_counts.get("user_number_sequence", 0) > 0:
                    max_seq = max(r["id"] for r in converted_data["user_number_sequence"])
                    try:
                        conn.execute(
                            sa.text("SELECT setval(pg_get_serial_sequence('user_number_sequence', 'id'), :m)"),
                            {"m": max_seq},
                        )
                    except Exception:
                        pass  # user_number_sequence nie używa SERIAL w obecnym schemacie

        # Transakcja zacommitowana pomyślnie
        result.success = True
        result.migrated_counts = migrated_counts
    except Exception as exc:
        result.success = False
        result.error_message = f"Transakcja wycofana (ROLLBACK). Błąd: {exc}"
    finally:
        if engine_created:
            engine.dispose()
        result.duration_seconds = time.perf_counter() - t_start

    return result


# ─── Punkt wejścia CLI ─────────────────────────────────────────────────────────


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="EVOLVE -- Narzędzie offline migracji danych SQLite -> PostgreSQL (Stage 20U.7A)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Wymagania wstępne:
  1. Schemat w bazie docelowej PostgreSQL musi zostać najpierw zainicjalizowany przez:
       alembic upgrade head
  2. Baza docelowa musi być pusta (brak wcześniejszych rekordów w 12 tabelach).
  3. Skrypt domyślnie uruchamia się w bezpiecznym trybie preflight (dry-run).
  4. Dodanie flagi `--apply` realizuje transakcyjny import all-or-nothing.
        """,
    )
    parser.add_argument(
        "--sqlite-path",
        required=True,
        type=str,
        help="Ścieżka do źródłowego pliku bazy SQLite (plik otwierany jest wyłącznie w trybie mode=ro).",
    )
    parser.add_argument(
        "--pg-url",
        required=True,
        type=str,
        help="URL połączenia z docelową bazą PostgreSQL (np. postgresql+psycopg://user:pass@host:5432/dbname).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        default=False,
        help="Wykonaj faktyczny import rekordów w pojedynczej transakcji. Domyślnie: tylko preflight/dry-run.",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        result = run_migration(
            sqlite_path=args.sqlite_path,
            pg_url=args.pg_url,
            apply=args.apply,
        )
        print(result.summary())
        return 0 if result.success else 1
    except Exception as exc:
        print(f"\n[ERROR] BŁĄD KRYTYCZNY NARZĘDZIA MIGRACYJNEGO: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
