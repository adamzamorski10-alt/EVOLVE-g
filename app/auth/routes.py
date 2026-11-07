"""
Auth Routes — registration, login, password change, token refresh
"""

import re
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmodel import Session, select

from app.auth import (
    _rate_limit_key,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.auth.jwt_utils import create_refresh_token, decode_token
from app.config import JWT_EXPIRE_MINUTES
from app.database import engine, get_session
from app.fitness.calculations import calc_calories, calc_protein
from app.models import RefreshTokenDB, UserDB, UserNumberSequenceDB
from app.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshAccessRequest,
    RefreshAccessResponse,
    RegisterRequest,
    TokenResponse,
    UserProfile,
)

router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=_rate_limit_key)


@router.post("/register", response_model=TokenResponse)
@limiter.limit("5/hour")
def register(request: Request, payload: RegisterRequest):
    """
    Rejestracja nowego użytkownika — tylko email i hasło.
    Numer użytkownika generowany automatycznie.
    """
    with Session(engine) as session:
        # Sprawdź unikalność e-maila
        existing = session.exec(
            select(UserDB).where(UserDB.email == payload.email.lower().strip())
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Konto z tym e-mailem już istnieje",
            )

        # Utwórz użytkownika BEZ user_number na razie — zostanie nadany atomowo poniżej
        user = UserDB(
            user_key="native:user:pending",        # tymczasowy — nadpisany po flush()
            email=payload.email.lower().strip(),
            nickname=None,                          # Nick nie jest wymagany
            user_number=None,                       # nadany atomowo przez sekwencję
            hashed_password=hash_password(payload.password),
            name=payload.name or "",                # tymczasowe — nadpisane po flush()
            age=payload.age,
            height=payload.height,
            weight=payload.weight,
            start_weight=payload.weight,
            target_weight=payload.target_weight,
            gender=payload.gender or "mężczyzna",
            goal=payload.goal,
            frequency=payload.frequency,
            diet=payload.diet,
            is_active=True,
            token_version=1,
        )
        if user.weight and user.height and user.age:
            user.calories_target = calc_calories(user)
            user.protein_target = calc_protein(user)
        else:
            user.calories_target = 0
            user.protein_target = 0
        session.add(user)
        session.flush()  # user.id jest teraz dostępne, transakcja jeszcze otwarta

        # Atomowe przydzielenie numeru przez AUTOINCREMENT SQLite
        seq_row = UserNumberSequenceDB(user_id=user.id)
        session.add(seq_row)
        session.flush()  # seq_row.id zostaje nadany atomowo przez SQLite

        user.user_number = seq_row.id
        user.user_key = f"native:user:{seq_row.id}"
        user.name = payload.name or f"Użytkownik#{seq_row.id:04d}"

        try:
            session.commit()
            session.refresh(user)
        except IntegrityError:
            session.rollback()
            # Sprawdź PRAWDZIWĄ przyczynę konfliktu
            existing_email = session.exec(
                select(UserDB).where(UserDB.email == payload.email.lower().strip())
            ).first()
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Konto z tym e-mailem już istnieje",
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Nie udało się utworzyć konta — spróbuj ponownie",
            )
        except SQLAlchemyError as exc:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Błąd bazy danych: {exc}",
            )

        token = create_access_token(user.id, user.email, user.role, token_version=user.token_version)
        refresh_tok = create_refresh_token(user.id, token_version=user.token_version, session=session)
        session.commit()
        return TokenResponse(
            access_token=token,
            refresh_token=refresh_tok,
            user_id=user.id,
            user_number=user.user_number,
            display_name=user.display_name,
            name=user.name,
            role=user.role,
            plan=user.plan,
        )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute;50/hour")
def login(request: Request, payload: LoginRequest):
    """
    Logowanie email + hasło. Zwraca JWT.
    Endpoint publiczny — nie wymaga tokena.
    """
    with Session(engine) as session:
        user = session.exec(
            select(UserDB).where(UserDB.email == payload.email.lower().strip())
        ).first()

        # Celowo jednolity komunikat błędu — nie ujawniamy czy email istnieje
        _INVALID = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nieprawidłowy e-mail lub hasło",
            headers={"WWW-Authenticate": "Bearer"},
        )
        if not user:
            raise _INVALID
        if not user.hashed_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="To konto używa logowania zewnętrznego (Netlify Identity). "
                "Użyj oryginalnego dostawcy.",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Konto zostało zablokowane. Skontaktuj się z pomocą techniczną.",
            )
        if not verify_password(payload.password, user.hashed_password):
            raise _INVALID

        token = create_access_token(user.id, user.email, user.role, token_version=user.token_version)
        refresh_tok = create_refresh_token(user.id, token_version=user.token_version, session=session)
        session.commit()
        return TokenResponse(
            access_token=token,
            refresh_token=refresh_tok,
            user_id=user.id,
            user_number=user.user_number,
            display_name=user.display_name,
            name=user.name,
            role=user.role,
            plan=user.plan,
        )


@router.get("/me")
def me(user: UserDB = Depends(get_current_user)):
    """Zwraca profil aktualnie zalogowanego użytkownika."""
    return user.to_profile_dict()


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    user: UserDB = Depends(get_current_user),
):
    """Zmiana hasła — wymaga podania aktualnego hasła."""
    if not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Konto zewnętrzne — zmień hasło u dostawcy identity.",
        )
    if not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Aktualne hasło jest nieprawidłowe",
        )
    if len(payload.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Nowe hasło musi mieć co najmniej 8 znaków",
        )
    with Session(engine) as session:
        db_user = session.get(UserDB, user.id)
        db_user.hashed_password = hash_password(payload.new_password)
        db_user.token_version = (db_user.token_version or 1) + 1
        db_user.updated_at = datetime.now()
        session.add(db_user)
        
        # Unieważnij wszystkie aktywne refresh tokeny tego użytkownika
        active_tokens = session.exec(
            select(RefreshTokenDB)
            .where(RefreshTokenDB.user_id == db_user.id)
            .where(RefreshTokenDB.revoked == False)
        ).all()
        for rt in active_tokens:
            rt.revoked = True
            session.add(rt)
        session.commit()
    return {"status": "ok", "message": "Hasło zostało zmienione"}


@router.post("/refresh", response_model=TokenResponse)
def refresh(user: UserDB = Depends(get_current_user)):
    """
    Odświeżenie tokena z zachowaniem wersji tokena i rotacją refresh tokena w bazie.
    """
    with Session(engine) as session:
        db_user = session.get(UserDB, user.id)
        current_version = db_user.token_version if db_user else 1
        token = create_access_token(user.id, user.email, user.role, token_version=current_version)
        refresh_tok = create_refresh_token(user.id, token_version=current_version, session=session)
        session.commit()
    return TokenResponse(
        access_token=token,
        refresh_token=refresh_tok,
        user_id=user.id,
        user_number=user.user_number,
        display_name=user.display_name,
        name=user.name,
        role=user.role,
        plan=user.plan,
    )


@router.get("/check-nickname")
def check_nickname(nickname: str, session: Session = Depends(get_session)):
    if not nickname or len(nickname.strip()) < 3:
        return {"available": False, "reason": "Za krótki (min. 3 znaki)"}

    normalized = nickname.strip().lower()
    if len(normalized) > 30:
        return {"available": False, "reason": "Za długi (max 30 znaków)"}
    if not re.match(r"^[a-z0-9_\-.]+$", normalized):
        return {"available": False, "reason": "Nieprawidłowe znaki (tylko a-z, 0-9, _ - .)"}

    existing = session.exec(select(UserDB).where(UserDB.nickname == normalized)).first()
    return {
        "available": existing is None,
        "nickname": normalized,
        "reason": None if existing is None else "Ten nick jest już zajęty",
    }


@router.post("/refresh-access", response_model=RefreshAccessResponse)
def refresh_access_token(payload: RefreshAccessRequest, session: Session = Depends(get_session)):
    """
    Wymienia długotrwały refresh token na nowy access token ORAZ nowy refresh token (rotacja).
    Weryfikuje typ tokena, wersję sesji (token_version) oraz jednorazowość jti.
    """
    try:
        decoded = decode_token(payload.refresh_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesja wygasła — zaloguj się ponownie",
        )

    if decoded.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nieprawidłowy typ tokenu — wymagany refresh token",
        )

    user = session.get(UserDB, decoded.get("sub"))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Konto nieaktywne lub nie istnieje",
        )

    # Weryfikacja wersji sesji (unieważnienie po zmianie hasła)
    if decoded.get("token_version") != user.token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesja wygasła lub hasło zostało zmienione — zaloguj się ponownie",
        )

    jti = decoded.get("jti")
    if not jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nieprawidłowy token — brak jti",
        )

    stored = session.exec(select(RefreshTokenDB).where(RefreshTokenDB.jti == jti)).first()
    if not stored or stored.revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesja wygasła lub została unieważniona",
        )

    # Unieważnij poprzedni refresh token (rotacja — ochrona przed ponownym użyciem)
    stored.revoked = True
    session.add(stored)

    new_access = create_access_token(user.id, user.email, user.role, token_version=user.token_version)
    new_refresh = create_refresh_token(user.id, token_version=user.token_version, session=session)
    session.commit()

    return RefreshAccessResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        token_type="bearer",
        expires_in=JWT_EXPIRE_MINUTES * 60,
    )


@router.post("/logout")
def auth_logout(
    payload: Optional[LogoutRequest] = None,
    session: Session = Depends(get_session),
):
    """
    Wylogowanie: unieważnia refresh token w bazie i zwraca pełną listę kluczy storage do wyczyszczenia.
    """
    if payload and payload.refresh_token:
        try:
            decoded = decode_token(payload.refresh_token)
            jti = decoded.get("jti")
            if jti:
                stored = session.exec(select(RefreshTokenDB).where(RefreshTokenDB.jti == jti)).first()
                if stored:
                    stored.revoked = True
                    session.add(stored)
                    session.commit()
        except Exception:
            pass

    return {
        "status": "logged_out",
        "message": "Wylogowano pomyślnie",
        "clear_storage": [
            "fitai_token", "fitai_refresh_token", "fitai_user", "fitai_identity_id",
            "fitai_user_id", "fitai_user_number", "fitai_display_name", "fitai_name",
            "fitai_role", "fitai_plan", "fitai_kcal_target", "fitai_protein_target",
            "fitai_nickname", "fitai_user_data", "fitai_profiles_v3", "fitai_profile_cache",
            "fitai_weekly_plan", "fitai_logs_v3", "fitai_checked_v3", "fitai_day_checked",
            "fitai_extras_v3", "fitai_training_plan", "fitai_diet_plan", "fitai_prefs",
            "fitai_training_locations", "fitai_sport_profile", "fitai_sport_v1",
        ],
    }


def ensure_demo_user_session(session: Session) -> dict:
    """Pobiera lub tworzy dedykowanego użytkownika demonstracyjnego demo@evolve.app."""
    user = session.exec(select(UserDB).where(UserDB.email == "demo@evolve.app")).first()
    if not user:
        user = UserDB(
            user_key="native:user:demo",
            user_number=999999,
            email="demo@evolve.app",
            name="Zawodnik EVOLVE",
            role="pro_user",
            plan="pro",
            is_active=True,
            age=25,
            height=188.0,
            weight=84.0,
            start_weight=84.0,
            target_weight=84.0,
            goal="strength_hypertrophy",
            frequency="4",
            diet="zbilansowana",
            calories_target=2800,
            protein_target=170,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

    token = create_access_token(str(user.id), user.email or "demo@evolve.app", user.role or "pro_user")
    return {
        "access_token": token,
        "token": token,
        "user_id": str(user.id),
        "user_number": user.user_number or 999999,
        "display_name": user.name or "Zawodnik EVOLVE",
        "name": user.name or "Zawodnik EVOLVE",
        "role": user.role or "pro_user",
        "plan": user.plan or "pro",
        "kcal_target": user.calories_target or 2800,
        "protein_target": user.protein_target or 170,
    }


@router.get("/demo-token")
@router.post("/demo-login")
def demo_login(session: Session = Depends(get_session)):
    """Tymczasowy endpoint demo - dostępny wyłącznie w środowisku development za jawną flagą."""
    import os
    env = os.getenv("ENV", "development").lower()
    allow_demo = os.getenv("ALLOW_DEMO_LOGIN", "false").lower() == "true"
    if env != "development" or not allow_demo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint niedostępny",
        )
    return ensure_demo_user_session(session)



@router.post("/users/{user_id}", deprecated=True)
def create_or_update_user(user_id: str, profile: UserProfile):
    """DEPRECATED — wyłączony od FitAI v2.1. Użyj POST /auth/register."""
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Ten endpoint jest wyłączony. Użyj POST /auth/register.",
    )