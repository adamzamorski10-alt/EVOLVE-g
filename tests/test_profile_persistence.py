"""
tests/test_profile_persistence.py — Profile persistence integration tests.

Covers reliable PUT/GET round-trip for the seven core profile fields:
  age, gender, height, weight, target_weight, frequency, goal

Uses FastAPI TestClient against the in-memory SQLite database (same engine
as the app), seeding users directly via SQLModel and authenticating with
JWT access tokens — mirroring the pattern in tests/test_today_api.py.
"""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.auth.jwt_utils import create_access_token
from app.database import engine
from app.models import UserDB
from main import app

client = TestClient(app)

SEVEN_FIELDS = {
    "age": 34,
    "gender": "kobieta",
    "height": 168.0,
    "weight": 65.5,
    "target_weight": 60.0,
    "frequency": "4-5 razy w tygodniu",
    "goal": "redukcja tkanki tłuszczowej",
}


def _seed_user(*, profile_fields: dict | None = None) -> tuple[str, str]:
    """Create a UserDB directly in the DB and return (user_id, access_token)."""
    suffix = uuid.uuid4().hex[:10]
    fields = {
        "user_key": f"test-profile:{suffix}",
        "email": f"profile-{suffix}@example.com",
        "nickname": f"profile_{suffix}",
        "name": "Profile Persistence Test",
        "hashed_password": "x",
        "is_active": True,
        "token_version": 1,
        "role": "free_user",
        "plan": "free",
    }
    if profile_fields:
        fields.update(profile_fields)
    user = UserDB(**fields)
    with Session(engine) as session:
        session.add(user)
        session.commit()
        session.refresh(user)
        token = create_access_token(user.id, user.email or "", user.role)
        return str(user.id), token


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── 1. Full seven-field PUT/GET round-trip ──────────────────────────────────

def test_profile_put_get_all_seven_fields_exact_match():
    """PUT all seven fields, then GET /app/profile — every value matches."""
    _, token = _seed_user()

    put_res = client.put("/app/profile", json=SEVEN_FIELDS, headers=_auth_headers(token))
    assert put_res.status_code == 200, f"PUT failed: {put_res.text}"
    put_body = put_res.json()
    assert put_body["status"] == "ok"

    get_res = client.get("/app/profile", headers=_auth_headers(token))
    assert get_res.status_code == 200, f"GET failed: {get_res.text}"
    profile = get_res.json()

    for field, expected in SEVEN_FIELDS.items():
        actual = profile.get(field)
        assert actual == expected, (
            f"Field {field!r}: expected {expected!r}, got {actual!r}"
        )


# ── 2. Partial update preserves other fields ────────────────────────────────

def test_profile_partial_update_preserves_existing_fields():
    """PUT a subset of fields; previously saved fields remain unchanged."""
    _, token = _seed_user(profile_fields=SEVEN_FIELDS)

    # Verify all seven are present after seed + initial state
    get_res = client.get("/app/profile", headers=_auth_headers(token))
    assert get_res.status_code == 200
    before = get_res.json()
    for field, expected in SEVEN_FIELDS.items():
        assert before.get(field) == expected, f"Pre-condition: {field} = {before.get(field)!r}"

    # Now update only two fields
    partial = {"goal": "budowa masy mięśniowej", "frequency": "5-6 razy w tygodniu"}
    put_res = client.put("/app/profile", json=partial, headers=_auth_headers(token))
    assert put_res.status_code == 200, f"Partial PUT failed: {put_res.text}"

    get_res = client.get("/app/profile", headers=_auth_headers(token))
    assert get_res.status_code == 200
    after = get_res.json()

    # Updated fields changed
    assert after["goal"] == "budowa masy mięśniowej"
    assert after["frequency"] == "5-6 razy w tygodniu"

    # Untouched fields preserved exactly
    for field in ("age", "gender", "height", "weight", "target_weight"):
        assert after.get(field) == SEVEN_FIELDS[field], (
            f"Field {field} was overwritten by partial update: {after.get(field)!r}"
        )


# ── 3. target_weight specific test ──────────────────────────────────────────

def test_profile_target_weight_persists_and_roundtrips():
    """target_weight is saved and returned exactly; camelCase->snake_case mapping works."""
    _, token = _seed_user()

    put_res = client.put(
        "/app/profile",
        json={"target_weight": 72.5},
        headers=_auth_headers(token),
    )
    assert put_res.status_code == 200, f"PUT target_weight failed: {put_res.text}"

    get_res = client.get("/app/profile", headers=_auth_headers(token))
    assert get_res.status_code == 200
    profile = get_res.json()
    assert profile.get("target_weight") == 72.5, (
        f"target_weight: expected 72.5, got {profile.get('target_weight')!r}"
    )


# ── 4. Fresh session / re-read persistence ──────────────────────────────────

def test_profile_persists_across_separate_requests():
    """Values survive multiple independent GET requests (fresh DB sessions)."""
    _, token = _seed_user(profile_fields=SEVEN_FIELDS)

    # First read
    r1 = client.get("/app/profile", headers=_auth_headers(token))
    assert r1.status_code == 200

    # Second read — new request, new DB session
    r2 = client.get("/app/profile", headers=_auth_headers(token))
    assert r2.status_code == 200
    profile = r2.json()

    for field, expected in SEVEN_FIELDS.items():
        assert profile.get(field) == expected, (
            f"Field {field} not preserved across requests: {profile.get(field)!r}"
        )
