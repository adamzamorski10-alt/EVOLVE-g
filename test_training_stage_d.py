"""
test_training_stage_d.py — testy etapów D3, D4, D5, D7, D8 (ścieżka treningu siłowego)

D3: today endpoint używa Warsaw timezone
D4: idempotencja serii — ta sama (exercise_key, set_number) → upsert, nie duplikat
D4: konflikt z dwóch urządzeń → ostatni zapis wygrywa, reszta nienaruszona
D5: jedna aktywna sesja treningowa per użytkownik
D7: historia i postępy endpointy → 200
D8: zakończenie sesji + progresja deterministyczna
"""
import json
import uuid
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.auth import routes as auth_routes
from app.auth import create_access_token, hash_password
from app.database import engine
from app.models import (
    TrainingSessionDB,
    TrainingSetResultDB,
    UserDB,
    UserNumberSequenceDB,
)
from main import app

client = TestClient(app)


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _disable_rate_limits():
    prev = auth_routes.limiter.enabled
    auth_routes.limiter.enabled = False
    yield
    auth_routes.limiter.enabled = prev


def _create_user(email: str, password: str = "SuperSecret123!") -> UserDB:
    with Session(engine) as session:
        user = UserDB(
            user_key=f"native:user:pending-{uuid.uuid4().hex[:8]}",
            email=email.lower().strip(),
            name="Test D",
            hashed_password=hash_password(password),
            is_active=True,
            age=25, height=180.0, weight=80.0,
            start_weight=80.0, target_weight=80.0,
            gender="mężczyzna", goal="performance",
            frequency="3", diet="balanced",
            role="free_user", plan="free",
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


def _auth_headers(user: UserDB) -> dict:
    # Use actual token_version from DB (default=1 in UserDB model)
    token = create_access_token(
        user.id, user.email,
        user.role or "free_user",
        token_version=user.token_version,
    )
    return {"Authorization": f"Bearer {token}"}


_PLAN_SNAPSHOT = {
    "exercises": [
        {"exercise_key": "squat", "exercise_name": "Przysiad", "sets": 3, "reps": 5, "weight_kg": 80},
        {"exercise_key": "bench", "exercise_name": "Wyciskanie", "sets": 3, "reps": 8, "weight_kg": 60},
    ]
}


def _make_active_session(user: UserDB, session_date: date) -> TrainingSessionDB:
    with Session(engine) as session:
        sess = TrainingSessionDB(
            user_id=user.id,
            session_date=session_date,
            status="active",
            planned_snapshot_json=json.dumps(_PLAN_SNAPSHOT),
        )
        session.add(sess)
        session.commit()
        session.refresh(sess)
        return sess


# ── D3: timezone ──────────────────────────────────────────────────────────────

def test_d3_today_endpoint_returns_warsaw_date():
    """GET /app/training/today → 'date' field equals today in Europe/Warsaw TZ."""
    user = _create_user(f"d3tz-{uuid.uuid4().hex[:6]}@test.com")
    headers = _auth_headers(user)

    resp = client.get("/app/training/today", headers=headers)
    assert resp.status_code == 200, resp.text

    warsaw_today = datetime.now(ZoneInfo("Europe/Warsaw")).date().isoformat()
    assert resp.json()["date"] == warsaw_today, (
        f"Expected Warsaw date {warsaw_today}, got {resp.json()['date']}"
    )


def test_d3_today_route_uses_warsaw_not_utc():
    """_today_warsaw() wraps datetime.now(ZoneInfo('Europe/Warsaw')).date()."""
    from app.training.routes import _today_warsaw
    result = _today_warsaw()
    expected = datetime.now(ZoneInfo("Europe/Warsaw")).date()
    assert result == expected


# ── D4: idempotencja serii ───────────────────────────────────────────────────

def test_d4_same_set_twice_is_upsert_not_duplicate():
    """Ta sama seria (exercise_key + set_number) wysłana 2x → update, nie duplikat w bazie."""
    user = _create_user(f"d4idem-{uuid.uuid4().hex[:6]}@test.com")
    headers = _auth_headers(user)
    today = datetime.now(ZoneInfo("Europe/Warsaw")).date()
    sess = _make_active_session(user, today)

    base_payload = {
        "exercise_key": "squat", "set_number": 1,
        "actual_reps": 5, "actual_weight_kg": 80.0,
        "actual_rpe": 7, "completed": True, "note": "pierwsza",
    }

    r1 = client.post(f"/app/training/sessions/{sess.id}/sets", json=base_payload, headers=headers)
    assert r1.status_code == 200, f"First log: {r1.text}"

    r2 = client.post(f"/app/training/sessions/{sess.id}/sets", json={
        **base_payload, "actual_weight_kg": 85.0, "note": "korekta"
    }, headers=headers)
    assert r2.status_code == 200, f"Second log: {r2.text}"
    assert r2.json()["status"] == "updated", f"Expected 'updated', got '{r2.json()['status']}'"
    assert r2.json()["set"]["actual_weight_kg"] == 85.0

    with Session(engine) as db:
        rows = db.exec(
            select(TrainingSetResultDB)
            .where(TrainingSetResultDB.session_id == sess.id)
            .where(TrainingSetResultDB.exercise_key == "squat")
            .where(TrainingSetResultDB.set_number == 1)
        ).all()
    assert len(rows) == 1, f"Expected 1 row, got {len(rows)} — duplikat!"


def test_d4_different_set_numbers_are_separate_rows():
    """Serie o różnych set_number tworzą osobne wiersze."""
    user = _create_user(f"d4sep-{uuid.uuid4().hex[:6]}@test.com")
    headers = _auth_headers(user)
    today = datetime.now(ZoneInfo("Europe/Warsaw")).date()
    sess = _make_active_session(user, today)

    for set_num in [1, 2, 3]:
        r = client.post(f"/app/training/sessions/{sess.id}/sets", json={
            "exercise_key": "squat", "set_number": set_num,
            "actual_reps": 5, "actual_weight_kg": 80.0, "completed": True, "note": "",
        }, headers=headers)
        assert r.status_code == 200, f"Set {set_num}: {r.text}"

    with Session(engine) as db:
        rows = db.exec(
            select(TrainingSetResultDB)
            .where(TrainingSetResultDB.session_id == sess.id)
            .where(TrainingSetResultDB.exercise_key == "squat")
        ).all()
    assert len(rows) == 3


def test_d4_last_write_wins_no_data_loss():
    """Konflikt: ostatni zapis wygrywa, pozostałe serie zachowane."""
    user = _create_user(f"d4lww-{uuid.uuid4().hex[:6]}@test.com")
    headers = _auth_headers(user)
    today = datetime.now(ZoneInfo("Europe/Warsaw")).date()
    sess = _make_active_session(user, today)

    # Device A: set 1
    r_a = client.post(f"/app/training/sessions/{sess.id}/sets", json={
        "exercise_key": "squat", "set_number": 1,
        "actual_reps": 5, "actual_weight_kg": 80.0, "completed": True, "note": "device_A",
    }, headers=headers)
    assert r_a.status_code == 200

    # Device B: set 2 (no conflict)
    r_b = client.post(f"/app/training/sessions/{sess.id}/sets", json={
        "exercise_key": "squat", "set_number": 2,
        "actual_reps": 5, "actual_weight_kg": 80.0, "completed": True, "note": "device_B",
    }, headers=headers)
    assert r_b.status_code == 200

    # Device A: re-sends set 1 with updated weight (conflict: last write wins)
    r_a2 = client.post(f"/app/training/sessions/{sess.id}/sets", json={
        "exercise_key": "squat", "set_number": 1,
        "actual_reps": 5, "actual_weight_kg": 90.0, "completed": True, "note": "device_A_retry",
    }, headers=headers)
    assert r_a2.status_code == 200
    assert r_a2.json()["set"]["actual_weight_kg"] == 90.0, "Last write (90kg) must win"

    with Session(engine) as db:
        rows = db.exec(
            select(TrainingSetResultDB)
            .where(TrainingSetResultDB.session_id == sess.id)
        ).all()
    assert len(rows) == 2, f"Expected 2 rows, got {len(rows)} — utrata danych!"
    set1 = next(r for r in rows if r.set_number == 1)
    assert set1.actual_weight_kg == 90.0


# ── D5: jedna aktywna sesja per użytkownik ────────────────────────────────────

def test_d5_second_start_does_not_create_duplicate_session():
    """POST /app/training/sessions/start gdy aktywna sesja istnieje → nie tworzy drugiej."""
    user = _create_user(f"d5single-{uuid.uuid4().hex[:6]}@test.com")
    headers = _auth_headers(user)
    today = datetime.now(ZoneInfo("Europe/Warsaw")).date()
    _make_active_session(user, today)

    r = client.post("/app/training/sessions/start", headers=headers)
    assert r.status_code in (200, 409), f"Unexpected: {r.status_code} {r.text}"

    with Session(engine) as db:
        active_sessions = db.exec(
            select(TrainingSessionDB)
            .where(TrainingSessionDB.user_id == user.id)
            .where(TrainingSessionDB.status == "active")
        ).all()
    assert len(active_sessions) == 1, f"Expected 1 active session, got {len(active_sessions)}"


def test_d5_today_shows_active_session_id():
    """GET /app/training/today zwraca istniejącą aktywną sesję z poprawnym id."""
    user = _create_user(f"d5today-{uuid.uuid4().hex[:6]}@test.com")
    headers = _auth_headers(user)
    today = datetime.now(ZoneInfo("Europe/Warsaw")).date()
    sess = _make_active_session(user, today)

    r = client.get("/app/training/today", headers=headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["session"]["id"] == sess.id, (
        f"Expected session id {sess.id}, got {data['session']}"
    )


# ── D7: historia i postępy ────────────────────────────────────────────────────

def test_d7_training_history_endpoint_returns_200():
    """GET /app/training/sessions/history → 200."""
    user = _create_user(f"d7hist-{uuid.uuid4().hex[:6]}@test.com")
    r = client.get("/app/training/sessions/history", headers=_auth_headers(user))
    assert r.status_code == 200, f"History: {r.status_code} {r.text}"


def test_d7_training_records_endpoint_returns_200():
    """GET /app/training/progress/records → 200."""
    user = _create_user(f"d7rec-{uuid.uuid4().hex[:6]}@test.com")
    r = client.get("/app/training/progress/records", headers=_auth_headers(user))
    assert r.status_code == 200, f"Records: {r.status_code} {r.text}"


def test_d7_training_progress_endpoint_returns_200():
    """GET /app/training/progress → 200."""
    user = _create_user(f"d7prog-{uuid.uuid4().hex[:6]}@test.com")
    r = client.get("/app/training/progress", headers=_auth_headers(user))
    assert r.status_code == 200, f"Progress: {r.status_code} {r.text}"


# ── D8: propozycja progresji (deterministyczna) ───────────────────────────────

def test_d8_complete_session_and_get_progression():
    """Zakończenie sesji + progresja → 200, deterministyczna."""
    user = _create_user(f"d8prog-{uuid.uuid4().hex[:6]}@test.com")
    headers = _auth_headers(user)
    today = datetime.now(ZoneInfo("Europe/Warsaw")).date()
    sess = _make_active_session(user, today)

    # Log one set so session is completable
    client.post(f"/app/training/sessions/{sess.id}/sets", json={
        "exercise_key": "squat", "set_number": 1,
        "actual_reps": 5, "actual_weight_kg": 80.0, "completed": True, "note": "",
    }, headers=headers)

    r_complete = client.post(f"/app/training/sessions/{sess.id}/complete", json={
        "final_rpe": 7, "notes": "test",
    }, headers=headers)
    assert r_complete.status_code == 200, f"Complete: {r_complete.text}"
    assert r_complete.json()["status"] in ("completed", "already_completed")

    r_prog = client.get(f"/app/training/sessions/{sess.id}/progression", headers=headers)
    assert r_prog.status_code in (200, 404), f"Progression: {r_prog.status_code} {r_prog.text}"
    if r_prog.status_code == 200:
        data = r_prog.json()
        r_prog2 = client.get(f"/app/training/sessions/{sess.id}/progression", headers=headers)
        assert r_prog2.json() == data, "Progression must be deterministic"
