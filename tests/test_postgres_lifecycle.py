"""
tests/test_postgres_lifecycle.py — Etap 1.4: Pełny test integracyjny na PostgreSQL

Scenariusz:
Rejestracja → Profil → Plan → Sesja z seriami → Zakończenie → Nowe połączenie → Odczyt kompletny.

W CI test wykonuje się na usłudze PostgreSQL 16 (zgodnie z .github/workflows/tests.yml).
Lokalnie pomija się wyraźnie, jeśli brak PostgreSQL.
"""
import os
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from main import app

POSTGRES_URL = os.getenv("TEST_POSTGRESQL_URL") or (
    os.getenv("DATABASE_URL") if (os.getenv("DATABASE_URL") or "").startswith("postgres") else None
)
HAS_POSTGRES = bool(POSTGRES_URL)


@pytest.mark.skipif(
    not HAS_POSTGRES,
    reason="PostgreSQL nie jest dostępny w bieżącym środowisku; test integracyjny uruchamia się w CI z usługą PostgreSQL.",
)
def test_postgres_full_training_lifecycle_integration():
    """1.4: Rejestracja → profil → plan → sesja z seriami → nowe połączenie → odczyt kompletny."""
    client = TestClient(app)

    unique_suffix = uuid.uuid4().hex[:8]
    test_email = f"postgres-lifecycle-{unique_suffix}@example.com"
    test_password = "SuperSecretPassword2026!"

    # 1. Rejestracja
    reg_res = client.post(
        "/auth/register",
        json={
            "email": test_email,
            "password": test_password,
            "name": f"Zawodnik PG {unique_suffix}",
        },
    )
    assert reg_res.status_code == 200, f"Rejestracja nie powiodła się: {reg_res.text}"
    auth_data = reg_res.json()
    token = auth_data["access_token"]
    user_id = auth_data["user_id"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Profil
    profile_res = client.put(
        "/app/profile",
        json={
            "name": f"Zawodnik PG {unique_suffix}",
            "weight": 85.5,
            "height": 182.0,
            "training_experience": "intermediate",
            "equipment": "full_gym",
            "goal": "strength",
        },
        headers=headers,
    )
    assert profile_res.status_code == 200, f"Aktualizacja profilu: {profile_res.text}"

    # 3. Plan — generowanie lub weryfikacja planu bazowego
    plan_res = client.post(
        "/app/plan/generate",
        json={
            "goal": "strength",
            "frequency": 3,
            "equipment": "full_gym",
        },
        headers=headers,
    )
    # Jeśli endpoint generate istnieje i tworzy plan:
    assert plan_res.status_code in (200, 201), f"Plan generate: {plan_res.text}"

    # 4. Sesja z seriami — rozpoczęcie aktywnej sesji
    start_res = client.post(
        "/app/training/sessions/start",
        json={},
        headers=headers,
    )
    assert start_res.status_code == 200, f"Start sesji: {start_res.text}"
    sess_data = start_res.json()["session"]
    sess_id = sess_data["id"]

    # Pobierz pierwsze ćwiczenie ze snapshotu sesji
    exercises = sess_data.get("planned", {}).get("exercises", [])
    if not exercises:
        ex_key = "squat"
        ex_name = "Przysiad ze sztangą"
    else:
        ex_key = exercises[0].get("exercise_key", "squat")
        ex_name = exercises[0].get("exercise_name", "Przysiad ze sztangą")

    # Zapisz 3 serie z unikalnymi client_id
    client_ids = [str(uuid.uuid4()) for _ in range(3)]
    for idx, cid in enumerate(client_ids, 1):
        set_res = client.post(
            f"/app/training/sessions/{sess_id}/sets",
            json={
                "client_id": cid,
                "exercise_key": ex_key,
                "set_number": idx,
                "actual_reps": 8,
                "actual_weight_kg": 80.0 + (idx * 5.0),
                "actual_rpe": 7 + idx,
                "completed": True,
                "note": f"Seria PG {idx}",
            },
            headers=headers,
        )
        assert set_res.status_code == 200, f"Zapis serii {idx}: {set_res.text}"
        assert set_res.json()["set"]["client_id"] == cid

    # 5. Zakończenie sesji
    complete_res = client.post(
        f"/app/training/sessions/{sess_id}/complete",
        json={
            "final_rpe": 8,
            "notes": "Ukończono w teście integracyjnym PostgreSQL",
        },
        headers=headers,
    )
    assert complete_res.status_code == 200, f"Zakończenie sesji: {complete_res.text}"
    assert complete_res.json()["status"] == "completed"

    # 6. Nowe, niezależne połączenie do PostgreSQL — weryfikacja na poziomie silnika bazy
    direct_engine = create_engine(POSTGRES_URL)
    with direct_engine.connect() as conn:
        # Weryfikacja sesji
        session_row = conn.execute(
            text("SELECT id, status, user_id, final_rpe FROM training_sessions WHERE id = :sid"),
            {"sid": sess_id},
        ).fetchone()
        assert session_row is not None, "Brak sesji w PostgreSQL!"
        assert session_row.status == "completed"
        assert session_row.user_id == user_id
        assert session_row.final_rpe == 8

        # Weryfikacja serii
        set_rows = conn.execute(
            text(
                "SELECT id, client_id, set_number, actual_weight_kg, actual_reps "
                "FROM training_set_results WHERE session_id = :sid ORDER BY set_number ASC"
            ),
            {"sid": sess_id},
        ).fetchall()
        assert len(set_rows) == 3, f"Oczekiwano 3 serii w PostgreSQL, znaleziono {len(set_rows)}"
        saved_cids = [r.client_id for r in set_rows]
        assert saved_cids == client_ids, "Niezgodność client_id w PostgreSQL"
    direct_engine.dispose()

    # 7. Odczyt kompletny przez API w nowym żądaniu
    get_res = client.get(f"/app/training/sessions/{sess_id}", headers=headers)
    assert get_res.status_code == 200, f"Odczyt sesji przez API: {get_res.text}"
    read_data = get_res.json()["session"]
    assert read_data["status"] == "completed"
    assert len(read_data["sets"]) == 3
    assert [s["client_id"] for s in read_data["sets"]] == client_ids

