"""
test_stage1_remove_demo.py — ETAP 1: Usunięcie demo-loginu w całości

Weryfikuje:
- 1.1: Brak tras /auth/demo-token i /auth/demo-login (zwracają 404 bez względu na ENV).
       Brak funkcji ensure_demo_user_session i flagi ALLOW_DEMO_LOGIN w konfiguracji.
- 1.2: Brak jakiegokolwiek wstrzykiwania tokena lub domyślnych danych konta w index.html.
- 1.3: HTML z /, /app, /app/ nie zawiera JWT, nie zawiera evolve-auto-auth, nie zawiera _evolveDemoToken
       (dla ENV=production i ENV=development, przy pustej i niepustej bazie).
- 1.4: Po rejestracji użytkownika żaden publiczny endpoint ani HTML nie wydaje tokena bez hasła.
- 1.5: Działanie skryptu scripts/reset_shared_demo_account.py na bazie tymczasowej.
"""
import os
import re
import subprocess
import sys
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import app
from app.database import engine
from app.models import UserDB

JWT_PATTERN = re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.")


@pytest.fixture
def client():
    return TestClient(app)


def test_1_1_demo_endpoints_do_not_exist_in_any_env(client, monkeypatch):
    """1.1: /auth/demo-token oraz /auth/demo-login zwracają 404 w każdym środowisku."""
    for env_val in ["production", "development", "staging"]:
        monkeypatch.setenv("ENV", env_val)
        res_get = client.get("/auth/demo-token")
        assert res_get.status_code == 404, f"Expected 404 for GET /auth/demo-token in {env_val}, got {res_get.status_code}"

        res_post = client.post("/auth/demo-login")
        assert res_post.status_code == 404, f"Expected 404 for POST /auth/demo-login in {env_val}, got {res_post.status_code}"


def test_1_1_ensure_demo_user_session_removed():
    """1.1: Funkcja ensure_demo_user_session została usunięta z app.auth.routes."""
    import app.auth.routes as auth_routes
    assert not hasattr(auth_routes, "ensure_demo_user_session"), (
        "ensure_demo_user_session must be removed from app.auth.routes"
    )


def test_1_1_allow_demo_login_removed_from_config():
    """1.1: Flaga ALLOW_DEMO_LOGIN nie istnieje w konfiguracji."""
    import app.config as config
    assert not hasattr(config, "ALLOW_DEMO_LOGIN"), (
        "ALLOW_DEMO_LOGIN must be removed from app.config"
    )


def test_1_3_html_never_contains_jwt_or_demo_injection(client, monkeypatch):
    """1.3: Odpowiedź HTML z /, /app, /app/ NIE zawiera żadnego JWT, evolve-auto-auth ani _evolveDemoToken."""
    for env_val in ["production", "development"]:
        monkeypatch.setenv("ENV", env_val)
        for path in ["/", "/app", "/app/"]:
            resp = client.get(path)
            assert resp.status_code == 200, f"Expected 200 for {path} in {env_val}, got {resp.status_code}"
            body = resp.text

            assert not JWT_PATTERN.search(body), f"Found JWT in HTML response for {path} in {env_val}!"
            assert "evolve-auto-auth" not in body, f"Found evolve-auto-auth in HTML for {path} in {env_val}"
            assert "_evolveDemoToken" not in body, f"Found _evolveDemoToken in HTML for {path} in {env_val}"


def test_1_4_no_token_leak_after_user_registered(client):
    """1.4: Po rejestracji użytkownika żaden publiczny endpoint ani HTML nie wydaje tokena bez hasła."""
    email = f"owner_{uuid.uuid4().hex[:6]}@example.com"
    pwd = "SuperSecretPassword123!"

    # Rejestracja
    reg_res = client.post("/auth/register", json={"email": email, "password": pwd})
    assert reg_res.status_code == 200, reg_res.text
    user_id = reg_res.json()["user_id"]

    # Sprawdzenie HTML — nie zawiera tokena ani id użytkownika
    for path in ["/", "/app", "/app/"]:
        resp = client.get(path)
        assert resp.status_code == 200
        assert not JWT_PATTERN.search(resp.text)
        assert "evolve-auto-auth" not in resp.text
        assert "_evolveDemoToken" not in resp.text
        assert user_id not in resp.text

    # Próba wejścia na endpointy publiczne/auth
    assert client.get("/auth/demo-token").status_code == 404
    assert client.post("/auth/demo-login").status_code == 404
    assert client.get("/auth/me").status_code == 401


def test_1_5_reset_shared_demo_account_script(tmp_path):
    """1.5: Skrypt reset_shared_demo_account.py działa poprawnie w trybie dry-run i execute."""
    script_path = os.path.join(os.path.dirname(__file__), "scripts", "reset_shared_demo_account.py")
    assert os.path.exists(script_path), f"Script {script_path} must exist"

    # Przygotuj tymczasową bazę SQLite
    test_db_file = tmp_path / "test_reset.db"
    db_url = f"sqlite:///{test_db_file}"

    # Wykonaj migracje alembic na testowej bazie
    env = os.environ.copy()
    env["DATABASE_URL"] = db_url
    env["ENV"] = "development"
    env["JWT_SECRET_KEY"] = "ci-jwt-secret-key-32-bytes-minimum-for-tests"
    env["CRON_SECRET"] = "ci-cron-secret"

    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        env=env,
        check=True,
        capture_output=True,
    )

    # Utwórz konto demo i powiązane rekordy w testowej bazie
    from sqlalchemy import create_engine
    test_engine = create_engine(db_url)
    with Session(test_engine) as session:
        u = UserDB(
            user_key="native:user:shared01",
            user_number=1,
            email="shared01@example.com",
            name="Zawodnik EVOLVE",
            hashed_password="old_hash_secret",
            age=25,
            height=188.0,
            weight=84.0,
        )
        session.add(u)
        session.commit()
        session.refresh(u)
        uid = u.id

    # 1. Dry run
    res_dry = subprocess.run(
        [sys.executable, script_path, "--database-url", db_url, "--email", "shared01@example.com", "--dry-run"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "[DRY-RUN]" in res_dry.stdout
    assert "shared01@example.com" in res_dry.stdout

    # W bazie dane nadal są nienaruszone
    with Session(test_engine) as session:
        check_u = session.exec(select(UserDB).where(UserDB.email == "shared01@example.com")).first()
        assert check_u is not None
        assert check_u.name == "Zawodnik EVOLVE"
        assert check_u.age == 25

    # 2. Execute reset-data + new password
    res_exec = subprocess.run(
        [
            sys.executable,
            script_path,
            "--database-url",
            db_url,
            "--email",
            "shared01@example.com",
            "--reset-data",
            "--password",
            "BrandNewSafePassword999!",
            "--execute",
        ],
        capture_output=True,
        text=True,
    )
    if res_exec.returncode != 0:
        pytest.fail(f"Script failed (rc={res_exec.returncode}):\nSTDOUT: {res_exec.stdout}\nSTDERR: {res_exec.stderr}")
    assert "[EXECUTE]" in res_exec.stdout

    with Session(test_engine) as session:
        updated_u = session.exec(select(UserDB).where(UserDB.email == "shared01@example.com")).first()
        assert updated_u is not None
        assert updated_u.age is None
        assert updated_u.height is None
        assert updated_u.weight is None
        assert updated_u.name != "Zawodnik EVOLVE"
        from app.auth.security import verify_password
        assert verify_password("BrandNewSafePassword999!", updated_u.hashed_password)
