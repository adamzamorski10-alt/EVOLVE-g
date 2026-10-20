"""Inicjalizacja bazy — SQLite bootstrap zachowany, dialekty nie-SQLite pomijane (Stage 20T.2).

Testy nie wymagają żywej bazy: dla dialektów nie-SQLite sprawdzamy, że
`create_db_and_tables()` nie wywołuje `create_all()`, nie otwiera połączenia
i nie commituje; dla SQLite używamy izolowanej bazy w katalogu tymczasowym.
"""
from __future__ import annotations

import importlib
import os
from unittest.mock import MagicMock

import dotenv
import pytest
from sqlalchemy import text
from sqlmodel import SQLModel

import app.config as app_config
import app.database as app_database
from app.models import UserDB

_ENV_KEYS = ("DATABASE_URL", "ENV")


@pytest.fixture
def reload_database():
    """Przeładowuje app.config/app.database na wskazanym DATABASE_URL.

    Przywraca oryginalne zmienne środowiskowe, dotenv.load_dotenv i treść
    obu modułów, aby nie wpływać na konfigurację innych testów.
    """
    saved_env = {key: os.environ.get(key) for key in _ENV_KEYS}
    real_load_dotenv = dotenv.load_dotenv

    def _reload(database_url):
        os.environ.pop("DATABASE_URL", None)
        os.environ.pop("ENV", None)
        os.environ["DATABASE_URL"] = database_url
        # Izolacja od lokalnego pliku .env — test w pełni kontroluje środowisko.
        dotenv.load_dotenv = lambda: None
        importlib.reload(app_config)
        return importlib.reload(app_database)

    try:
        yield _reload
    finally:
        dotenv.load_dotenv = real_load_dotenv
        for key, value in saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        importlib.reload(app_config)
        importlib.reload(app_database)


def _sqlite_tables(module) -> set[str]:
    with module.engine.connect() as conn:
        return {
            row[0]
            for row in conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            ).fetchall()
        }


def test_sqlite_initialization_creates_schema(reload_database, tmp_path):
    db_file = tmp_path / "evolve_init.db"
    module = reload_database(f"sqlite:///{db_file.as_posix()}")

    assert module.create_db_and_tables() is True

    tables = _sqlite_tables(module)
    assert {"users", "training_sessions", "user_number_sequence"} <= tables


def test_sqlite_initialization_is_idempotent(reload_database, tmp_path):
    db_file = tmp_path / "evolve_init_again.db"
    module = reload_database(f"sqlite:///{db_file.as_posix()}")

    assert module.create_db_and_tables() is True
    first = _sqlite_tables(module)
    assert module.create_db_and_tables() is True
    assert _sqlite_tables(module) == first


def test_sqlite_initialization_syncs_user_number_sequence(reload_database, tmp_path):
    db_file = tmp_path / "evolve_init_seq.db"
    module = reload_database(f"sqlite:///{db_file.as_posix()}")
    module.create_db_and_tables()

    with app_database.Session(module.engine) as session:
        session.add(
            UserDB(
                id="user-seq-1",
                user_key="native:user:7",
                user_number=7,
                name="Sekwencja",
                age=30,
                height=180.0,
                weight=80.0,
                start_weight=80.0,
                target_weight=75.0,
                gender="mężczyzna",
                goal="redukcja",
                frequency="3",
                diet="zbilansowana",
            )
        )
        session.commit()

    with module.engine.connect() as conn:
        assert conn.execute(
            text("SELECT COUNT(*) FROM user_number_sequence")
        ).scalar() == 0

    assert module.create_db_and_tables() is True

    with module.engine.connect() as conn:
        row = conn.execute(
            text("SELECT id, user_id FROM user_number_sequence WHERE user_id = 'user-seq-1'")
        ).first()
    assert row == (7, "user-seq-1")


def _fake_engine(dialect_name: str) -> MagicMock:
    engine = MagicMock()
    engine.dialect.name = dialect_name
    return engine


def _assert_no_database_mutations(fake_engine, create_all_calls):
    assert create_all_calls == []
    fake_engine.connect.assert_not_called()
    fake_engine.begin.assert_not_called()
    fake_engine.execute.assert_not_called()


@pytest.mark.parametrize("dialect_name", ["postgresql", "mysql", "mariadb"])
def test_non_sqlite_dialect_skips_initialization(monkeypatch, dialect_name):
    fake_engine = _fake_engine(dialect_name)
    monkeypatch.setattr(app_database, "engine", fake_engine)
    create_all_calls: list[str] = []
    monkeypatch.setattr(
        SQLModel.metadata,
        "create_all",
        lambda *args, **kwargs: create_all_calls.append("create_all"),
    )

    assert app_database.create_db_and_tables() is False

    _assert_no_database_mutations(fake_engine, create_all_calls)


def test_postgresql_skips_initialization_without_connection(monkeypatch):
    fake_engine = _fake_engine("postgresql")
    monkeypatch.setattr(app_database, "engine", fake_engine)
    create_all_calls: list[str] = []
    monkeypatch.setattr(
        SQLModel.metadata,
        "create_all",
        lambda *args, **kwargs: create_all_calls.append("create_all"),
    )

    before = len(create_all_calls)
    assert app_database.create_db_and_tables() is False
    assert len(create_all_calls) == before

    fake_engine.connect.assert_not_called()
    fake_engine.begin.assert_not_called()
