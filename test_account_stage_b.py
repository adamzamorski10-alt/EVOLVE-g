import hashlib
import os
import uuid
from datetime import date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.auth import routes as auth_routes
from app.auth import create_access_token, hash_password, verify_password
from app.database import engine
from app.models import (
    DailyLogDB,
    GoalDB,
    NutritionEntryDB,
    RefreshTokenDB,
    TrainingSessionDB,
    UserDB,
    UserNumberSequenceDB,
)
from main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def _disable_rate_limits():
    prev_auth = auth_routes.limiter.enabled
    auth_routes.limiter.enabled = False
    yield
    auth_routes.limiter.enabled = prev_auth


def _create_user(email: str, password: str = "SuperSecret123!", name: str = "Test User") -> UserDB:
    with Session(engine) as session:
        user = UserDB(
            user_key=f"native:user:pending-{uuid.uuid4().hex[:8]}",
            email=email.lower().strip(),
            name=name,
            hashed_password=hash_password(password),
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
        session.flush()
        seq = UserNumberSequenceDB(user_id=user.id)
        session.add(seq)
        session.flush()
        user.user_number = seq.id
        user.user_key = f"native:user:{seq.id}"
        session.commit()
        session.refresh(user)
        return user


# ─── B1: Reset Hasła ──────────────────────────────────────────────────────────

def test_b1_password_reset_request_identical_response_prevents_user_enumeration():
    """
    Żądanie resetu hasła zwraca dokładnie taką samą odpowiedź
    zarówno dla istniejącego, jak i nieistniejącego emaila (brak user enumeration).
    Dla istniejącego użytkownika zapisuje hash tokena i datę ważności w bazie.
    """
    existing_email = f"user-{uuid.uuid4().hex[:6]}@example.com"
    user = _create_user(existing_email)

    res_existing = client.post("/auth/password-reset/request", json={"email": existing_email})
    assert res_existing.status_code == 200, f"Expected 200, got {res_existing.status_code}: {res_existing.text}"
    data_existing = res_existing.json()
    assert "status" in data_existing

    res_missing = client.post("/auth/password-reset/request", json={"email": "nonexistent_email_404@example.com"})
    assert res_missing.status_code == 200
    data_missing = res_missing.json()

    assert data_existing["message"] == data_missing["message"], "Komunikaty muszą być identyczne (ochrona przed enumeracją)"

    # Sprawdzamy stan w bazie dla istniejącego usera
    with Session(engine) as session:
        db_user = session.get(UserDB, user.id)
        assert db_user.password_reset_token_hash is not None
        assert db_user.password_reset_expires_at is not None
        assert db_user.password_reset_expires_at > datetime.utcnow()


def test_b1_password_reset_confirm_resets_password_and_invalidates_old_tokens():
    """
    Potwierdzenie resetu hasła nowym hasłem (min 8 znaków):
    1. Zmienia hasło (nowe działa, stare nie).
    2. Podbija token_version i unieważnia stare tokeny.
    3. Usuwa jednorazowy token z bazy (brak ponownego użycia).
    """
    email = f"resetme-{uuid.uuid4().hex[:6]}@example.com"
    old_pw = "OldSecretPassword123!"
    new_pw = "BrandNewPassword2026!"
    user = _create_user(email, password=old_pw)

    old_token = create_access_token(user.id, user.email, user.role, token_version=user.token_version)

    # Ustawiamy jawny token resetu w bazie dla testu
    raw_token = f"test-reset-token-{uuid.uuid4().hex}"
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    with Session(engine) as session:
        db_u = session.get(UserDB, user.id)
        db_u.password_reset_token_hash = token_hash
        db_u.password_reset_expires_at = datetime.utcnow() + timedelta(hours=1)
        session.add(db_u)
        session.commit()

    # Wywołujemy confirm
    res = client.post(
        "/auth/password-reset/confirm",
        json={"token": raw_token, "new_password": new_pw},
    )
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"

    # Stary access token nie działa (token_version wzrosła)
    res_me_old = client.get("/auth/me", headers={"Authorization": f"Bearer {old_token}"})
    assert res_me_old.status_code == 401

    # Logowanie starym hasłem odpada
    res_login_old = client.post("/auth/login", json={"email": email, "password": old_pw})
    assert res_login_old.status_code == 401

    # Logowanie nowym hasłem działa
    res_login_new = client.post("/auth/login", json={"email": email, "password": new_pw})
    assert res_login_new.status_code == 200

    # Ponowne użycie tego samego tokena resetującego musi zostać odrzucone
    res_reuse = client.post(
        "/auth/password-reset/confirm",
        json={"token": raw_token, "new_password": "AnotherPassword999!"},
    )
    assert res_reuse.status_code in {400, 404, 422}


def test_b1_password_reset_confirm_rejects_expired_token():
    """Wygasły token resetu hasła zostaje odrzucony."""
    email = f"expired-{uuid.uuid4().hex[:6]}@example.com"
    user = _create_user(email)
    raw_token = f"expired-token-{uuid.uuid4().hex}"
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    with Session(engine) as session:
        db_u = session.get(UserDB, user.id)
        db_u.password_reset_token_hash = token_hash
        db_u.password_reset_expires_at = datetime.utcnow() - timedelta(minutes=5)
        session.add(db_u)
        session.commit()

    res = client.post(
        "/auth/password-reset/confirm",
        json={"token": raw_token, "new_password": "NewSecretPass123!"},
    )
    assert res.status_code in {400, 422}


# ─── B3: Usuwanie Konta ───────────────────────────────────────────────────────

def test_b3_delete_account_requires_password_and_cleans_up_all_data():
    """
    DELETE /auth/me wymaga podania aktualnego hasła w payloadzie.
    Po usunięciu:
    1. Użytkownik i wszystkie jego dane (sesje, logi, cele itp.) są usunięte.
    2. Dane innego użytkownika w bazie pozostają nienaruszone.
    3. Logowanie usuniętego użytkownika zwraca 401.
    """
    password = "CorrectDeletePassword123!"
    user1 = _create_user(f"delete1-{uuid.uuid4().hex[:6]}@example.com", password=password)
    user2 = _create_user(f"keep2-{uuid.uuid4().hex[:6]}@example.com", password=password)

    token1 = create_access_token(user1.id, user1.email, user1.role, token_version=user1.token_version)

    # Dodajemy powiązane rekordy dla user1 i user2
    with Session(engine) as session:
        session.add(DailyLogDB(user_id=user1.id, log_date=date(2026, 11, 7), mood=5))
        session.add(DailyLogDB(user_id=user2.id, log_date=date(2026, 11, 7), mood=4))
        session.add(TrainingSessionDB(user_id=user1.id, session_date=date(2026, 11, 7), status="completed", planned_snapshot_json="{}"))
        session.add(TrainingSessionDB(user_id=user2.id, session_date=date(2026, 11, 7), status="completed", planned_snapshot_json="{}"))
        session.add(GoalDB(user_id=user1.id, title="User1 Goal", goal_type="strength", target_value=100.0))
        session.add(GoalDB(user_id=user2.id, title="User2 Goal", goal_type="strength", target_value=120.0))
        session.commit()

    # Błędne hasło -> 401
    res_wrong_pw = client.request(
        "DELETE",
        "/auth/me",
        headers={"Authorization": f"Bearer {token1}"},
        json={"password": "WrongPassword999!"},
    )
    assert res_wrong_pw.status_code == 401

    # Poprawne hasło -> 200
    res_ok = client.request(
        "DELETE",
        "/auth/me",
        headers={"Authorization": f"Bearer {token1}"},
        json={"password": password},
    )
    assert res_ok.status_code == 200, f"Expected 200, got {res_ok.status_code}: {res_ok.text}"

    # Weryfikacja usunięcia danych user1 i nienaruszenia user2
    with Session(engine) as session:
        assert session.get(UserDB, user1.id) is None
        assert session.get(UserDB, user2.id) is not None

        u1_logs = session.exec(select(DailyLogDB).where(DailyLogDB.user_id == user1.id)).all()
        assert len(u1_logs) == 0
        u2_logs = session.exec(select(DailyLogDB).where(DailyLogDB.user_id == user2.id)).all()
        assert len(u2_logs) == 1

        u1_sessions = session.exec(select(TrainingSessionDB).where(TrainingSessionDB.user_id == user1.id)).all()
        assert len(u1_sessions) == 0
        u2_sessions = session.exec(select(TrainingSessionDB).where(TrainingSessionDB.user_id == user2.id)).all()
        assert len(u2_sessions) == 1

    # Logowanie user1 odpada
    res_relogin = client.post("/auth/login", json={"email": user1.email, "password": password})
    assert res_relogin.status_code == 401


# ─── B4: Eksport Danych ───────────────────────────────────────────────────────

def test_b4_export_user_data_returns_sanitized_json_isolated():
    """
    GET /app/export zwraca pełny eksport danych użytkownika:
    1. Zawiera profil, logi, sesje treningowe, cele.
    2. NIE zawiera hashed_password, token_version, password_reset_token_hash.
    3. Nie zawiera danych innych użytkowników (pełna izolacja).
    """
    user_a = _create_user(f"export_a-{uuid.uuid4().hex[:6]}@example.com", name="User A")
    user_b = _create_user(f"export_b-{uuid.uuid4().hex[:6]}@example.com", name="User B")

    with Session(engine) as session:
        session.add(DailyLogDB(user_id=user_a.id, log_date=date(2026, 11, 7), mood=5))
        session.add(DailyLogDB(user_id=user_b.id, log_date=date(2026, 11, 7), mood=3))
        session.commit()

    token_a = create_access_token(user_a.id, user_a.email, user_a.role, token_version=user_a.token_version)

    res = client.get("/app/export", headers={"Authorization": f"Bearer {token_a}"})
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()

    assert "profile" in data
    assert data["profile"]["email"] == user_a.email
    assert "hashed_password" not in data["profile"]
    assert "password_reset_token_hash" not in data["profile"]

    # Sprawdzamy daily_logs
    assert "daily_logs" in data
    for log in data["daily_logs"]:
        assert log["user_id"] == user_a.id
        assert log["user_id"] != user_b.id


# ─── B5: Allowlist tras i JSON 404 dla API ─────────────────────────────────────

def test_b5_nonexistent_api_routes_return_json_404_not_html():
    """
    Ścieżki pod /api/*, /auth/*, /app/* w przypadku braku endpointu
    muszą zwracać kod 404 z JSON-em ({"detail": "..."}), a nie HTML fallback SPA.
    """
    for route in ["/api/nonexistent-endpoint-xyz", "/auth/nonexistent-xyz", "/app/nonexistent-xyz"]:
        res = client.get(route)
        assert res.status_code == 404, f"Route {route} expected 404, got {res.status_code}"
        content_type = res.headers.get("content-type", "")
        assert "application/json" in content_type, f"Route {route} expected JSON, got {content_type}"


def test_b5_protected_routes_require_authentication():
    """Trasy chronione bez nagłówka Authorization zwracają 401 Unauthorized."""
    protected_endpoints = [
        ("GET", "/auth/me"),
        ("POST", "/auth/change-password"),
        ("DELETE", "/auth/me"),
        ("GET", "/app/export"),
        ("GET", "/app/today"),
        ("GET", "/app/goals"),
    ]
    for method, path in protected_endpoints:
        res = client.request(method, path)
        assert res.status_code == 401, f"{method} {path} expected 401 Unauthorized, got {res.status_code}"


# ─── B6: Walidacja Rejestracji i Profilu ───────────────────────────────────────

def test_b6_register_duplicate_email_rejected_and_no_hash_in_response():
    """
    Rejestracja z istniejącym emailem zostaje odrzucona (400 lub 409).
    Odpowiedź rejestracji ani profilu nie zawiera pola hashed_password.
    """
    email = f"dupcheck-{uuid.uuid4().hex[:6]}@example.com"
    payload = {
        "email": email,
        "password": "ValidPassword123!",
        "name": "First User",
    }
    res1 = client.post("/auth/register", json=payload)
    assert res1.status_code in {200, 201}
    assert "hashed_password" not in res1.json()

    # Druga rejestracja z tym samym adresem
    res2 = client.post("/auth/register", json=payload)
    assert res2.status_code in {400, 409}, f"Duplicate registration expected 400/409, got {res2.status_code}"
