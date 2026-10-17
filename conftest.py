import pytest

from app.auth import routes as auth_routes


@pytest.fixture(autouse=True)
def disable_registration_rate_limit_for_tests():
    previous = auth_routes.limiter.enabled
    auth_routes.limiter.enabled = False
    yield
    auth_routes.limiter.enabled = previous
