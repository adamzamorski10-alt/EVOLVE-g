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


# ─── S1: Password Change Invalidates Tokens ───────────────────────────────────

def test_s1_change_password_invalidates_old_access_and_refresh_tokens():
    """
    Po POST /auth/change-password:
    - stary access token musi zwracać 401 przy próbie użycia (np. /auth/me)
    - stary refresh token musi zwracać 401 w /auth/refresh-access
    - nowe hasło pozwala się zalogować i uzyskać nowe, działające tokeny.
    """
    raw_email = f"passchange-{uuid.uuid4().hex[:6]}@example.com"
    initial_password = "OldSecurePassword123!"
    new_password = "NewSecurePassword456!"

    # 1. Rejestracja
    reg_res = client.post("/auth/register", json={
        "email": raw_email,
        "password": initial_password,
        "name": "Password Changer",
    })
    assert reg_res.status_code == 200, reg_res.text
    old_access_token = reg_res.json()["access_token"]
    old_refresh_token = reg_res.json()["refresh_token"]

    # 2. Sprawdźmy, że tokeny działają przed zmianą
    me_res = client.get("/auth/me", headers={"Authorization": f"Bearer {old_access_token}"})
    assert me_res.status_code == 200

    ref_res = client.post("/auth/refresh-access", json={"refresh_token": old_refresh_token})
    assert ref_res.status_code == 200

    # 3. Zmiana hasła
    change_res = client.post(
        "/auth/change-password",
        headers={"Authorization": f"Bearer {old_access_token}"},
        json={
            "current_password": initial_password,
            "new_password": new_password,
        },
    )
    assert change_res.status_code == 200, change_res.text

    # 4. WERYFIKACJA UNIEWAŻNIENIA:
    # Stary access token musi natychmiast dać 401
    me_after = client.get("/auth/me", headers={"Authorization": f"Bearer {old_access_token}"})
    assert me_after.status_code == 401, f"Expected 401 for old access token, got {me_after.status_code}"

    # Stary refresh token musi dać 401
    ref_after = client.post("/auth/refresh-access", json={"refresh_token": old_refresh_token})
    assert ref_after.status_code == 401, f"Expected 401 for old refresh token, got {ref_after.status_code}"

    # 5. Logowanie nowym hasłem działa
    login_res = client.post("/auth/login", json={
        "email": raw_email,
        "password": new_password,
    })
    assert login_res.status_code == 200
    new_access = login_res.json()["access_token"]
    me_new = client.get("/auth/me", headers={"Authorization": f"Bearer {new_access}"})
    assert me_new.status_code == 200


# ─── S2: Refresh Token Rotation & Invalidation ────────────────────────────────

def test_s2_refresh_token_rotation_and_logout():
    """
    S2:
    - POST /auth/refresh-access wykonuje rotację refresh tokena (zwraca nowy refresh token)
    - Poprzedni refresh token staje się nieważny (ponowne użycie daje 401)
    - Endpoint wylogowania POST /auth/logout unieważnia refresh token.
    """
    raw_email = f"rotation-{uuid.uuid4().hex[:6]}@example.com"
    password = "RotationPassword123!"

    reg_res = client.post("/auth/register", json={
        "email": raw_email,
        "password": password,
    })
    assert reg_res.status_code == 200
    rt1 = reg_res.json()["refresh_token"]

    # 1. Wymiana rt1 na nowy zestaw (rotacja)
    rot_res = client.post("/auth/refresh-access", json={"refresh_token": rt1})
    assert rot_res.status_code == 200, rot_res.text
    rot_data = rot_res.json()
    assert "access_token" in rot_data
    assert "refresh_token" in rot_data
    rt2 = rot_data["refresh_token"]
    assert rt2 != rt1

    # 2. Ponowna próba użycia rt1 (replay attack) musi zostać odrzucona (401)
    replay_res = client.post("/auth/refresh-access", json={"refresh_token": rt1})
    assert replay_res.status_code == 401, f"Replay of rotated refresh token must fail with 401, got {replay_res.status_code}"

    # 3. Użycie rt2 działa
    rot2_res = client.post("/auth/refresh-access", json={"refresh_token": rt2})
    assert rot2_res.status_code == 200
    rt3 = rot2_res.json()["refresh_token"]

    # 4. Wylogowanie POST /auth/logout unieważnia rt3
    logout_res = client.post("/auth/logout", json={"refresh_token": rt3})
    assert logout_res.status_code == 200

    # Próba odświeżenia po wylogowaniu daje 401
    after_logout_res = client.post("/auth/refresh-access", json={"refresh_token": rt3})
    assert after_logout_res.status_code == 401
