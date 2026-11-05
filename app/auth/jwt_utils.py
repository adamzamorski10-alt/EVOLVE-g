"""
Auth JWT Utilities — Token creation and decoding
"""

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import HTTPException, status
from sqlmodel import Session

from app.config import JWT_ALGORITHM, JWT_EXPIRE_MINUTES, JWT_REFRESH_EXPIRE_DAYS, JWT_SECRET_KEY
from app.models import RefreshTokenDB


def create_access_token(user_id: str, email: str, role: str, token_version: int = 1) -> str:
    """Tworzy podpisany token JWT z payloadem użytkownika i wersją tokena."""
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "token_version": int(token_version),
        "type": "access",
        "exp": exp,
        "iat": now,
        "jti": secrets.token_hex(16),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(
    user_id: str,
    token_version: int = 1,
    session: Optional[Session] = None,
) -> str:
    """Tworzy token długotrwały i rejestruje jego jti w bazie sesji."""
    now = datetime.now(timezone.utc)
    exp = now + timedelta(days=JWT_REFRESH_EXPIRE_DAYS)
    jti = secrets.token_hex(16)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "token_version": int(token_version),
        "exp": exp,
        "iat": now,
        "jti": jti,
    }
    encoded = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    if session is not None:
        db_token = RefreshTokenDB(
            user_id=str(user_id),
            jti=jti,
            expires_at=exp.replace(tzinfo=None),
            revoked=False,
            created_at=now.replace(tzinfo=None),
        )
        session.add(db_token)

    return encoded


def decode_token(token: str) -> dict:
    """Dekoduje i weryfikuje token JWT. Rzuca HTTPException przy błędzie."""
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token wygasł — zaloguj się ponownie",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Nieprawidłowy token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )
