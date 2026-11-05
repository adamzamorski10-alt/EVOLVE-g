"""
Tests for Auth & Account Hardening — Stage 0 to Stage 5 Security Hardening
"""
from __future__ import annotations

import os
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.auth import routes as auth_routes
from app.auth.security import hash_password
from app.database import engine
from app.models import UserDB
from main import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def _disable_rate_limits():
    prev_auth = auth_routes.limiter.enabled
    auth_routes.limiter.enabled = False
    yield
    auth_routes.limiter.enabled = prev_auth


def _create_user(email: str, name: str = "Test User") -> UserDB:
    with Session(engine) as session:
        user = UserDB(
            user_key=f"native:user:{uuid.uuid4().hex[:8]}",
            email=email.lower().strip(),
            name=name,
            hashed_password=hash_password("SuperSecret123!"),
            is_active=True,
            age=25,
            height=180.0,
            weight=80.0,
            start_weight=80.0,
            target_weight=80.0,
            gender="mężczyzna",
            goal="performance",
            frequency="3",
            diet="balanced",
            role="free_user",
            plan="free",
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


# ─── K1: Demo Token Vulnerability ─────────────────────────────────────────────

def test_k1_demo_token_disabled_or_safe_in_production(monkeypatch):
    """
    W produkcyjnej konfiguracji (ENV=production lub domyślnie bezpiecznej):
    1. Rejestrujemy lub tworzymy dwóch prawdziwych użytkowników.
    2. GET /auth/demo-token oraz POST /auth/demo-login NIE MOGĄ zwrócić tokena
       żadnego istniejącego użytkownika (powinny zwrócić 404 lub 403).
    """
    monkeypatch.setenv("ENV", "production")
    user1 = _create_user(f"owner-{uuid.uuid4().hex[:6]}@example.com", name="Owner")
    user2 = _create_user(f"athlete-{uuid.uuid4().hex[:6]}@example.com", name="Athlete")

    res_get = client.get("/auth/demo-token")
    assert res_get.status_code in {403, 404}, f"Expected 403/404 in production, got {res_get.status_code}: {res_get.text}"

    res_post = client.post("/auth/demo-login")
    assert res_post.status_code in {403, 404}, f"Expected 403/404 in production, got {res_post.status_code}: {res_post.text}"


def test_k1_demo_token_never_picks_first_existing_user_when_demo_missing():
    """
    Nawet jeśli endpoint byłby wywołany w środowisku dev,
    gdy brak użytkownika demo@evolve.app, NIGDY nie wolno wybrać pierwszego
    istniejącego użytkownika (UserDB.first()) i wydać na niego tokena!
    """
    # Upewniamy się, że w bazie jest prawdziwy user
    owner = _create_user(f"realowner-{uuid.uuid4().hex[:6]}@example.com", name="Real Owner")
    
    # Wywołanie wewnętrznej funkcji ensure_demo_user_session
    with Session(engine) as session:
        # Usuńmy potencjalnego demo usera jeśli istnieje
        demo = session.exec(select(UserDB).where(UserDB.email == "demo@evolve.app")).first()
        if demo:
            session.delete(demo)
            session.commit()

        # Wywołanie ensure_demo_user_session NIE MOŻE zwrócić id ani emaila realnego użytkownika
        result = auth_routes.ensure_demo_user_session(session)
        assert result["user_id"] != str(owner.id)
        assert result.get("email") != owner.email
