"""
FitAI Configuration — Environment, constants, settings
"""

import os
import secrets
import sys
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()

# ─── Database ─────────────────────────────────────────────────────────────────
_raw_database_url = os.getenv("DATABASE_URL", "").strip()

_env = os.getenv("ENV", "development")
_is_production = _env == "production"

if not _raw_database_url:
    if _is_production:
        print(
            "KRYTYCZNY BŁĄD: DATABASE_URL nie jest ustawiony w produkcji — "
            "konfiguracja bazy danych jest niekompletna.",
            file=sys.stderr,
        )
        sys.exit(1)
    _raw_database_url = "sqlite:///fitai.db"


def _normalize_database_url(raw_url: str) -> str:
    """Ujednolica schemat PostgreSQL dla aplikacji i Alembica.

    Hostingi (Render/Heroku) podają schemat ``postgres://``, którego
    SQLAlchemy 2.x nie rozpoznaje. Normalizacja do ``postgresql+psycopg://``
    gwarantuje ten sam sterownik w obu wejściach: ``app/database.py`` tworzy
    engine, ``alembic/env.py`` wykonuje migracje. URL SQLite oraz jawne
    schematy z konkretnym sterownikiem (``postgresql+psycopg2://``) pozostają
    bez zmian. Operacja jest czysto tekstowa i nie nawiązuje połączenia.
    """
    scheme, separator, remainder = raw_url.partition("://")
    if separator and scheme.lower() in {"postgres", "postgresql"}:
        return f"postgresql+psycopg://{remainder}"
    return raw_url


DATABASE_URL = _normalize_database_url(_raw_database_url)

# Fail-closed: w produkcji zabraniaj użycia SQLite
if _is_production:
    lowered = DATABASE_URL.lower()
    if lowered.startswith("sqlite"):
        print(
            "KRYTYCZNY BŁĄD: DATABASE_URL wskazuje na SQLite w środowisku produkcyjnym.",
            file=sys.stderr,
        )
        sys.exit(1)

# ─── JWT / Auth ────────────────────────────────────────────────────────────────
_jwt_secret = os.getenv("JWT_SECRET_KEY", "")
if not _jwt_secret:
    import sys
    if os.getenv("ENV", "development") == "production":
        print("KRYTYCZNY BŁĄD: JWT_SECRET_KEY nie jest ustawiony w produkcji!", file=sys.stderr)
        sys.exit(1)
    else:
        _jwt_secret = secrets.token_hex(32)
        print("OSTRZEŻENIE: JWT_SECRET_KEY nie ustawiony — używam losowego klucza (tylko dev!).")
JWT_SECRET_KEY: str = _jwt_secret
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MIN", "30"))          # access token: 30 min
JWT_REFRESH_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "60"))  # refresh token: 60 dni

# ─── Rate Limiting ─────────────────────────────────────────────────────────────
AI_RATE_PER_MINUTE: str = os.getenv("AI_RATE_PER_MINUTE", "10/minute")
AI_RATE_PER_HOUR: str = os.getenv("AI_RATE_PER_HOUR", "50/hour")

# ─── AI Services ──────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
AI_PROVIDER = os.getenv("AI_PROVIDER", "groq")  # "groq" lub "gemini"

# ─── Discord ───────────────────────────────────────────────────────────────────
DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")  # pusty = bot nie startuje (dev bez tokena)

# ─── Cron / Scheduler ─────────────────────────────────────────────────────────
_cron_secret = os.getenv("CRON_SECRET", "")
if not _cron_secret:
    import sys as _sys
    if os.getenv("ENV", "development") == "production":
        print("KRYTYCZNY BŁĄD: CRON_SECRET nie jest ustawiony w produkcji!", file=_sys.stderr)
        _sys.exit(1)
    else:
        _cron_secret = secrets.token_hex(16)
        print(f"OSTRZEŻENIE: CRON_SECRET nie ustawiony — używam losowego klucza (tylko dev!): {_cron_secret}")
CRON_SECRET: str = _cron_secret

# ─── Nutrition Constants ──────────────────────────────────────────────────────
# XP system
_XP_CHECKIN = 10
_XP_WEIGHT_LOGGED = 15
_XP_WORKOUT_LOGGED = 50
_XP_MEAL_LOGGED = 5
_XP_RECOVERY_FILLED = 8
_XP_DRILL_ATTEMPT = 25
_XP_DRILL_COMPLETED = 100
_XP_STREAK_BONUS = 10

# ─── CORS ─────────────────────────────────────────────────────────────────────
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# ─── App Info ──────────────────────────────────────────────────────────────────
APP_VERSION = "2.1.0"
APP_NAME = "FitAI"

# ─── Feature Flags ────────────────────────────────────────────────────────────
DEBUG = os.getenv("DEBUG", "false").lower() == "true"