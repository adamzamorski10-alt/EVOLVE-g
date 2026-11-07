"""
Auth Dependencies — FastAPI Depends for route protection
"""

import os
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.auth.jwt_utils import decode_token
from app.config import JWT_ALGORITHM, JWT_SECRET_KEY
from app.database import engine
from app.models import UserDB

_bearer_scheme = HTTPBearer(auto_error=False)


def _rate_limit_key(request: Request) -> str:
    """Use Bearer sub (user UUID) only if properly signed and not expired; otherwise fall back to client IP.
    
    Render proxy headers are handled at uvicorn level (--proxy-headers --forwarded-allow-ips="*"),
    so client IP is safely extracted from request.client.host via get_remote_address.
    Client-controlled X-Forwarded-For is never trusted directly here.
    """
    from slowapi.util import get_remote_address

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        try:
            payload = jwt.decode(
                token,
                JWT_SECRET_KEY,
                algorithms=[JWT_ALGORITHM],
                options={"verify_exp": True},
            )
            sub = payload.get("sub")
            if sub:
                return f"user:{sub}"
        except Exception:
            pass
    return get_remote_address(request)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> UserDB:
    """
    FastAPI Dependency — wyciąga użytkownika z Bearer tokena.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Brak tokena autoryzacji",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(credentials.credentials)

    # Odrzuć tokeny o nieprawidłowym typie lub braku typu (wymagany jawny access token)
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nieprawidłowy typ tokenu — wymagany access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nieprawidłowy token — brak identyfikatora użytkownika",
            headers={"WWW-Authenticate": "Bearer"},
        )
    with Session(engine) as session:
        user = session.get(UserDB, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Użytkownik z tokena nie istnieje",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Konto zostało zablokowane",
        )

    # Weryfikacja wersji sesji (unieważnienie po zmianie hasła)
    token_ver = payload.get("token_version")
    if token_ver is None or int(token_ver) != int(user.token_version or 1):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesja wygasła lub hasło zostało zmienione — zaloguj się ponownie",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_pro_user(user: UserDB = Depends(get_current_user)) -> UserDB:
    """Dependency — wymaga planu PRO."""
    if user.role not in ("pro_user", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ta funkcja wymaga planu PRO",
        )
    return user


def get_current_admin(user: UserDB = Depends(get_current_user)) -> UserDB:
    """Dependency — wymaga roli admin."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Brak uprawnień administratora",
        )
    return user
