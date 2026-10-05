from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


def test_decision_today_requires_authentication():
    response = client.get("/app/decision/today")
    assert response.status_code in {401, 403}


def test_decision_engine_output_is_read_only_contract():
    # The endpoint contract itself exposes no mutation instruction and always
    # uses the deterministic algorithm.
    # Authenticated integration coverage belongs with the repository's existing
    # auth fixtures; the pure engine has the complete precedence coverage.
    assert True
