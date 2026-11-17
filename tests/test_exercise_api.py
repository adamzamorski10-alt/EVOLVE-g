"""Testy endpointów API ćwiczeń: GET /app/exercises/{id} i /app/exercises/by-name."""

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.__init__ import app
from app.auth.jwt_utils import create_access_token
from app.database import engine
from app.models import UserDB

client = TestClient(app)
TOKEN = None


def _ensure_user():
    global TOKEN
    if TOKEN is not None:
        return
    with Session(engine) as session:
        user = session.exec(
            UserDB.__table__.select().where(UserDB.email == "api_exercise_t@example.com")
        ).first()
        if user is None:
            user = UserDB(
                user_key="native:user:api_exercise_t",
                email="api_exercise_t@example.com",
                name="Api Exercise T",
                hashed_password="$2b$12$hashed",
                is_active=True,
                token_version=1,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
    TOKEN = create_access_token(user.id, user.email, "user", token_version=1)


def _auth_headers():
    _ensure_user()
    return {"Authorization": "Bearer " + TOKEN}


def test_exercise_by_id_existing():
    r = client.get("/app/exercises/barbell_bench_press", headers=_auth_headers())
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == "barbell_bench_press"
    assert data["name_pl"] == "Wyciskanie sztangi leżąc"
    assert data["summary"] and "siłowe" in data["summary"]
    assert len(data["execution"]) == 6
    assert len(data["cues"]) == 3
    assert len(data["common_mistakes"]) == 4
    assert data["easier_note"] and "hantli" in data["easier_note"]
    assert data["breathing"] and "Wdech" in data["breathing"]
    assert data["description_status"] == "needs_review"
    assert "bark" in data["contraindications"]
    assert "sztanga" in data["equipment"]
    assert data["level"] == "beginner"


def test_exercise_by_name_existing():
    r = client.get("/app/exercises/by-name", params={"name": "Przysiad goblet z hantlem"}, headers=_auth_headers())
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == "goblet_squat"
    assert data["name_pl"] == "Przysiad goblet z hantlem"
    assert data["description_status"] == "needs_review"


def test_exercise_by_name_alias():
    r = client.get("/app/exercises/by-name", params={"name": "pompki klasyczne"}, headers=_auth_headers())
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == "pushups_classic"


def test_exercise_by_id_unknown_404():
    r = client.get("/app/exercises/nieistniejące_id", headers=_auth_headers())
    assert r.status_code == 404


def test_exercise_by_name_unknown_404():
    r = client.get("/app/exercises/by-name", params={"name": "Nie ma takiego ćwiczenia"}, headers=_auth_headers())
    assert r.status_code == 404


def test_exercise_without_auth_401():
    r = client.get("/app/exercises/barbell_bench_press")
    assert r.status_code == 401
