"""Stage B3: migration tests for evolve33userexperience (strength experience + dumbbell fields).

Weryfikacja odbywa się na izolowanej bazie SQLite — PostgreSQL nie jest
dostępne w tym środowisku. Alembic migracje działają identycznie na obu
dialektach (batch_alter_table / add_column / drop_column), więc testy na
SQLite potwierdzają poprawność logiki upgrade/downgrade oraz idempotentność.
"""
from __future__ import annotations

from sqlalchemy import inspect, text

import alembic.command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlmodel import Session

from app.models import UserDB

_REVISION_HEAD = "evolve33userexperience"
_REVISION_BASE = "38d81e29e253"

_EXPECTED_COLUMNS = {
    "strength_training_experience": ("String", True),
    "dumbbell_type": ("String", True),
    "dumbbell_max_kg_per_dumbbell": ("Float", True),
    "dumbbell_increment_kg": ("Float", True),
}


def _alembic_config(sqlite_url: str) -> Config:
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", sqlite_url)
    return cfg


def _upgrade_head(sqlite_url: str) -> None:
    alembic.command.upgrade(_alembic_config(sqlite_url), "head")


def _downgrade_to(sqlite_url: str, revision: str) -> None:
    alembic.command.downgrade(_alembic_config(sqlite_url), revision)


def _columns(conn) -> dict:
    return {
        row["name"]: row
        for row in inspect(conn).get_columns("users")
    }


def _insert_user(engine) -> str:
    user_id = "user-migration-test"
    with Session(engine) as session:
        session.add(
            UserDB(
                id=user_id,
                user_key="native:user:migration-test",
                email="migration-test@example.com",
                name="Migration Test",
                hashed_password="x",
                is_active=True,
                token_version=1,
                gender="mężczyzna",
            )
        )
        session.commit()
    return user_id


def _user_count(engine) -> int:
    with Session(engine) as session:
        return session.exec(text("SELECT COUNT(*) FROM users")).scalar()


def test_migration_chain_has_single_head() -> None:
    """Alembic łańcuch rewizji ma dokładnie jedną głowę: evolve33userexperience."""
    from alembic.script import ScriptDirectory

    script_dir = ScriptDirectory.from_config(Config("alembic.ini"))
    heads = script_dir.get_heads()
    assert heads == [_REVISION_HEAD], f"Oczekiwano jednej głowy {_REVISION_HEAD!r}, otrzymano: {heads}"


def test_upgrade_adds_all_four_columns_when_missing(tmp_path) -> None:
    """Po upgrade do head wszystkie cztery kolumny istnieją w tabeli users."""
    db_file = tmp_path / "evolve_b3_upgrade.db"
    sqlite_url = f"sqlite:///{db_file.as_posix()}"
    # Stwórz bazę na poziomie bazowym (przed nową migracją) bez kolumn B3.
    alembic.command.upgrade(_alembic_config(sqlite_url), _REVISION_BASE)

    engine = create_engine(sqlite_url)
    with engine.connect() as conn:
        before = _columns(conn)
        for col in _EXPECTED_COLUMNS:
            assert col not in before, f"Kolumna {col!r} nie powinna istnieć przed migracją B3"

    _upgrade_head(sqlite_url)

    engine = create_engine(sqlite_url)
    with engine.connect() as conn:
        after = _columns(conn)
        for col in _EXPECTED_COLUMNS:
            assert col in after, f"Kolumna {col!r} nie została dodana przez migrację B3"


def test_column_types_and_nullable_match_model(tmp_path) -> None:
    """Typy i nullable dodanych kolumn zgadzają się z definicją modelu UserDB."""
    db_file = tmp_path / "evolve_b3_types.db"
    sqlite_url = f"sqlite:///{db_file.as_posix()}"
    alembic.command.upgrade(_alembic_config(sqlite_url), _REVISION_HEAD)

    engine = create_engine(sqlite_url)
    with engine.connect() as conn:
        cols = _columns(conn)

    # strength_training_experience: String, nullable
    assert cols["strength_training_experience"]["nullable"] is True
    assert str(cols["strength_training_experience"]["type"]).upper().startswith("VARCHAR")

    # dumbbell_type: String, nullable
    assert cols["dumbbell_type"]["nullable"] is True
    assert str(cols["dumbbell_type"]["type"]).upper().startswith("VARCHAR")

    # dumbbell_max_kg_per_dumbbell: Float, nullable
    assert cols["dumbbell_max_kg_per_dumbbell"]["nullable"] is True
    assert "FLOAT" in str(cols["dumbbell_max_kg_per_dumbbell"]["type"]).upper()

    # dumbbell_increment_kg: Float, nullable
    assert cols["dumbbell_increment_kg"]["nullable"] is True
    assert "FLOAT" in str(cols["dumbbell_increment_kg"]["type"]).upper()


def test_upgrade_is_idempotent(tmp_path) -> None:
    """Ponowne uruchomienie upgrade nie duplikuje kolumn ani nie powoduje błędu."""
    db_file = tmp_path / "evolve_b3_idempotent.db"
    sqlite_url = f"sqlite:///{db_file.as_posix()}"
    _upgrade_head(sqlite_url)
    _upgrade_head(sqlite_url)  # drugi raz — bez zmian

    engine = create_engine(sqlite_url)
    with engine.connect() as conn:
        cols = _columns(conn)
        for col in _EXPECTED_COLUMNS:
            assert col in cols, f"Kolumna {col!r} zniknęła po powtórnym upgrade"


def test_downgrade_removes_columns(tmp_path) -> None:
    """Downgrade do wersji przed B3 usuwa dodane kolumny."""
    db_file = tmp_path / "evolve_b3_downgrade.db"
    sqlite_url = f"sqlite:///{db_file.as_posix()}"
    _upgrade_head(sqlite_url)

    _downgrade_to(sqlite_url, _REVISION_BASE)

    engine = create_engine(sqlite_url)
    with engine.connect() as conn:
        after = _columns(conn)
        for col in _EXPECTED_COLUMNS:
            assert col not in after, f"Kolumna {col!r} nie została usunięta przez downgrade"


def test_existing_user_data_preserved(tmp_path) -> None:
    """Dane użytkowników są zachowane podczas upgrade i downgrade.

    Użytkownik zostaje wstawiony po upgrade do head (wszystkie kolumny
    istnieją), a następnie baza zostaje zdegradowana do wersji przed B3 i
    ponownie podniesiona — weryfikujemy, że wiersz użytkownika przetrwa.
    """
    db_file = tmp_path / "evolve_b3_data.db"
    sqlite_url = f"sqlite:///{db_file.as_posix()}"
    alembic.command.upgrade(_alembic_config(sqlite_url), _REVISION_HEAD)

    engine = create_engine(sqlite_url)
    _insert_user(engine)
    user_count_before = _user_count(engine)

    _downgrade_to(sqlite_url, _REVISION_BASE)
    _upgrade_head(sqlite_url)

    engine = create_engine(sqlite_url)
    assert _user_count(engine) == user_count_before
