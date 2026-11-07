"""Testy bezpieczeństwa — Etap A (A1–A4).

Pełne pokrycie wymagań:
- A1: Ochrona rate limitera przed spoofowaniem X-Forwarded-For, test wygasłych/podrobionych tokenów, poprawność proxy
- A2: Bezpieczne wartości domyślne ENV (brak ENV = domyślnie production)
- A3: Izolacja i blokada endpointów demo w produkcji i w development
"""
from types import SimpleNamespace
import os
import time
import uuid
import jwt
import pytest
from fastapi.testclient import TestClient

from app.auth.dependencies import _rate_limit_key
from app.config import JWT_ALGORITHM, JWT_SECRET_KEY
from main import app

client = TestClient(app)


# ─── A1: Ochrona Rate Limitera ────────────────────────────────────────────────


def test_a1_rate_limit_key_never_trusts_raw_x_forwarded_for():
    """
    Klucz limitu IP pobierany jest z request.client.host (ustawianego przez zaufane proxy
    uvicorn z flagami --proxy-headers --forwarded-allow-ips="*"),
    a nie bezpośrednio ze spreparowanego nagłówka klienta.
    """
    req = SimpleNamespace(
        headers={"X-Forwarded-For": "spoofed-ip-1.2.3.4, 10.0.0.1"},
        client=SimpleNamespace(host="198.51.100.25"),
    )
    key = _rate_limit_key(req)
    assert key == "198.51.100.25", f"Klucz nie może pochodzić z nagłówka klienta: {key}"


def test_a1_invalid_signature_token_falls_back_to_client_ip():
    """
    Token ze złym podpisem nie tworzy odrębnego koszyka limitera — spada na IP klienta.
    """
    fake_token = jwt.encode({"sub": "fake-user-uuid"}, "wrong-secret", algorithm=JWT_ALGORITHM)
    req = SimpleNamespace(
        headers={"Authorization": f"Bearer {fake_token}"},
        client=SimpleNamespace(host="198.51.100.26"),
    )
    assert _rate_limit_key(req) == "198.51.100.26"


def test_a1_expired_token_falls_back_to_client_ip():
    """
    Wygasły token nie tworzy odrębnego koszyka limitera — spada na IP klienta.
    """
    expired_token = jwt.encode(
        {"sub": "expired-user-uuid", "exp": int(time.time()) - 3600},
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )
    req = SimpleNamespace(
        headers={"Authorization": f"Bearer {expired_token}"},
        client=SimpleNamespace(host="198.51.100.27"),
    )
    assert _rate_limit_key(req) == "198.51.100.27"


def test_a1_valid_token_uses_sub_scoped_bucket():
    """
    Poprawny, niewygasły token używa izolowanego koszyka użytkownika: user:{sub}.
    """
    user_id = str(uuid.uuid4())
    valid_token = jwt.encode(
        {"sub": user_id, "exp": int(time.time()) + 3600},
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )
    req = SimpleNamespace(
        headers={"Authorization": f"Bearer {valid_token}"},
        client=SimpleNamespace(host="198.51.100.28"),
    )
    assert _rate_limit_key(req) == f"user:{user_id}"


def test_a1_rotating_x_forwarded_for_cannot_bypass_rate_limit():
    """
    Atakujący rotujący nagłówek X-Forwarded-For z tego samego IP/sesji nie może ominąć limitu.
    Klucz limitera dla wszystkich tych żądań jest identyczny (oparty o host ASGI klienta).
    """
    keys = set()
    for i in range(10):
        req = SimpleNamespace(
            headers={"X-Forwarded-For": f"random-spoofed-ip-{i}.net"},
            client=SimpleNamespace(host="203.0.113.50"),
        )
        keys.add(_rate_limit_key(req))

    # Wszystkie żądania z tego samego hosta klienta muszą dzielić dokładnie ten sam klucz limitera
    assert len(keys) == 1
    assert "203.0.113.50" in keys


def test_a1_rate_limit_key_with_asgi_client_scope():
    """
    Symulacja obiektu Request z rzeczywistego scope ASGI za proxy.
    """
    from starlette.requests import Request

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/auth/login",
        "headers": [(b"x-forwarded-for", b"spoofed.client.ip")],
        "client": ("192.0.2.99", 54321),
    }
    request = Request(scope)
    assert _rate_limit_key(request) == "192.0.2.99"


# ─── A2: Bezpieczne wartości domyślne ENV (fail-closed) ───────────────────────


def test_a2_env_defaults_to_production_when_unset(monkeypatch):
    """
    A2: Gdy zmienna ENV nie jest ustawiona, aplikacja traktuje środowisko jako produkcję
    (brak docs, brak demo, bezpieczne reguły).
    """
    from app.config import get_env, is_development, is_production

    monkeypatch.delenv("ENV", raising=False)
    
    # 1. Reguła fail-closed: get_env() zwraca 'production'
    assert get_env() == "production"
    assert is_production() is True
    assert is_development() is False

    # 2. Bez ENV endpointy demo zwracają 404
    monkeypatch.setenv("ALLOW_DEMO_LOGIN", "true")  # nawet przy fladze demo brak ENV=development musi blokować
    res_get = client.get("/auth/demo-token")
    assert res_get.status_code == 404, f"Oczekiwano 404 bez ENV=development, otrzymano {res_get.status_code}"
    res_post = client.post("/auth/demo-login")
    assert res_post.status_code == 404


# ─── A3: Bezpieczeństwo Endpointów Demo ───────────────────────────────────────


def test_a3_demo_token_returns_404_in_production(monkeypatch):
    """
    A3: Endpointy /auth/demo-token i /auth/demo-login w konfiguracji produkcyjnej
    zwracają kod 404 Not Found.
    """
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("ALLOW_DEMO_LOGIN", "false")

    res_get = client.get("/auth/demo-token")
    assert res_get.status_code == 404, f"Oczekiwano 404 dla demo w produkcji, otrzymano {res_get.status_code}"

    res_post = client.post("/auth/demo-login")
    assert res_post.status_code == 404, f"Oczekiwano 404 dla demo w produkcji, otrzymano {res_post.status_code}"


def test_a3_demo_token_never_impersonates_existing_user(monkeypatch):
    """
    A3: Nawet w development endpoint demo nigdy nie kradnie tożsamości innego, istniejącego konta.
    Jeśli użytkownik demo@evolve.app nie istnieje, tworzone jest wyłącznie dedykowane konto demo.
    """
    monkeypatch.setenv("ENV", "development")
    monkeypatch.setenv("ALLOW_DEMO_LOGIN", "true")

    # Załóż zwykłego użytkownika
    real_email = f"realuser-{uuid.uuid4().hex[:6]}@example.com"
    reg = client.post("/auth/register", json={"email": real_email, "password": "Password123!"})
    assert reg.status_code == 200, reg.text
    real_uid = reg.json()["user_id"]

    # Wywołaj demo-token
    demo_res = client.get("/auth/demo-token")
    assert demo_res.status_code == 200, demo_res.text
    demo_data = demo_res.json()

    # Sprawdź, że demo NIE zwróciło tokena/id prawdziwego użytkownika
    assert demo_data["user_id"] != real_uid
    assert demo_data["display_name"] == "Zawodnik EVOLVE"
