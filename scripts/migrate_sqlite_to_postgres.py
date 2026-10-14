#!/usr/bin/env python3
"""Offline SQLite -> PostgreSQL Migration Tool for EVOLVE (Stage 20U.7C).

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
      przez migracje Alembic (`alembic upgrade head`). Narzędzie nie wywołuje
      `SQLModel.metadata.create_all()` ani żadnego DDL.
   5. Weryfikuje schemat docelowy w pełnym zakresie: tabele, kolumny, typy,
      nullability, klucze główne, klucze obce, ograniczenia unikalności i wymagane
      indeksy (w tym indeksy częściowe) na podstawie metadanych SQLModel.
   6. Weryfikuje `alembic_version` bazy docelowej względem RZECZYWISTEGO headu
      wyznaczonego z grafu migracji repozytorium (bez utrwalanej listy rewizji).
   7. Wszystkie hasła i wrażliwe parametry w URL połączenia są maskowane w logach i na wyjściu.
   8. Weryfikuje integralność danych: typy Boolean (0/1 -> True/False), daty (DATE),
      znaczniki czasu (TIMESTAMP), wartości NULL, relacje kluczy obcych (brak sierot),
      ograniczenia unikalności oraz indeksy częściowe.
   9. Klucze obce i ograniczenia unikalności są wyznaczane z metadanych SQLModel
      (nie z ręcznie utrzymywanej listy tabel), dzięki czemu uwzględniają też
      relacje `exercise_results` i `user_number_sequence`.
  10. Walidacja dat i znaczników czasu sprawdza CAŁY format (nie tylko prefiks):
      daty wymagają postaci `YYYY-MM-DD`, znaczniki czasu postaci
      `YYYY-MM-DD[ T]HH:MM[:SS[.ffffff]][Z|±HH:MM]`. Świadome strefowo znaczniki
      czasu są konwertowane do UTC i dopiero potem pozbawiane informacji o strefie
      (model wymaga naive UTC). Konwersja jest jawna i udokumentowana.
  11. Pusty ciąg w opcjonalnej kolumnie klucza obcego jest danym niejednoznacznym
      (kontrakt rozróżnia `NULL` = brak relacji) i przerywa preflight z czytelnym błędem.
      Narzędzie NIE normalizuje automatycznie pustych ciągów do NULL.
  12. Synchronizacja sekwencji PostgreSQL dotyczy wyłącznie istniejących sekwencji
      (`pg_get_serial_sequence`), które faktycznie tego wymagają. Brak sekwencji jest
      raportowany jako ostrzeżenie, a błąd jej synchronizacji przerywa transakcję
      (bez cichego ukrywania wyjątków).
  13. Całość importu w trybie `--apply` realizowana jest w pojedynczej transakcji
      PostgreSQL -- jakikolwiek błąd wywołuje natychmiastowy rollback (all-or-nothing).
  14. Ochrona przed ponownym uruchomieniem: baza docelowa musi być całkowicie pusta;
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
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

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

ALEMBIC_INI_PATH = _REPO_ROOT / "alembic.ini"

# Kolumny tekstowe, których wartości można bezpiecznie wypisać w komunikatach
# (klucze wewnętrzne/auth, dane osobowe takie jak nickname/email są pomijane).
SAFE_TEXT_IDENTIFIER_COLUMNS: frozenset[str] = frozenset({"user_key"})


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


class PartialPredicateError(MigrationError):
    """Nie można zweryfikować predykatu indeksu częściowego."""


class SequenceSyncError(MigrationError):
    """Krytyczny błąd synchronizacji sekwencji PostgreSQL."""


# ─── Struktury raportu ────────────────────────────────────────────────────────


@dataclass
class PreflightReport:
    success: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
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

        if self.notes:
            lines.append("\n  Informacje:")
            for n in self.notes:
                lines.append(f"    [INFO] {n}")

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


# ─── Introspekcja metadanych SQLModel ──────────────────────────────────────────


@dataclass(frozen=True)
class ForeignKeySpec:
    """Rzeczywista relacja klucza obcego wyznaczona z metadanych SQLModel."""

    table: str
    column: str
    ref_table: str
    ref_column: str

    def describe(self) -> str:
        return f"{self.table}.{self.column} -> {self.ref_table}.{self.ref_column}"


@dataclass(frozen=True)
class UniqueSpec:
    """Wymagane ograniczenie unikalności wyznaczone z metadanych SQLModel.

    `kind` opisuje źródło ograniczenia (`index`, `constraint` albo `column`)
    i służy do czytelnej komunii komunikatów. `predicate` jest ustawione dla
    indeksów częściowych (np. `uq_training_active_user_day` dla `status = 'active'`).
    """

    table: str
    label: str
    columns: Tuple[str, ...]
    kind: str = "column"
    predicate: Optional[str] = None

    @property
    def key_columns_label(self) -> str:
        return ", ".join(self.columns)

    @property
    def conflict_label(self) -> str:
        """Nazwa użyta w komunikacie o konflikcie (kompatybilna z wcześniejszymi raportami)."""
        if self.kind == "index":
            return f"indeksu {self.label}"
        if self.kind == "constraint":
            return f"ograniczenia unikalności {self.label}"
        return f"unikalności kolumny {self.label}"


_MODEL_TABLES: dict[str, sa.Table] = {
    tbl.name: tbl for tbl in SQLModel.metadata.tables.values()
}


def model_table(name: str) -> sa.Table:
    """Zwraca tabelę SQLModel po nazwie (błąd przy nieznanym modelu)."""
    try:
        return _MODEL_TABLES[name]
    except KeyError as exc:  # pragma: no cover - ochrona regresji modelu
        raise MigrationError(f"Model SQLModel nie definiuje tabeli '{name}'.") from exc


def build_foreign_key_map(tables: Optional[Iterable[str]] = None) -> Dict[str, List[ForeignKeySpec]]:
    """Buduje mapę WSZYSTKICH rzeczywistych kluczy obcych z metadanych SQLModel.

    Nie korzysta z ręcznie utrzymywanej listy tabel -- każde `Field(foreign_key=...)`
    jest wykrywane automatycznie, dzięki czemu relacje `exercise_results`
    (source_session_id) ani `user_number_sequence` (user_id) nie mogą zostać pominięte.
    """
    names = list(tables) if tables is not None else list(_MODEL_TABLES)
    fk_map: Dict[str, List[ForeignKeySpec]] = {}
    for table_name in names:
        table = model_table(table_name)
        specs: List[ForeignKeySpec] = []
        for fk in sorted(table.foreign_keys, key=lambda f: f.parent.name):
            specs.append(
                ForeignKeySpec(
                    table=table_name,
                    column=fk.parent.name,
                    ref_table=fk.column.table.name,
                    ref_column=fk.column.name,
                )
            )
        if specs:
            fk_map[table_name] = specs
    return fk_map


def build_insert_order(tables: Optional[Iterable[str]] = None) -> List[str]:
    """Wyznacz kolejność importu faktycznie zależną od FK (sortowanie topologiczne).

    Kolejność nie jest wpisana na twardo -- wynika z grafu zależności metadanych,
    więc nowe relacje nie mogą spowodować insertu przed wierszem rodzica.
    """
    names = list(tables) if tables is not None else sorted(_MODEL_TABLES)
    name_set = set(names)
    deps: Dict[str, Set[str]] = {}
    for table_name in names:
        table = model_table(table_name)
        deps[table_name] = {
            fk.column.table.name
            for fk in table.foreign_keys
            if fk.column.table.name in name_set and fk.column.table.name != table_name
        }

    ordered: List[str] = []
    remaining = sorted(names)
    while remaining:
        ready = [name for name in remaining if not (deps[name] - set(ordered))]
        if not ready:
            raise MigrationError(
                "Nie udało się wyznaczyć kolejności importu -- cykl lub nieznana zależność FK "
                f"wśród tabel: {sorted(remaining)}"
            )
        for name in ready:
            ordered.append(name)
            remaining.remove(name)
    return ordered


def _index_predicate(index: sa.Index) -> Optional[str]:
    """Zwraca tekst predykatu indeksu częściowego (lub None dla pełnego indeksu)."""
    for dialect_key in ("postgresql", "sqlite"):
        options = index.dialect_options.get(dialect_key) or {}
        where = options.get("where")
        if where is not None:
            return str(where).strip()
    return None


def build_unique_specs(tables: Optional[Iterable[str]] = None) -> List[UniqueSpec]:
    """Buduje pełną listę wymaganych ograniczeń unikalności z metadanych.

    Uwzględnia `UniqueConstraint`, unikalne indeksy (w tym częściowe) oraz
    unikalność na poziomie kolumny -- między innymi
    `user_number_sequence.user_id`.
    """
    names = list(tables) if tables is not None else sorted(_MODEL_TABLES)
    specs: Dict[Tuple[str, Tuple[str, ...]], UniqueSpec] = {}

    def _register(spec: UniqueSpec) -> None:
        specs.setdefault((spec.table, spec.columns), spec)

    for table_name in names:
        table = model_table(table_name)
        table_label = table_name

        for constraint in sorted(table.constraints, key=lambda c: type(c).__name__):
            if not isinstance(constraint, sa.UniqueConstraint):
                continue
            columns = tuple(c.name for c in constraint.columns)
            label = constraint.name or f"{table_label}: unique ({', '.join(columns)})"
            _register(
                UniqueSpec(table=table_name, label=label, columns=columns, kind="constraint")
            )

        for index in sorted(table.indexes, key=lambda i: i.name):
            if not index.unique:
                continue
            columns = tuple(c.name for c in index.columns)
            _register(
                UniqueSpec(
                    table=table_name,
                    label=index.name,
                    columns=columns,
                    kind="index",
                    predicate=_index_predicate(index),
                )
            )

        for column in sorted(table.columns, key=lambda c: c.name):
            if not column.unique:
                continue
            _register(
                UniqueSpec(
                    table=table_name,
                    label=column.name,
                    columns=(column.name,),
                    kind="column",
                )
            )

    return sorted(specs.values(), key=lambda s: (s.table, s.columns))


def build_required_indexes(tables: Optional[Iterable[str]] = None) -> List[sa.Index]:
    """Zwraca indeksy wymagane przez model (wymagane w bazie docelowej)."""
    names = list(tables) if tables is not None else sorted(_MODEL_TABLES)
    indexes: List[sa.Index] = []
    for table_name in names:
        indexes.extend(model_table(table_name).indexes)
    return sorted(indexes, key=lambda i: (i.table.name, i.name))


def is_safe_to_echo(column: sa.Column) -> bool:
    """Czy wartość kolumny można wypisać w komunikacie błędu.

    Klucze główne, klucze obce oraz wewnętrzny `user_key` są bezpieczne.
    Wartości typów nienumerycznych pochodzące od użytkownika (np. `nickname`,
    `email`, notatki) nie są wypisywane, aby nie logować danych osobowych.
    """
    if column.primary_key or column.foreign_keys:
        return True
    if column.name in SAFE_TEXT_IDENTIFIER_COLUMNS:
        return True
    if classify_column_type(column.type) in {"int", "float", "bool", "date", "datetime"}:
        return True
    return False


# ─── Kolejność importu i integralność modelu ───────────────────────────────────


def verify_insert_order(order: Sequence[str], tables: Optional[Iterable[str]] = None) -> None:
    """Weryfikuje, że kolejność importu spełnia wszystkie rzeczywiste więzy FK."""
    expected = set(tables) if tables is not None else set(_MODEL_TABLES)
    if set(order) != expected:
        raise MigrationError(
            "Kolejność importu nie obejmuje wszystkich tabel modelu: "
            f"brakuje={sorted(expected - set(order))}, nadmiar={sorted(set(order) - expected)}"
        )

    fk_map = build_foreign_key_map(order)
    for table_name, specs in fk_map.items():
        for spec in specs:
            if spec.ref_table == table_name:
                continue
            if spec.ref_table not in order:
                raise MigrationError(
                    f"Relacja {spec.describe()} wskazuje tabelę spoza kolejności importu."
                )
            if order.index(table_name) < order.index(spec.ref_table):
                raise MigrationError(
                    f"Kolejność importu narusza relację {spec.describe()}: "
                    f"'{table_name}' wstawiana przed '{spec.ref_table}'."
                )


_INSERT_ORDER: List[str] = build_insert_order()


# ─── Predykaty indeksów częściowych ───────────────────────────────────────────

_PREDICATE_TOKEN_RE = re.compile(
    r"\s*(?:(?P<qstr>'(?:[^']|'')*')"
    r"|(?P<op>>=|<=|<>|!=|=|>|<|\(|\))"
    r"|(?P<word>[A-Za-z_][A-Za-z0-9_.]*)"
    r"|(?P<num>-?\d+(?:\.\d+)?))"
)

_PREDICATE_KEYWORDS = {"AND", "OR", "NOT", "IS", "NULL", "TRUE", "FALSE"}
_LITERAL_TOKENS = {"literal", "TRUE", "FALSE", "NULL"}


def _tokenize_predicate(predicate: str) -> List[Tuple[str, Any]]:
    """Dzieli tekst predykatu (np. `status = 'active'`) na tokeny."""
    tokens: List[Tuple[str, Any]] = []
    pos = 0
    while pos < len(predicate):
        match = _PREDICATE_TOKEN_RE.match(predicate, pos)
        if match is None:
            if predicate[pos:].strip() == "":
                break
            raise PartialPredicateError(
                f"Nie udało się sparsować predykatu indeksu częściowego: '{predicate}'."
            )
        pos = match.end()
        if match.lastgroup == "qstr":
            tokens.append(("literal", match.group("qstr")[1:-1].replace("''", "'")))
        elif match.lastgroup == "op":
            tokens.append(("op", match.group("op")))
        elif match.lastgroup == "word":
            word = match.group("word")
            if word.upper() in _PREDICATE_KEYWORDS:
                tokens.append((word.upper(), word))
            else:
                tokens.append(("ident", word))
        elif match.lastgroup == "num":
            raw = match.group("num")
            tokens.append(("literal", float(raw) if "." in raw else int(raw)))
    if not tokens:
        raise PartialPredicateError(f"Predykat indeksu częściowego jest pusty: '{predicate}'.")
    return tokens


@lru_cache(maxsize=256)
def _parse_predicate(predicate: str) -> Tuple[List[Tuple[str, Any]], Callable[[Mapping[str, Any]], bool]]:
    """Parsuje tekst predykatu do drzewa tokenów i funkcji oceny wiersza.

    Obsługiwana gramatyka (jedyjna forma występująca w modelu):
    `porównanie [AND|OR porównanie]*`, gdzie porównanie to
    `kolumna [=|!=|<>|<|>|<=|>=] literal` bądź `kolumna IS [NOT] NULL`,
    z opcjonalnym nawiasem oraz prefiksem `NOT`.
    """
    tokens = _tokenize_predicate(predicate)
    pos = 0

    def peek() -> Optional[Tuple[str, Any]]:
        return tokens[pos] if pos < len(tokens) else None

    def literal_value(token: Tuple[str, Any]) -> Any:
        kind, value = token
        if kind == "TRUE":
            return True
        if kind == "FALSE":
            return False
        if kind == "NULL":
            return None
        return value

    def parse_or() -> Callable[[Mapping[str, Any]], bool]:
        nonlocal pos
        left = parse_and()
        while peek() is not None and peek()[0] == "OR":
            pos += 1
            right = parse_and()
            left_fn, right_fn = left, right
            left = lambda row, l=left_fn, r=right_fn: bool(l(row) or r(row))
        return left

    def parse_and() -> Callable[[Mapping[str, Any]], bool]:
        nonlocal pos
        left = parse_not()
        while peek() is not None and peek()[0] == "AND":
            pos += 1
            right = parse_not()
            left_fn, right_fn = left, right
            left = lambda row, l=left_fn, r=right_fn: bool(l(row) and r(row))
        return left

    def parse_not() -> Callable[[Mapping[str, Any]], bool]:
        nonlocal pos
        if peek() is not None and peek()[0] == "NOT":
            pos += 1
            inner = parse_not()
            return lambda row, i=inner: not i(row)
        return parse_primary()

    def parse_primary() -> Callable[[Mapping[str, Any]], bool]:
        nonlocal pos
        token = peek()
        if token is None:
            raise PartialPredicateError(f"Nie udało się sparsować predykatu '{predicate}'.")
        if token[0] == "(":
            pos += 1
            inner = parse_or()
            if peek() is None or peek()[0] != ")":
                raise PartialPredicateError(
                    f"Brak zamknięcia nawiasu w predykacie indeksu częściowego: '{predicate}'."
                )
            pos += 1
            return inner
        if token[0] == "ident":
            column_name = token[1]
            pos += 1
            nxt = peek()
            if nxt is not None and nxt[0] == "IS":
                pos += 1
                negate = False
                if peek() is not None and peek()[0] == "NOT":
                    pos += 1
                    negate = True
                value_token = peek()
                if value_token is None or value_token[0] not in _LITERAL_TOKENS:
                    raise PartialPredicateError(
                        f"Niepoprawne wyrażenie IS w predykacie indeksu częściowego: '{predicate}'."
                    )
                pos += 1
                literal = literal_value(value_token)

                def evaluate_is(
                    row: Mapping[str, Any],
                    col: str = column_name,
                    lit: Any = literal,
                    negated: bool = negate,
                ) -> bool:
                    result = (row.get(col) is None) if lit is None else (row.get(col) == lit)
                    return (not result) if negated else result

                return evaluate_is
            if nxt is not None and nxt[0] == "op":
                operator = nxt[1]
                pos += 1
                value_token = peek()
                if value_token is None or value_token[0] not in _LITERAL_TOKENS:
                    raise PartialPredicateError(
                        "Predykat indeksu częściowego porównuje kolumnę z wartością, "
                        "której nie można ustalić statycznie."
                    )
                pos += 1
                literal = literal_value(value_token)
                return _comparison_callable(predicate, column_name, operator, literal)
            raise PartialPredicateError(
                f"Predykat indeksu częściowego zawiera nierozpoznane wyrażenie: '{predicate}'."
            )
        if token[0] in {"literal", "TRUE", "FALSE"}:
            pos += 1
            literal = literal_value(token)
            return lambda row, lit=literal: bool(lit)
        raise PartialPredicateError(f"Nie udało się sparsować predykatu '{predicate}'.")

    matcher = parse_or()
    if pos != len(tokens):
        raise PartialPredicateError(
            f"Predykat indeksu częściowego zawiera nadmiarowe tokeny: '{predicate}'."
        )
    return tokens, matcher


def _comparison_callable(
    predicate: str,
    column_name: str,
    operator: str,
    literal: Any,
) -> Callable[[Mapping[str, Any]], bool]:
    """Buduje porównanie wartości wiersza z literałem zachowując semantykę SQL NULL."""
    if literal is None:
        # `col = NULL` oraz `col <> NULL` są w SQL nieprawdziwe.
        return lambda row: False

    def compare(row: Mapping[str, Any]) -> bool:
        actual = row.get(column_name)
        if actual is None:
            return False
        try:
            if operator in {"=", "=="}:
                return bool(actual == literal)
            if operator in {"!=", "<>"}:
                return bool(actual != literal)
            if operator == ">":
                return bool(actual > literal)
            if operator == "<":
                return bool(actual < literal)
            if operator == ">=":
                return bool(actual >= literal)
            if operator == "<=":
                return bool(actual <= literal)
        except TypeError as exc:
            raise PartialPredicateError(
                f"Predykat indeksu częściowego: nieporównywalne wartości w kolumnie "
                f"'{column_name}' predykatu '{predicate}'."
            ) from exc
        raise PartialPredicateError(
            f"Nieobsługiwany operator '{operator}' w predykacie indeksu częściowego: '{predicate}'."
        )

    return compare


def row_matches_partial_predicate(
    predicate: str,
    row: Mapping[str, Any],
    table_name: str,
    row_index: int,
    row_label: str,
) -> bool:
    """Sprawdza, czy wiersz spełnia predykat indeksu częściowego (błąd jest krytyczny)."""
    try:
        _, matcher = _parse_predicate(predicate)
        return bool(matcher(row))
    except PartialPredicateError as exc:
        raise PreflightError(
            f"Tabela '{table_name}' (wiersz {row_index}, wiersz źródłowy {row_label}): {exc}"
        ) from exc


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


def classify_type_repr(type_repr: str) -> str:
    """Klasyfikuje typ bazy docelowej (tekst z inspektora) na ten sam klasifikator."""
    normalized = " ".join(type_repr.upper().split())
    if normalized in {"BOOLEAN", "BOOL"}:
        return "bool"
    if "TIMESTAMP" in normalized or "DATETIME" in normalized:
        return "datetime"
    if normalized.startswith("DATE"):
        return "date"
    if normalized in {"DOUBLE PRECISION", "REAL", "FLOAT"} or "NUMERIC" in normalized or "DECIMAL" in normalized:
        return "float"
    if "INT" in normalized:
        return "int"
    if "CHAR" in normalized or "TEXT" in normalized or "STRING" in normalized or "CLOB" in normalized:
        return "string"
    return "other"


_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DATETIME_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2}(\.\d{1,6})?)?(Z|[+-]\d{2}:\d{2})?$"
)


def to_naive_utc(value: datetime.datetime) -> datetime.datetime:
    """Konwertuje świadomy strefowo `datetime` na czas UTC i usuwa strefę.

    Model aplikacji zakłada naive UTC (patrz `app/models.py`), dlatego konwersja
    do UTC musi nastąpić PRZED usunięciem `tzinfo`. Dla wartości już svobodnych
    (tzinfo=None) nie jest wykonywana żadna konwersja.
    """
    if value.tzinfo is None:
        return value
    return value.astimezone(datetime.timezone.utc).replace(tzinfo=None)


def _parse_datetime_text(raw: str) -> datetime.datetime:
    """Parsuje tekst daty/czasu po zweryfikowaniu PEŁNEGO formatu.

    Samodzielna data (`YYYY-MM-DD`) jest jednoznacznym zapisem północy,
    dlatego jest akceptowana; każdy inny prefiks bez pełnej postaci jest odrzucany.
    """
    if _DATE_RE.match(raw):
        return datetime.datetime.fromisoformat(raw)
    if not _DATETIME_RE.match(raw):
        raise ValueError(raw)
    text = raw[:-1] if raw.endswith("Z") else raw
    parsed = datetime.datetime.fromisoformat(text)
    if parsed.tzinfo is not None:
        parsed = to_naive_utc(parsed)
    return parsed


def _parse_datetime_offset_text(raw: str) -> datetime.datetime:
    """Wariant `fromisoformat` obsługujący sufiks `Z` (Python < 3.11) oraz daty."""
    return _parse_datetime_text(raw)


def _parse_date_text(raw: str) -> datetime.date:
    """Parsuje tekst daty wymagając DOKŁADNIE formatu `YYYY-MM-DD` (bez przedłużenia)."""
    if not _DATE_RE.match(raw):
        raise ValueError(raw)
    try:
        return datetime.date.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(raw) from exc


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
        if isinstance(val, datetime.datetime):
            # Świadome strefowo datetimes muszą trafić do UTC przed wielokrotnym użyciem.
            return to_naive_utc(val).date(), None
        if isinstance(val, datetime.date):
            return val, None
        s = str(val).strip()
        if not s:
            if nullable:
                return None, None
            return None, f"Kolumna '{col_name}' (date): pusta wartość dla kolumny NOT NULL."
        try:
            return _parse_date_text(s), None
        except ValueError:
            if _DATETIME_RE.match(s):
                try:
                    return _parse_datetime_offset_text(s).date(), None
                except ValueError:
                    pass
            return None, (
                f"Kolumna '{col_name}' (date): nieprawidłowy format daty: {val} "
                "(wymagany format YYYY-MM-DD)."
            )

    if col_type_kind == "datetime":
        if isinstance(val, datetime.datetime):
            return to_naive_utc(val), None
        if isinstance(val, datetime.date):
            return datetime.datetime.combine(val, datetime.time.min), None
        s = str(val).strip()
        if not s:
            if nullable:
                return None, None
            return None, f"Kolumna '{col_name}' (datetime): pusta wartość dla kolumny NOT NULL."
        try:
            return _parse_datetime_offset_text(s), None
        except ValueError:
            return None, (
                f"Kolumna '{col_name}' (datetime): nieprawidłowy format znacznika czasu: {val} "
                "(wymagany format YYYY-MM-DD[ T]HH:MM[:SS[.ffffff]][Z|±HH:MM])."
            )

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
        if isinstance(val, (int, float, Decimal)) and not isinstance(val, bool):
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
        if isinstance(val, (bytes, bytearray)):
            return val.decode("utf-8", errors="replace"), None
        return str(val), None

    return val, None


# ─── Weryfikacja wersji Alembic (head z grafu migracji) ───────────────────────


def expected_alembic_heads(ini_path: Path | None = None) -> list[str]:
    """Zwraca rzeczywisty head grafu migracji Alembic z repozytorium."""
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    path = ini_path or ALEMBIC_INI_PATH
    if not path.exists():
        raise MigrationError(
            f"Nie znaleziono konfiguracji Alembic ({path}) -- "
            "nie można zweryfikować oczekiwanej wersji schematu."
        )
    config = Config(str(path))
    script_dir = ScriptDirectory.from_config(config)
    return list(script_dir.get_heads())


def read_target_alembic_revisions(engine: Engine) -> list[str]:
    """Odczytuje zapisane rewizje `alembic_version` z bazy docelowej."""
    insp = sa.inspect(engine)
    if "alembic_version" not in set(insp.get_table_names()):
        raise TargetSchemaError(
            "W bazie docelowej brakuje tabeli 'alembic_version'. "
            "Schemat musi zostać zainicjalizowany przez 'alembic upgrade head'."
        )
    with engine.connect() as conn:
        rows = conn.execute(sa.text("SELECT version_num FROM alembic_version")).scalars().all()
    return [str(r) for r in rows]


def verify_alembic_version(engine: Engine) -> Tuple[Optional[list[str]], Optional[list[str]], list[str]]:
    """Porównuje `alembic_version` celu z rzeczywistym headem repozytorium.

    Zwraca `(zapisane_w_celu, oczekiwane_heady, błędy)`.
    """
    errors: list[str] = []
    expected: Optional[list[str]] = None
    try:
        expected = expected_alembic_heads()
    except Exception as exc:
        errors.append(
            f"Nie udało się wyznaczyć oczekiwanego headu migracji Alembic: {exc}"
        )

    try:
        current = read_target_alembic_revisions(engine)
    except TargetSchemaError as exc:
        return None, expected, [str(exc)]
    except Exception as exc:
        return None, expected, [f"Nie udało się odczytać 'alembic_version' z bazy docelowej: {exc}"]

    if expected is not None:
        if set(current) != set(expected):
            errors.append(
                "Wersja schematu bazy docelowej jest niezgodna z repozytorium -- "
                f"alembic_version={sorted(set(current))}, oczekiwany head={sorted(set(expected))}. "
                "Uruchom 'alembic upgrade head' na bazie docelowej przed migracją danych."
            )
        elif len(current) != len(set(current)):
            errors.append(
                "Tabela 'alembic_version' zawiera zduplikowane rewizje: "
                f"{current}. Schemat docelowy jest uszkodzony."
            )
    return current, expected, errors


# ─── Inspekcja schematu bazy docelowej ────────────────────────────────────────


def _table_rows(conn: Any, table_name: str) -> Any:
    return conn.execute(sa.text(f"SELECT COUNT(*) FROM {table_name}")).scalar()


def inspect_target_schema(engine: Engine) -> tuple[dict[str, int], list[str]]:
    """Sprawdza schemat docelowy: tabele, wypełnienie, wersję Alembica i pełną zgodność.

    Narzędzie NIE tworzy schematu -- weryfikuje wyłącznie to, co przygotował Alembic.
    """
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
                cnt = _table_rows(conn, tbl) or 0
                counts[tbl] = cnt
                if cnt > 0:
                    errors.append(
                        f"Tabela docelowa '{tbl}' zawiera już {cnt} rekordów! "
                        "Baza docelowa musi być całkowicie pusta przed migracją, "
                        "aby zapobiec duplikacji danych i konfliktom kluczy."
                    )
            else:
                counts[tbl] = -1

    if missing:
        return counts, errors

    # Weryfikacja pełnego schematu względem metadanych modelu.
    errors.extend(verify_target_schema_against_models(insp, existing_tables))

    # Weryfikacja wersji schematu względem rzeczywistego headu grafu migracji.
    errors.extend(verify_alembic_version(engine)[2])

    return counts, errors


def _format_type_mismatch(table_name: str, column_name: str, expected: str, actual: str) -> str:
    return (
        f"Tabela '{table_name}', kolumna '{column_name}': niezgodny typ — "
        f"model wymaga '{expected}', baza docelowa ma '{actual}'."
    )


def verify_target_schema_against_models(
    insp: Any,
    existing_tables: Optional[Set[str]] = None,
) -> list[str]:
    """Porównuje schemat docelowy z metadanymi SQLModel (kolumny, PK, FK, UQ, indeksy)."""
    errors: list[str] = []
    known_tables = set(existing_tables) if existing_tables is not None else set(insp.get_table_names())

    for table_name in TABLE_ORDER:
        table = model_table(table_name)
        if table_name not in known_tables:
            continue  # brak tabeli jest już zgłoszony przez inspect_target_schema

        target_columns = {col["name"]: col for col in insp.get_columns(table_name)}
        columns_checked: set[str] = set()

        for column in table.columns:
            columns_checked.add(column.name)
            target_column = target_columns.get(column.name)
            if target_column is None:
                errors.append(
                    f"Tabela '{table_name}': brak kolumny '{column.name}' wymaganej przez model."
                )
                continue

            expected_kind = classify_column_type(column.type)
            actual_kind = classify_type_repr(str(target_column["type"]))
            if expected_kind != "other" and expected_kind != actual_kind:
                errors.append(
                    _format_type_mismatch(
                        table_name, column.name, expected_kind, str(target_column["type"])
                    )
                )

            if bool(column.nullable) != bool(target_column["nullable"]):
                errors.append(
                    f"Tabela '{table_name}', kolumna '{column.name}': niezgodna nullability — "
                    f"model wymaga nullable={column.nullable}, "
                    f"baza docelowa ma nullable={target_column['nullable']}."
                )

        for extra in sorted(set(target_columns) - columns_checked):
            errors.append(
                f"Tabela '{table_name}': kolumna '{extra}' istnieje w bazie docelowej, "
                "ale nie występuje w modelu SQLModel."
            )

        # Klucz główny
        target_pk = insp.get_pk_constraint(table_name)
        target_pk_columns = list(target_pk.get("constrained_columns") or [])
        model_pk_columns = [col.name for col in table.primary_key.columns]
        if target_pk_columns != model_pk_columns:
            errors.append(
                f"Tabela '{table_name}': niezgodny klucz główny — "
                f"model wymaga {model_pk_columns}, baza docelowa ma {target_pk_columns}."
            )

        # Klucze obce
        target_fks = {
            (tuple(fk.get("constrained_columns") or []), fk.get("referred_table"),
             tuple(fk.get("referred_columns") or []))
            for fk in insp.get_foreign_keys(table_name)
        }
        for spec in build_foreign_key_map([table_name]).get(table_name, []):
            expected_fk = ((spec.column,), spec.ref_table, (spec.ref_column,))
            if expected_fk not in target_fks:
                errors.append(
                    f"Tabela '{table_name}': brak klucza obcego {spec.describe()} "
                    "w bazie docelowej."
                )

        # Ograniczenia unikalności (m.in. user_number_sequence.user_id)
        target_unique = {
            tuple(sorted(uc.get("column_names") or []))
            for uc in insp.get_unique_constraints(table_name)
        }
        target_indexes = {
            idx.get("name"): (
                tuple(sorted(idx.get("column_names") or [])),
                bool(idx.get("unique")),
            )
            for idx in insp.get_indexes(table_name)
        }

        for spec in build_unique_specs([table_name]):
            model_columns = tuple(sorted(spec.columns))
            as_unique_constraint = model_columns in target_unique
            as_unique_index = model_columns in {
                cols for cols, is_unique in target_indexes.values() if is_unique
            }
            if not (as_unique_constraint or as_unique_index):
                errors.append(
                    f"Tabela '{table_name}': brak wymaganej unikalności "
                    f"'{spec.label}' ({spec.key_columns_label})."
                )

        # Wymagane indeksy (w tym indeks częściowy uq_training_active_user_day)
        for index in build_required_indexes([table_name]):
            target_index = target_indexes.get(index.name)
            if target_index is None:
                errors.append(
                    f"Tabela '{table_name}': brak wymaganego indeksu '{index.name}'."
                )
                continue
            index_columns, index_is_unique = target_index
            model_columns = tuple(sorted(col.name for col in index.columns))
            if index_columns != model_columns:
                errors.append(
                    f"Tabela '{table_name}': indeks '{index.name}' obejmuje inne kolumny — "
                    f"model wymaga {list(model_columns)}, baza docelowa ma {list(index_columns)}."
                )
            elif index_is_unique != bool(index.unique):
                errors.append(
                    f"Tabela '{table_name}': indeks '{index.name}' ma unique="
                    f"{index_is_unique}, a model wymaga unique={bool(index.unique)}."
                )

    return errors


def inspect_target_sequences(engine: Engine) -> list[str]:
    """Raportuje brakujące sekwencje PostgreSQL dla kolumn integer PK modelu.

    Synchronizowane są wyłącznie sekwencje, które naprawdę istnieją w bazie
    docelowej; brak sekwencji jest zgłaszany jako ostrzeżenie (nie błąd),
    bo wtedy kolumna jest zapewne ręcznie wypełniana.
    """
    warnings: list[str] = []
    for table_name in TABLE_ORDER:
        table = model_table(table_name)
        integer_pk_columns = [
            col
            for col in table.primary_key.columns
            if classify_column_type(col.type) == "int"
        ]
        if not integer_pk_columns:
            continue
        column = integer_pk_columns[0]
        try:
            with engine.connect() as conn:
                sequence_name = conn.execute(
                    sa.text("SELECT pg_get_serial_sequence(:table_name, :column_name)"),
                    {"table_name": table_name, "column_name": column.name},
                ).scalar()
        except Exception as exc:  # brak uprawnień/inny problem — nie blokuje preflightu
            warnings.append(
                f"Tabela '{table_name}': nie udało się sprawdzić sekwencji kolumny "
                f"'{column.name}' ({type(exc).__name__}). Weryfikacja nastąpi podczas importu."
            )
            continue
        if not sequence_name:
            warnings.append(
                f"Tabela '{table_name}': kolumna '{column.name}' nie ma sekwencji PostgreSQL "
                "(pg_get_serial_sequence zwraca NULL). Nowe wiersze wymagają jawnego 'id'."
            )
    return warnings


def sync_target_sequences(conn: Any, converted_data: Mapping[str, Any]) -> list[str]:
    """Synchronizuje istniejące sekwencje PostgreSQL w ramach aktywnej transakcji.

    Dla każdej kolumny typu INTEGER będącej kluczem głównym weryfikujemy, czy w bazie
    docelowej istnieje sekwencja (`pg_get_serial_sequence`). Jeśli istnieje — ustawiamy
    jej wartość na maksymalne zaimportowane `id` (z `is_called = TRUE`, aby kolejny
    insert otrzymał następny numer). Brak sekwencji = pominięcie (bez ukrywania błędu),
    a każdy błąd synchronizacji jest KRYTYCZNY i przerywa transakcję.
    """
    synced: list[str] = []
    for table_name in TABLE_ORDER:
        table = model_table(table_name)
        integer_pk_columns = [
            col
            for col in table.primary_key.columns
            if classify_column_type(col.type) == "int"
        ]
        if not integer_pk_columns:
            continue
        column = integer_pk_columns[0]
        rows = list(converted_data.get(table_name) or [])
        if not rows:
            continue

        missing_ids = [
            idx for idx, row in enumerate(rows, start=1) if row.get(column.name) is None
        ]
        if missing_ids:
            raise MigrationError(
                f"Tabela '{table_name}': brak wartości klucza głównego '{column.name}' "
                f"dla wierszy {missing_ids[:10]} — nie można zweryfikować sekwencji."
            )

        max_id = max(row[column.name] for row in rows)

        sequence_name = conn.execute(
            sa.text("SELECT pg_get_serial_sequence(:table_name, :column_name)"),
            {"table_name": table_name, "column_name": column.name},
        ).scalar()
        if not sequence_name:
            continue  # brak sekwencji = pominięcie, bez cichego ukrywania błędu

        try:
            applied = conn.execute(
                sa.text("SELECT setval(:sequence_name, :last_value, TRUE)"),
                {"sequence_name": str(sequence_name), "last_value": max_id},
            ).scalar()
        except Exception as exc:
            raise SequenceSyncError(
                f"Krytyczny błąd synchronizacji sekwencji '{sequence_name}' dla tabeli "
                f"'{table_name}.{column.name}' (wartość docelowa {max_id}): {exc}"
            ) from exc

        if applied is None or int(applied) != int(max_id):
            raise SequenceSyncError(
                f"Sekwencja '{sequence_name}' nie została ustawiona na {max_id} "
                f"(otrzymano {applied}) dla tabeli '{table_name}.{column.name}'."
            )
        synced.append(f"{table_name}.{column.name} -> {sequence_name} = {max_id}")
    return synced


# ─── Ekstrakcja i konwersja danych źródłowych ─────────────────────────────────


def _column_default(column: sa.Column) -> Any:
    if column.default is None:
        return None
    arg = getattr(column.default, "arg", None)
    if callable(arg):
        return None
    return arg


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
    for req in sorted(REQUIRED_SOURCE_TABLES):
        if req not in src_tables:
            errors.append(f"W źródłowej bazie SQLite brakuje kluczowej tabeli '{req}'.")

    if errors:
        return {}, errors, warnings

    for table_name in TABLE_ORDER:
        data_by_table[table_name] = []
        if table_name not in src_tables:
            warnings.append(
                f"Tabela '{table_name}' nie występuje w pliku SQLite -- 0 rekordów do migracji."
            )
            continue

        target_table = model_table(table_name)
        src_cols = {
            r["name"] for r in cur.execute(f"PRAGMA table_info({table_name})").fetchall()
        }

        # Sprawdź czy kolumny NOT NULL bez domyślnych istnieją w źródle
        for col in target_table.columns:
            if not col.nullable and col.default is None and col.server_default is None:
                if col.name not in src_cols:
                    errors.append(
                        f"Tabela '{table_name}': wymagana kolumna NOT NULL '{col.name}' "
                        "nie istnieje w źródłowej tabeli SQLite."
                    )
            elif col.name not in src_cols:
                warnings.append(
                    f"Tabela '{table_name}': kolumna '{col.name}' nie istnieje w źródle — "
                    "wiersze otrzymają wartość domyślną/NULL."
                )

        rows = cur.execute(f"SELECT * FROM {table_name}").fetchall()
        for idx, row in enumerate(rows, start=1):
            row_label = idx
            row_pk_value = row[target_table.primary_key.columns[0].name] if _pk_value_available(
                row, target_table
            ) else None
            if row_pk_value is not None:
                row_label = str(row_pk_value)

            converted_row: dict[str, Any] = {}
            for col in target_table.columns:
                col_name = col.name
                col_type_kind = classify_column_type(col.type)

                raw_val = row[col_name] if col_name in src_cols else None

                val, err = coerce_value(
                    raw_val,
                    col_type_kind,
                    col_name,
                    col.nullable,
                    _column_default(col),
                )
                if err:
                    errors.append(f"[{table_name} wiersz {row_label}] {err}")
                converted_row[col_name] = val

            data_by_table[table_name].append(converted_row)

    if errors:
        return data_by_table, errors, warnings

    # 2. Walidacja relacyjna i ograniczeń unikalności
    rel_errors = validate_relational_constraints(data_by_table)
    errors.extend(rel_errors)

    return data_by_table, errors, warnings


def _pk_value_available(row: Any, table: sa.Table) -> bool:
    """Sprawdza, czy wiersz źródłowy ma wartości dla wszystkich kolumn klucza głównego."""
    available = getattr(row, "keys", None)
    if callable(available):
        keys = set(row.keys())
        return all(col.name in keys for col in table.primary_key.columns)
    return False


# ─── Walidacja relacyjna wyznaczona z metadanych ──────────────────────────────


def validate_relational_constraints(
    data_by_table: dict[str, list[dict[str, Any]]],
) -> list[str]:
    """Weryfikuje klucze główne, klucze obce, unikalność i indeksy częściowe.

    Lista relacji i ograniczeń nie jest wpisana na twardo — jest wyznaczana
    z metadanych SQLModel, więc obejmuje wszystkie rzeczywiste klucze obce,
    w tym `exercise_results.source_session_id` oraz `user_number_sequence.user_id`.
    """
    errors: list[str] = []

    errors.extend(_validate_primary_keys(data_by_table))
    errors.extend(_validate_foreign_keys(data_by_table))
    errors.extend(_validate_unique_constraints(data_by_table))
    return errors


def _validate_primary_keys(data_by_table: dict[str, list[dict[str, Any]]]) -> list[str]:
    errors: list[str] = []
    for table_name in TABLE_ORDER:
        table = model_table(table_name)
        pk_columns = [col.name for col in table.primary_key.columns]
        if len(pk_columns) != 1:
            continue
        pk_column = pk_columns[0]

        seen: Dict[Any, int] = {}
        for idx, row in enumerate(data_by_table.get(table_name, []), start=1):
            value = row.get(pk_column)
            if value is None:
                errors.append(
                    f"Tabela '{table_name}': rekord z pustym kluczem głównym '{pk_column}' "
                    f"(wiersz źródłowy {idx})."
                )
                continue
            key = value if isinstance(value, (str, int, float, bool)) else str(value)
            if key in seen:
                errors.append(
                    f"Tabela '{table_name}': zduplikowany klucz główny {pk_column}='{value}' "
                    f"(wiersze źródłowe {seen[key]} i {idx})."
                )
                continue
            seen[key] = idx
    return errors


def _validate_foreign_keys(data_by_table: dict[str, list[dict[str, Any]]]) -> list[str]:
    """Weryfikuje brak osieroconych rekordów i puste wartości w opcjonalnych FK."""
    errors: list[str] = []

    # Indeks wartości rodzica dla każdej pary (tabela, kolumna) docelowej FK.
    parent_value_index: Dict[Tuple[str, str], set] = {}
    for table_name, rows in data_by_table.items():
        table = model_table(table_name)
        for column in table.primary_key.columns:
            values = set()
            for row in rows:
                value = row.get(column.name)
                if value is None:
                    continue
                values.add(value if isinstance(value, (str, int, float, bool)) else str(value))
            parent_value_index[(table_name, column.name)] = values

    for table_name in TABLE_ORDER:
        fk_map = build_foreign_key_map([table_name])
        specs = fk_map.get(table_name, [])
        if not specs:
            continue

        table = model_table(table_name)
        rows = data_by_table.get(table_name, [])
        pk_column = table.primary_key.columns[0].name if len(table.primary_key.columns) == 1 else "id"

        for idx, row in enumerate(rows, start=1):
            row_pk = row.get(pk_column)
            for spec in specs:
                column = table.columns[spec.column]
                value = row.get(spec.column)

                if value is None:
                    if not column.nullable:
                        errors.append(
                            f"Tabela '{table_name}' (id={row_pk}): kolumna klucza obcego "
                            f"'{spec.column}' nie może być NULL ({spec.describe()})."
                        )
                    continue

                # Pusty ciąg w opcjonalnym FK jest niejednoznaczny: kontrakt rozróżnia
                # NULL (brak relacji). Automatyczna normalizacja mogłaby ukryć błąd
                # źródła, dlatego preflight kończy się czytelnym błędem.
                if isinstance(value, str) and value.strip() == "":
                    errors.append(
                        f"Tabela '{table_name}' (id={row_pk}): kolumna klucza obcego "
                        f"'{spec.column}' zawiera pusty ciąg zamiast NULL. Kontrakt danych "
                        f"nie uzasadnia automatycznej normalizacji — "
                        f"napraw dane w źródle ({spec.describe()})."
                    )
                    continue

                key = value if isinstance(value, (str, int, float, bool)) else str(value)
                allowed = parent_value_index.get((spec.ref_table, spec.ref_column), set())
                if key not in allowed:
                    errors.append(
                        f"Tabela '{table_name}' (id={row_pk}): osierocony {spec.column}='{value}' "
                        f"nie istnieje w '{spec.ref_table}' ({spec.describe()})."
                    )
    return errors


def _validate_unique_constraints(data_by_table: dict[str, list[dict[str, Any]]]) -> list[str]:
    """Weryfikuje wszystkie wymagane ograniczenia unikalności (w tym częściowe)."""
    errors: list[str] = []

    for spec in build_unique_specs():
        table = model_table(spec.table)
        rows = data_by_table.get(spec.table, [])
        if not rows:
            continue

        pk_column = table.primary_key.columns[0].name if len(table.primary_key.columns) == 1 else "id"
        columns = [table.columns[name] for name in spec.columns]
        row_labels: Dict[int, str] = {}
        seen: Dict[Tuple[Any, ...], Tuple[Any, str]] = {}

        for idx, row in enumerate(rows, start=1):
            row_pk = row.get(pk_column)
            row_labels[idx] = str(row_pk) if row_pk is not None else str(idx)

            if spec.predicate is not None and not row_matches_partial_predicate(
                spec.predicate, row, spec.table, idx, row_labels[idx]
            ):
                continue

            key_values = tuple(row.get(column.name) for column in columns)
            if any(value is None for value in key_values):
                # Standard SQL: wiele wartości NULL nie narusza unikalności.
                continue

            normalized = tuple(
                value if isinstance(value, (str, int, float, bool)) else str(value)
                for value in key_values
            )
            if normalized in seen:
                first_idx, first_label = seen[normalized]
                errors.append(_duplicate_unique_message(spec, columns, key_values, row, first_label, row_labels[idx], first_idx, idx))
                continue
            seen[normalized] = (idx, row_labels[idx])

    return errors


def _duplicate_unique_message(
    spec: UniqueSpec,
    columns: Sequence[sa.Column],
    key_values: Sequence[Any],
    row: Mapping[str, Any],
    first_label: str,
    current_label: str,
    first_idx: int,
    current_idx: int,
) -> str:
    """Buduje komunikat o konflikcie unikalności bez ujawniania danych osobowych."""
    table = model_table(spec.table)
    pk_column = table.primary_key.columns[0].name if len(table.primary_key.columns) == 1 else "id"

    parts: list[str] = []
    for column, value in zip(columns, key_values):
        if is_safe_to_echo(column):
            parts.append(f"{column.name}={value!r}")
        else:
            # Wartości potencjalnie wrażliwe (nickname, email, notatki) nie są logowane.
            parts.append(f"{column.name}=<wartość nieujawniona>")

    key_description = ", ".join(parts) if parts else "-"
    if len(columns) == 1 and parts:
        key_description = parts[0]
    predicate = f" WHERE {spec.predicate}" if spec.predicate else ""

    return (
        f"Tabela '{spec.table}': konflikt {spec.conflict_label}{predicate} — "
        f"zduplikowany {key_description} dla wierszy "
        f"{first_label} i {current_label} (wiersze źródłowe {first_idx} i {current_idx}, "
        f"klucz główny {pk_column})."
    )


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

    # 0. Zgłoś oczekiwany head migracji (informacyjnie; błąd jest blokujący).
    try:
        expected_heads = expected_alembic_heads()
        report.notes.append(
            "Oczekiwany head Alembic z grafu migracji: " + ", ".join(expected_heads)
        )
    except Exception as exc:
        report.errors.append(str(exc))

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
        else:
            report.notes.append(
                "Schemat docelowy zgodny z modelem SQLModel i z headem migracji Alembic."
            )

        # Weryfikacja sekwencji tylko dla rzeczywistych silników (testy używają atrap).
        if isinstance(engine, Engine):
            try:
                _, _, alembic_errors = verify_alembic_version(engine)
                if not alembic_errors:
                    report.notes.append(
                        "Wersja schematu docelowej bazy (alembic_version) zgodna z headem."
                    )
                report.warnings.extend(inspect_target_sequences(engine))
            except Exception as exc:
                report.warnings.append(f"Nie udało się zweryfikować sekwencji docelowej bazy: {exc}")

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

    migrated_counts: dict[str, int] = {}
    try:
        with engine.connect() as conn:
            with conn.begin():  # Otwiera pojedynczą atomową transakcję
                # Ponowna weryfikacja czystości tabel wewnątrz transakcji
                for tbl_name in _INSERT_ORDER:
                    tbl_obj = model_table(tbl_name)
                    cnt = conn.execute(select(func.count()).select_from(tbl_obj)).scalar() or 0
                    if cnt > 0:
                        raise TargetNotEmptyError(
                            f"Tabela docelowa '{tbl_name}' zawiera {cnt} rekordów! "
                            "Przerwano migrację, aby nie nadpisała danych."
                        )

                # Wstawianie rekordów w kolejności zależności wyznaczonej z FK
                for tbl_name in _INSERT_ORDER:
                    rows = converted_data.get(tbl_name, [])
                    tbl_obj = model_table(tbl_name)
                    if rows:
                        conn.execute(tbl_obj.insert(), rows)
                    migrated_counts[tbl_name] = len(rows)

                # Weryfikacja liczby wierszy po imporcie (wewnątrz transakcji przed commitem)
                for tbl_name in _INSERT_ORDER:
                    tbl_obj = model_table(tbl_name)
                    cnt = conn.execute(select(func.count()).select_from(tbl_obj)).scalar() or 0
                    expected = migrated_counts[tbl_name]
                    if cnt != expected:
                        raise MigrationError(
                            f"Błąd weryfikacji tabeli '{tbl_name}': oczekiwano {expected} rekordów, "
                            f"a w bazie znajduje się {cnt}."
                        )

                # Synchronizacja istniejących sekwencji PostgreSQL (błąd = rollback).
                synced = sync_target_sequences(conn, converted_data)
                for entry in synced:
                    result.preflight_report.notes.append(f"Zsynchronizowano sekwencję: {entry}")

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
        description="EVOLVE -- Narzędzie offline migracji danych SQLite -> PostgreSQL (Stage 20U.7C)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Wymagania wstępne:
  1. Schemat w bazie docelowej PostgreSQL musi zostać najpierw zainicjalizowany przez:
       alembic upgrade head
  2. Baza docelowa musi być pusta (brak wcześniejszych rekordów w 12 tabelach).
  3. Wersja schematu bazy docelowej musi odpowiadać rzeczywistememu headowi grafu migracji.
  4. Skrypt domyślnie uruchamia się w bezpiecznym trybie preflight (dry-run).
  5. Dodanie flagi `--apply` realizuje transakcyjny import all-or-nothing.
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
