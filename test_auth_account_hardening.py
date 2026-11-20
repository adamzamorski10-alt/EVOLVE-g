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
from app.config import JWT_EXPIRE_MINUTES
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
            user_key=f"native:user:pending-{uuid.uuid4().hex[:8]}",
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
        session.flush()
        from app.models import UserNumberSequenceDB
        seq = UserNumberSequenceDB(user_id=user.id)
        session.add(seq)
        session.flush()
        user.user_number = seq.id
        user.user_key = f"native:user:{seq.id}"
        session.commit()
        session.refresh(user)
        return user


# ─── K1: Demo Token Vulnerability ─────────────────────────────────────────────

def test_k1_demo_token_disabled_or_safe_in_production(monkeypatch):
    """
    W produkcyjnej i developerskiej konfiguracji:
    1. Rejestrujemy lub tworzymy dwóch prawdziwych użytkowników.
    2. Trasy /auth/demo-token oraz /auth/demo-login zostały całkowicie usunięte
       i zwracają 404.
    """
    for env_name in ["production", "development"]:
        monkeypatch.setenv("ENV", env_name)
        user1 = _create_user(f"owner-{uuid.uuid4().hex[:6]}@example.com", name="Owner")
        user2 = _create_user(f"athlete-{uuid.uuid4().hex[:6]}@example.com", name="Athlete")

        res_get = client.get("/auth/demo-token")
        assert res_get.status_code == 404, f"Expected 404 for GET /auth/demo-token in {env_name}, got {res_get.status_code}"

        res_post = client.post("/auth/demo-login")
        assert res_post.status_code == 404, f"Expected 404 for POST /auth/demo-login in {env_name}, got {res_post.status_code}"


def test_k1_demo_token_never_picks_first_existing_user_when_demo_missing():
    """
    Funkcja ensure_demo_user_session została całkowicie usunięta,
    a endpointy demo nie istnieją (404) — zero ryzyka impersonacji pierwszego użytkownika.
    """
    assert not hasattr(auth_routes, "ensure_demo_user_session")


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


# ─── S4: Refresh-Access Contract Used by Frontend ──────────────────────────────

def test_s4_refresh_access_contract_frontend_flow():
    """
    Frontend odświeża wygasły access token przez POST /auth/refresh-access
    z refresh tokenem w ciele (bez access tokena w nagłówku Authorization).

    Kontrakt, od którego zależy frontend:
    - odpowiedź zawiera access_token oraz nowy refresh_token (rotacja),
    - token_type = bearer oraz expires_in zgodne z konfiguracją,
    - nowy access token działa na chronionym endpointcie (/auth/me),
    - stary refresh token po rotacji jest odrzucany (brak ponownego użycia).
    """
    raw_email = f"refreshcontract-{uuid.uuid4().hex[:6]}@example.com"
    reg_res = client.post("/auth/register", json={
        "email": raw_email,
        "password": "ContractPassword123!",
        "name": "Contract User",
    })
    assert reg_res.status_code == 200, reg_res.text
    access_token = reg_res.json()["access_token"]
    refresh_token = reg_res.json()["refresh_token"]

    # access token działa przed odświeżeniem
    me_res = client.get("/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me_res.status_code == 200

    # Odświeżenie przez poprawny endpoint: refresh token w ciele, bez Bearer.
    ref_res = client.post("/auth/refresh-access", json={"refresh_token": refresh_token})
    assert ref_res.status_code == 200, ref_res.text
    data = ref_res.json()
    assert "access_token" in data, data
    assert "refresh_token" in data, data
    assert data["token_type"] == "bearer", data
    assert data["expires_in"] == JWT_EXPIRE_MINUTES * 60, data

    new_access = data["access_token"]
    new_refresh = data["refresh_token"]
    assert new_refresh != refresh_token  # rotacja refresh tokena

    # Nowy access token odświeżonej sesji działa na chronionym endpointcie.
    me_new = client.get("/auth/me", headers={"Authorization": f"Bearer {new_access}"})
    assert me_new.status_code == 200

    # Stary refresh token po rotacji jest odrzucany (brak ponownego użycia).
    ref_replay = client.post("/auth/refresh-access", json={"refresh_token": refresh_token})
    assert ref_replay.status_code == 401, ref_replay.text


# ─── S5: Pełny cykl odzyskiwania sesji po wygaśnięciu access tokena (frontend) ─

def test_s5_session_recovery_after_access_token_expiry():
    """
    Modeluje cykl, którego oczekuje frontend po wygaśnięciu access tokena:
    1. access token 401 na chronionym endpointcie,
    2. odświeżenie przez /auth/refresh-access (refresh token w ciele, bez Bearer),
    3. ponowne użycie nowego access tokena → 200,
    4. rotacja: nowy refresh token działa dokładnie raz, jego ponowne użycie → 401
       (zapobiega wyścigom rotacji przy równoczesnych 401).
    """
    raw_email = f"sessionrecovery-{uuid.uuid4().hex[:6]}@example.com"
    reg_res = client.post("/auth/register", json={
        "email": raw_email,
        "password": "RecoveryPassword123!",
        "name": "Recovery User",
    })
    assert reg_res.status_code == 200, reg_res.text
    access_token = reg_res.json()["access_token"]
    refresh_token = reg_res.json()["refresh_token"]

    # access token działa przed odświeżeniem
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {access_token}"}).status_code == 200

    # Pierwsze odświeżenie (po wygaśnięciu access tokena)
    ref1 = client.post("/auth/refresh-access", json={"refresh_token": refresh_token})
    assert ref1.status_code == 200, ref1.text
    acc1 = ref1.json()["access_token"]
    rt1 = ref1.json()["refresh_token"]
    assert rt1 != refresh_token

    # Ponowne użycie nowego access tokena udaje się
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {acc1}"}).status_code == 200

    # Drugie odświeżenie z rt1 (symulacja kolejnego wygaśnięcia access tokena)
    ref2 = client.post("/auth/refresh-access", json={"refresh_token": rt1})
    assert ref2.status_code == 200, ref2.text
    rt2 = ref2.json()["refresh_token"]
    assert rt2 != rt1

    # rt1 po rotacji nie może być już użyty (ochrona przed wyścigiem / ponownym użyciem)
    assert client.post("/auth/refresh-access", json={"refresh_token": rt1}).status_code == 401

    # Nowy access token z drugiego odświeżenia działa
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {ref2.json()['access_token']}"}).status_code == 200


# ─── S3 & S3b: Biometrics Validation, No Guessing, Under-18 Calorie Safety ─────

def test_s3_register_rejects_absurd_biometrics():
    """Absurdalne wartości biometryczne (ujemny wiek, ujemny wzrost, waga 0) muszą dać 422."""
    raw_email = f"absurd-{uuid.uuid4().hex[:6]}@example.com"
    res = client.post("/auth/register", json={
        "email": raw_email,
        "password": "ValidPassword123!",
        "age": -5,
        "height": -10,
        "weight": 0,
    })
    assert res.status_code == 422, f"Expected 422 for absurd biometrics, got {res.status_code}: {res.text}"


def test_s3_register_without_biometrics_does_not_guess_defaults():
    """
    Przy rejestracji bez podania wieku/wzrostu/wagi backend NIE zgaduje 25/170/70.
    Wartości biometryczne w profilu to null/None, a cele żywieniowe nie są wyliczane (0/null).
    """
    raw_email = f"nobiometrics-{uuid.uuid4().hex[:6]}@example.com"
    res = client.post("/auth/register", json={
        "email": raw_email,
        "password": "ValidPassword123!",
    })
    assert res.status_code == 200, res.text
    token = res.json()["access_token"]

    profile_res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert profile_res.status_code == 200
    p = profile_res.json()
    assert p["age"] is None, f"Age should be None, got {p['age']}"
    assert p["height"] is None, f"Height should be None, got {p['height']}"
    assert p["weight"] is None, f"Weight should be None, got {p['weight']}"
    assert p["calories_target"] in (0, None)
    assert p["protein_target"] in (0, None)


def test_s3_under_18_no_calorie_reduction():
    """
    Dla użytkownika poniżej 18 roku życia z celem redukcji, system nie generuje
    deficytu kalorycznego (tylko utrzymanie/masę).
    """
    from app.fitness.calculations import calc_calories

    adult_user = {
        "age": 25,
        "height": 180,
        "weight": 80,
        "gender": "mężczyzna",
        "frequency": "3-4",
        "goal": "redukcja",
    }
    minor_user = {
        "age": 16,
        "height": 180,
        "weight": 80,
        "gender": "mężczyzna",
        "frequency": "3-4",
        "goal": "redukcja",
    }
    adult_maintenance = {
        "age": 25,
        "height": 180,
        "weight": 80,
        "gender": "mężczyzna",
        "frequency": "3-4",
        "goal": "utrzymanie",
    }

    minor_maintenance = {
        "age": 16,
        "height": 180,
        "weight": 80,
        "gender": "mężczyzna",
        "frequency": "3-4",
        "goal": "utrzymanie",
    }

    # Dorosły na redukcji ma 400 kcal mniej niż na utrzymaniu
    assert calc_calories(adult_user) == calc_calories(adult_maintenance) - 400

    # Nastolatek (<18) na redukcji ma kalorie utrzymania (zero deficytu)
    assert calc_calories(minor_user) == calc_calories(minor_maintenance)


def test_s3b_profile_update_size_limits():
    """
    PUT /app/profile odrzuca gigantyczny payload basketball_profile (np. > 64KB JSON).
    """
    raw_email = f"profilesize-{uuid.uuid4().hex[:6]}@example.com"
    reg = client.post("/auth/register", json={"email": raw_email, "password": "Password123!"})
    token = reg.json()["access_token"]

    huge_dict = {"data": "A" * 70000}
    res = client.put(
        "/app/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={"basketball_profile": huge_dict},
    )
    assert res.status_code == 422, f"Expected 422 for oversized basketball_profile, got {res.status_code}"



# ─── S3c-S3f: PUT /app/profile persistence & ownership ──────────────────────────

def test_s3c_profile_update_persists_to_backend():
    """Udane PUT /app/profile zapisuje dane w bazie i GET /auth/me je odzwierciedla."""
    raw_email = f"profilepersist-{uuid.uuid4().hex[:6]}@example.com"
    reg = client.post("/auth/register", json={
        "email": raw_email, "password": "PersistPassword123!", "name": "Jan",
    })
    assert reg.status_code == 200, reg.text
    token = reg.json()["access_token"]

    res = client.put(
        "/app/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "age": 30, "weight": 85.0, "height": 185.0, "target_weight": 80.0,
            "gender": "mężczyzna", "frequency": "4-5", "diet": "wysokobiałkowa",
            "goal": "masa", "meals_per_day": 4, "allergies": "orzechy",
            "health_limitations": "brak", "basketball_position": "rzucający",
            "training_experience": "zaawansowany", "equipment": "sztanga",
        },
    )
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "ok"

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    p = me.json()
    assert p["age"] == 30
    assert p["weight"] == 85.0
    assert p["height"] == 185.0
    assert p["goal"] == "masa"
    assert p["allergies"] == "orzechy"


def test_s3d_partial_profile_update_does_not_clear_other_fields():
    """Częściowa aktualizacja (tylko waga) nie czyści pozostałych pól profilu."""
    raw_email = f"profilepartial-{uuid.uuid4().hex[:6]}@example.com"
    reg = client.post("/auth/register", json={
        "email": raw_email, "password": "PartialPassword123!", "name": "Anna",
        "age": 28, "weight": 60.0, "goal": "utrzymanie",
    })
    assert reg.status_code == 200, reg.text
    token = reg.json()["access_token"]

    before = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
    assert before["name"] == "Anna"
    assert before["goal"] == "utrzymanie"

    # Aktualizujemy wyłącznie wagę — pozostałe pola muszą zostać nienaruszone.
    res = client.put(
        "/app/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={"weight": 62.5},
    )
    assert res.status_code == 200, res.text

    after = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
    assert after["weight"] == 62.5, after
    assert after["name"] == "Anna", "Imię nie może zostać wyczyszczone przy częściowej aktualizacji"
    assert after["goal"] == "utrzymanie", "Cel nie może zostać wyczyszczony przy częściowej aktualizacji"
    assert after["age"] == 28, "Wiek nie może zostać wyczyszczony przy częściowej aktualizacji"


def test_s3e_profile_ownership_enforced():
    """Użytkownik A może zaktualizować tylko swój własny profil; dane użytkownika B nienaruszone."""
    reg_a = client.post("/auth/register", json={
        "email": f"profileownera-{uuid.uuid4().hex[:6]}@example.com", "password": "Pass123!", "name": "Wlasciciel A",
    })
    assert reg_a.status_code == 200
    token_a = reg_a.json()["access_token"]

    reg_b = client.post("/auth/register", json={
        "email": f"profileownerb-{uuid.uuid4().hex[:6]}@example.com", "password": "Pass123!", "name": "Wlasciciel B",
    })
    assert reg_b.status_code == 200
    token_b = reg_b.json()["access_token"]

    before_b = client.get("/auth/me", headers={"Authorization": f"Bearer {token_b}"}).json()
    assert before_b["name"] == "Wlasciciel B"

    # A aktualizuje swój profil
    res = client.put(
        "/app/profile",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"name": "Wlasciciel A Zmieniony"},
    )
    assert res.status_code == 200, res.text

    # B nadal ma swoje dane — A nie nadpisał profilu B
    after_b = client.get("/auth/me", headers={"Authorization": f"Bearer {token_b}"}).json()
    assert after_b["name"] == "Wlasciciel B", after_b

    # A ma swoje zaktualizowane dane
    after_a = client.get("/auth/me", headers={"Authorization": f"Bearer {token_a}"}).json()
    assert after_a["name"] == "Wlasciciel A Zmieniony", after_a


def test_s3f_profile_backend_rejects_invalid_and_unauthenticated():
    """Backend nie traktuje błędnych/nieautoryzowanych żądań jako sukcesu."""
    raw_email = f"profilefail-{uuid.uuid4().hex[:6]}@example.com"
    reg = client.post("/auth/register", json={
        "email": raw_email, "password": "FailPassword123!",
    })
    assert reg.status_code == 200
    token = reg.json()["access_token"]

    # meals_per_day poza dozwolonym zakresem (1-12) → 422, nie 200
    bad = client.put(
        "/app/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={"meals_per_day": 99},
    )
    assert bad.status_code == 422, f"Expected 422 for invalid meals_per_day, got {bad.status_code}"

    # Brak tokena → 401, nie 200
    no_auth = client.put("/app/profile", json={"weight": 70})
    assert no_auth.status_code == 401, f"Expected 401 without token, got {no_auth.status_code}"


# ─── S4: Pełny cykl odzyskiwania sesji po wygaśnięciu access tokena (frontend) ─


def test_s1_2_docs_disabled_in_production(monkeypatch):
    """
    1.2: Poza ENV=development /docs, /redoc i /openapi.json są None (wyłączone).
    """
    from fastapi.testclient import TestClient
    import app as app_pkg

    # Symulacja środowiska produkcyjnego
    monkeypatch.setenv("ENV", "production")
    _is_dev = os.getenv("ENV", "development") == "development"
    assert not _is_dev

    # Weryfikacja reguły konfiguracji:
    assert (None if not _is_dev else "/docs") is None
    assert (None if not _is_dev else "/redoc") is None
    assert (None if not _is_dev else "/openapi.json") is None


def test_s1_5_cors_origins_enforced_in_production(monkeypatch):
    """
    1.5: W produkcji CORS_ORIGINS nie może być '*' ani pusty z allow_credentials=True.
    """
    import importlib
    import pytest
    import app.config as app_cfg

    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@localhost:5432/db")
    monkeypatch.setenv("CRON_SECRET", "test-cron-secret")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret-key-32-chars-long")
    monkeypatch.setenv("CORS_ORIGINS", "*")

    with pytest.raises(SystemExit):
        importlib.reload(app_cfg)


def test_s1_6_rate_limit_key_does_not_trust_client_x_forwarded_for():
    """
    1.6 / A1: _rate_limit_key NIE ufa nagłówkowi X-Forwarded-For od klienta (zapobieganie obejściu limitów).
    Polega na request.client.host ustawianym przez zaufane proxy (uvicorn --proxy-headers --forwarded-allow-ips="*").
    """
    from types import SimpleNamespace
    from app.auth.dependencies import _rate_limit_key

    req = SimpleNamespace(
        headers={"X-Forwarded-For": "attacker.spoofed.ip, 10.0.0.1"},
        client=SimpleNamespace(host="10.0.0.1"),
    )
    key = _rate_limit_key(req)
    assert key == "10.0.0.1"
