"""DATABASE_URL configuration — PostgreSQL normalization and fail-closed (Stage 20S).

app.config is a module-level singleton shared przez całą aplikację i Alembica,
dlatego każdy test przeładowuje go w kontrolowanym środowisku i przywraca
pierwotny stan (zmienne środowiskowe, load_dotenv, treść modułu), aby nie
wpływać na konfigurację i bazę używaną przez inne testy.
"""
from __future__ import annotations

import importlib
import os

import dotenv
import pytest

import app.config as app_config

_ENV_KEYS = ("DATABASE_URL", "ENV", "JWT_SECRET_KEY", "CRON_SECRET")


@pytest.fixture
def reloaded_config():
    saved_env = {key: os.environ.get(key) for key in _ENV_KEYS}
    real_load_dotenv = dotenv.load_dotenv

    def _reload(database_url=None, env=None):
        for key in _ENV_KEYS:
            os.environ.pop(key, None)
        if database_url is not None:
            os.environ["DATABASE_URL"] = database_url
        if env is not None:
            os.environ["ENV"] = env
        # app.config wymaga tych sekretów przy ENV=production; używaj wyłącznie
        # syntetycznych wartości testowych i przywracaj oryginały w teardown.
        if env == "production":
            os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-for-db-tests"
            os.environ["CRON_SECRET"] = "test-cron-secret-for-db-tests"
        # Izolacja od lokalnego pliku .env — testy w pełni kontrolują środowisko.
        # Patch na module dotenv, bo przywiazanie `from dotenv import load_dotenv`
        # w app.config odświeża się podczas importlib.reload.
        dotenv.load_dotenv = lambda: None
        return importlib.reload(app_config)

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


def test_postgres_scheme_is_normalized_to_psycopg_driver(reloaded_config):
    module = reloaded_config("postgres://user:password@db.internal:5432/fitai")
    assert module.DATABASE_URL == "postgresql+psycopg://user:password@db.internal:5432/fitai"


def test_postgresql_scheme_is_normalized_to_psycopg_driver(reloaded_config):
    module = reloaded_config("postgresql://user:password@db.internal:5432/fitai")
    assert module.DATABASE_URL == "postgresql+psycopg://user:password@db.internal:5432/fitai"


def test_normalization_preserves_query_parameters(reloaded_config):
    module = reloaded_config("postgres://user:password@db.internal:5432/fitai?sslmode=require")
    assert module.DATABASE_URL == (
        "postgresql+psycopg://user:password@db.internal:5432/fitai?sslmode=require"
    )


def test_explicit_postgresql_driver_is_preserved(reloaded_config):
    url = "postgresql+psycopg://user:password@db.internal:5432/fitai"
    module = reloaded_config(url)
    assert module.DATABASE_URL == url

    other = "postgresql+psycopg2://user:password@db.internal:5432/fitai"
    module = reloaded_config(other)
    assert module.DATABASE_URL == other


def test_sqlite_url_is_unchanged(reloaded_config):
    module = reloaded_config("sqlite:///./isolated.db")
    assert module.DATABASE_URL == "sqlite:///./isolated.db"


def test_development_without_database_url_keeps_sqlite_default(reloaded_config):
    module = reloaded_config(env="development")
    assert module.DATABASE_URL == "sqlite:///fitai.db"


def test_blank_database_url_in_development_keeps_sqlite_default(reloaded_config):
    module = reloaded_config("   ", env="development")
    assert module.DATABASE_URL == "sqlite:///fitai.db"


def test_production_without_database_url_exits(reloaded_config, capsys):
    with pytest.raises(SystemExit) as exit_info:
        reloaded_config(env="production")
    assert exit_info.value.code == 1
    assert "DATABASE_URL" in capsys.readouterr().err


def test_production_with_blank_database_url_exits(reloaded_config, capsys):
    with pytest.raises(SystemExit) as exit_info:
        reloaded_config("  ", env="production")
    assert exit_info.value.code == 1
    assert "DATABASE_URL" in capsys.readouterr().err


def test_production_error_message_hides_connection_details(reloaded_config, capsys):
    with pytest.raises(SystemExit):
        reloaded_config(env="production")
    error_output = capsys.readouterr().err
    assert "://" not in error_output
    assert "fitai.db" not in error_output
    assert "user:password" not in error_output

def test_production_with_sqlite_url_exits(reloaded_config, capsys):
    with pytest.raises(SystemExit) as exit_info:
        reloaded_config('sqlite:///./app.db', env='production')
    assert exit_info.value.code == 1
    assert 'DATABASE_URL' in capsys.readouterr().err


def test_production_with_whitespace_only_database_url_exits(reloaded_config, capsys):
    with pytest.raises(SystemExit) as exit_info:
        reloaded_config('   \t\n', env='production')
    assert exit_info.value.code == 1
    assert 'DATABASE_URL' in capsys.readouterr().err


def test_production_with_postgres_url_is_accepted(reloaded_config):
    module = reloaded_config('postgres://user:pass@db:5432/app', env='production')
    assert module.DATABASE_URL.startswith('postgresql+psycopg://')


def test_production_with_postgresql_url_is_accepted(reloaded_config):
    module = reloaded_config('postgresql://user:pass@db:5432/app', env='production')
    assert module.DATABASE_URL.startswith('postgresql+psycopg://')


def test_production_with_explicit_psycopg2_driver_is_accepted(reloaded_config):
    url = 'postgresql+psycopg2://user:pass@db:5432/app'
    module = reloaded_config(url, env='production')
    assert module.DATABASE_URL == url


def test_development_with_sqlite_url_is_accepted(reloaded_config):
    module = reloaded_config('sqlite:///./dev.db', env='development')
    assert module.DATABASE_URL == 'sqlite:///./dev.db'


def test_test_env_with_sqlite_url_is_accepted(reloaded_config):
    module = reloaded_config('sqlite:///./test.db', env='test')
    assert module.DATABASE_URL == 'sqlite:///./test.db'


def test_missing_database_url_in_dev_keeps_default_sqlite(reloaded_config):
    module = reloaded_config(env='development')
    assert module.DATABASE_URL == 'sqlite:///fitai.db'
