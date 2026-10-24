from pathlib import Path


APP_INIT = (Path(__file__).parent / "app" / "__init__.py").read_text(encoding="utf-8")


def test_dashboard_boot_validates_stored_token_before_showing_dashboard():
    assert "fetch('/app/profile'" in APP_INIT
    assert "response.status === 401 || response.status === 403" in APP_INIT
    assert "localStorage.removeItem('fitai_token')" in APP_INIT
    assert "showAuthenticatedShell(false)" in APP_INIT
    assert "if (typeof initApp === 'function') initApp();" in APP_INIT
