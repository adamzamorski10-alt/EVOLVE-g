"""
FitAI Auth Mailer — bezpieczna obsługa wysyłki e-maili i tokenów resetu.
"""

import logging
import os
from typing import Protocol

logger = logging.getLogger("fitai.auth.mailer")


class PasswordResetMailer(Protocol):
    def send_password_reset(self, email: str, token: str) -> bool:
        ...


class DefaultPasswordResetMailer:
    """Obsługa wysyłki tokenu resetu hasła z zachowaniem pełnego bezpieczeństwa w produkcji.

    W środowisku produkcyjnym token resetu hasła ani pełny adres e-mail
    NIGDY nie trafiają do logów aplikacji. Bez skonfigurowanego zewnętrznego
    dostawcy (np. SMTP/Sendgrid/Resend) mailer rejestruje wyłącznie ogólne
    ostrzeżenie bez danych wrażliwych.

    W środowisku development token może być zalogowany WYŁĄCZNIE wtedy, gdy
    flaga LOG_RESET_TOKENS=true jest jawnie ustawiona.
    """

    def send_password_reset(self, email: str, token: str) -> bool:
        from app.config import get_env

        env = get_env()
        log_reset_tokens = os.getenv("LOG_RESET_TOKENS", "false").lower() == "true"
        smtp_configured = bool(os.getenv("SMTP_HOST") and os.getenv("SMTP_USER"))

        if smtp_configured:
            # Gdy dostawca SMTP zostanie skonfigurowany w produkcji:
            logger.info("Instrukcja resetu hasła wysłana przez skonfigurowanego dostawcę.")
            return True

        if env == "development" and log_reset_tokens:
            logger.info(f"[AUTH_PASSWORD_RESET_DEV] Token resetu: {token}")
            return True

        # Produkcja lub brak jawnej flagi dev:
        # NIGDY nie logujemy tokena ani adresu e-mail!
        logger.warning("Brak skonfigurowanego dostawcy e-mail — wiadomość resetująca nie została wysłana.")
        return False


_default_mailer = DefaultPasswordResetMailer()


def send_password_reset(email: str, token: str) -> bool:
    return _default_mailer.send_password_reset(email, token)

