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

_ENV_KEYS = ("DATABASE_URL", "ENV", "CRON_SECRET", "JWT_SECRET_KEY", "CORS_ORIGINS", "ALLOW_DEMO_LOGIN")


@pytest.fixture
def reloaded_config():
    saved_env = {key: os.environ.get(key) for key in _ENV_KEYS}
    real_load_dotenv = dotenv.load_dotenv

    def _reload(database_url=None, env=None, cors_origins=None):
        for key in _ENV_KEYS:
            os.environ.pop(key, None)
        if database_url is not None:
            os.environ["DATABASE_URL"] = database_url
        if env is not None:
            os.environ["ENV"] = env
        if cors_origins is not None:
            os.environ["CORS_ORIGINS"] = cors_origins
        elif env == "production" or env is None:
            os.environ["CORS_ORIGINS"] = "https://app.example.com"
        effective_env = os.environ.get("ENV") or "production"
        if effective_env == "production":
            os.environ.setdefault("CRON_SECRET", "test-cron-secret")
            os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-32-chars-long")
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
    module = reloaded_config(
        "postgres://user:password@db.internal:5432/fitai",
        env="development",
        cors_origins="*",
    )
    assert module.DATABASE_URL == "postgresql+psycopg://user:password@db.internal:5432/fitai"


def test_postgresql_scheme_is_normalized_to_psycopg_driver(reloaded_config):
    module = reloaded_config(
        "postgresql://user:password@db.internal:5432/fitai",
        env="development",
        cors_origins="*",
    )
    assert module.DATABASE_URL == "postgresql+psycopg://user:password@db.internal:5432/fitai"


def test_normalization_preserves_query_parameters(reloaded_config):
    module = reloaded_config(
        "postgres://user:password@db.internal:5432/fitai?sslmode=require",
        env="development",
        cors_origins="*",
    )
    assert module.DATABASE_URL == (
        "postgresql+psycopg://user:password@db.internal:5432/fitai?sslmode=require"
    )


def test_explicit_postgresql_driver_is_preserved(reloaded_config):
    url = "postgresql+psycopg://user:password@db.internal:5432/fitai"
    module = reloaded_config(url, env="development", cors_origins="*")
    assert module.DATABASE_URL == url

    other = "postgresql+psycopg2://user:password@db.internal:5432/fitai"
    module = reloaded_config(other, env="development", cors_origins="*")
    assert module.DATABASE_URL == other


def test_sqlite_url_is_unchanged(reloaded_config):
    module = reloaded_config("sqlite:///./isolated.db", env="development", cors_origins="*")
    assert module.DATABASE_URL == "sqlite:///./isolated.db"


def test_development_without_database_url_keeps_sqlite_default(reloaded_config):
    module = reloaded_config(env="development", cors_origins="*")
    assert module.DATABASE_URL == "sqlite:///fitai.db"


def test_blank_database_url_in_development_keeps_sqlite_default(reloaded_config):
    module = reloaded_config("   ", env="development", cors_origins="*")
    assert module.DATABASE_URL == "sqlite:///fitai.db"


def test_production_without_database_url_exits(reloaded_config, capsys):
    with pytest.raises(SystemExit) as exit_info:
        reloaded_config(env="production", cors_origins="https://app.example.com")
    assert exit_info.value.code == 1
    assert "DATABASE_URL" in capsys.readouterr().err


def test_production_with_blank_database_url_exits(reloaded_config, capsys):
    with pytest.raises(SystemExit) as exit_info:
        reloaded_config("  ", env="production", cors_origins="https://app.example.com")
    assert exit_info.value.code == 1
    assert "DATABASE_URL" in capsys.readouterr().err


def test_production_error_message_hides_connection_details(reloaded_config, capsys):
    with pytest.raises(SystemExit):
        reloaded_config(env="production", cors_origins="https://app.example.com")
    error_output = capsys.readouterr().err
    assert "://" not in error_output
    assert "fitai.db" not in error_output
    assert "user:password" not in error_output


def test_production_with_sqlite_url_exits(reloaded_config, capsys):
    with pytest.raises(SystemExit) as exit_info:
        reloaded_config("sqlite:///./app.db", env="production", cors_origins="https://app.example.com")
    assert exit_info.value.code == 1
    assert "DATABASE_URL" in capsys.readouterr().err


def test_production_with_whitespace_only_database_url_exits(reloaded_config, capsys):
    with pytest.raises(SystemExit) as exit_info:
        reloaded_config("   \t\n", env="production", cors_origins="https://app.example.com")
    assert exit_info.value.code == 1
    assert "DATABASE_URL" in capsys.readouterr().err


def test_production_with_postgres_url_is_accepted(reloaded_config):
    module = reloaded_config(
        "postgres://user:pass@db:5432/app",
        env="production",
        cors_origins="https://app.example.com",
    )
    assert module.DATABASE_URL.startswith("postgresql+psycopg://")


def test_production_with_postgresql_url_is_accepted(reloaded_config):
    module = reloaded_config(
        "postgresql://user:pass@db:5432/app",
        env="production",
        cors_origins="https://app.example.com",
    )
    assert module.DATABASE_URL.startswith("postgresql+psycopg://")


def test_production_with_explicit_psycopg2_driver_is_accepted(reloaded_config):
    url = "postgresql+psycopg2://user:pass@db:5432/app"
    module = reloaded_config(url, env="production", cors_origins="https://app.example.com")
    assert module.DATABASE_URL == url


def test_development_with_sqlite_url_is_accepted(reloaded_config):
    module = reloaded_config("sqlite:///./dev.db", env="development", cors_origins="*")
    assert module.DATABASE_URL == "sqlite:///./dev.db"


def test_test_env_with_sqlite_url_is_accepted(reloaded_config):
    module = reloaded_config("sqlite:///./test.db", env="test", cors_origins="*")
    assert module.DATABASE_URL == "sqlite:///./test.db"


def test_missing_database_url_in_dev_keeps_default_sqlite(reloaded_config):
    module = reloaded_config(env="development", cors_origins="*")
    assert module.DATABASE_URL == "sqlite:///fitai.db"


def test_missing_env_behaves_as_production_rejects_sqlite_disables_docs_and_demo(reloaded_config, capsys):
    """Gdy ENV nie jest ustawione, aplikacja zachowuje się jak w produkcji:

    - SQLite jest kategorycznie odrzucany (sys.exit(1))
    - get_env() zwraca 'production'
    - docs (/docs) są wyłączone (404)
    - demo token (/auth/demo-token) zwraca 404
    """
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.database import get_session
    from app.auth.routes import router as auth_router

    # 1. Próba startu z SQLite bez zmiennej ENV kończy się sys.exit(1)
    with pytest.raises(SystemExit) as exit_info:
        reloaded_config(
            database_url="sqlite:///./unauthorized.db",
            env=None,
            cors_origins="https://app.example.com",
        )
    assert exit_info.value.code == 1
    captured_err = capsys.readouterr().err
    assert "DATABASE_URL wskazuje na SQLite w środowisku produkcyjnym" in captured_err

    # 2. Start z poprawnym PostgreSQL bez zmiennej ENV — fail-closed weryfikacja
    module = reloaded_config(
        "postgresql+psycopg://user:password@localhost:5432/fitai",
        env=None,
        cors_origins="https://app.example.com",
    )
    assert module.get_env() == "production"
    assert module.is_production() is True
    assert module.is_development() is False

    # 3. Weryfikacja docs i demo endpointu w trybie produkcyjnym
    os.environ["ALLOW_DEMO_LOGIN"] = "true"  # nawet jeśli flaga demo jest True, ENV!=development blokuje
    probe_app = FastAPI(docs_url="/docs" if module.is_development() else None)
    probe_app.include_router(auth_router)
    probe_app.dependency_overrides[get_session] = lambda: None

    client = TestClient(probe_app)
    docs_res = client.get("/docs")
    assert docs_res.status_code == 404

    demo_res = client.get("/auth/demo-token")
    assert demo_res.status_code == 404
    assert demo_res.json()["detail"] == "Endpoint niedostępny"
