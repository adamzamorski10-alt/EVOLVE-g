from pathlib import Path


APP_INIT = (Path(__file__).parent / "app" / "__init__.py").read_text(encoding="utf-8")


def test_dashboard_boot_validates_stored_token_before_showing_dashboard():
    assert "fetch('/app/profile'" in APP_INIT
    assert "error.status !== 401 && error.status !== 403" in APP_INIT
    assert "refresh-access" in APP_INIT
    assert "await validateAccessToken(refreshed.access_token)" in APP_INIT
    assert "'fitai_token'" in APP_INIT
    assert "auth-loading" in APP_INIT
    assert "if (typeof initApp === 'function') initApp();" in APP_INIT


def test_auth_boot_does_not_clear_user_data_or_open_preview_dashboard():
    assert "fitai_profile_cache" not in APP_INIT
    assert "fitai_training_plan" not in APP_INIT
    assert "enterDashboard();" not in APP_INIT.split("window.EVOLVE_AUTH_READY", 1)[0]
