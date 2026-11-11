"""
Auth Routes — registration, login, password change, password reset, account deletion, token refresh, export
"""

import hashlib
import logging
import re
import secrets
from datetime import datetime, timedelta
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
from app.auth.mailer import send_password_reset
from app.config import JWT_EXPIRE_MINUTES, get_env
from app.database import engine, get_session
from app.fitness.calculations import calc_calories, calc_protein
from app.models import (
    AdaptivePlanRevisionDB,
    AssessmentDB,
    DailyLogDB,
    DrillResultDB,
    ExerciseResultDB,
    GoalDB,
    NutritionAdaptationDB,
    NutritionEntryDB,
    RefreshTokenDB,
    SportAttemptDB,
    TrainingSessionDB,
    TrainingSetResultDB,
    UserDB,
    UserNumberSequenceDB,
)
from app.schemas import (
    ChangePasswordRequest,
    DeleteAccountRequest,
    LoginRequest,
    LogoutRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RefreshAccessRequest,
    RefreshAccessResponse,
    RegisterRequest,
    TokenResponse,
    UserProfile,
)

logger = logging.getLogger(__name__)

from app.config import RATE_LIMIT_ENABLED

router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=_rate_limit_key, enabled=RATE_LIMIT_ENABLED)


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
            user_key=f"native:user:pending-{secrets.token_hex(8)}",
            email=payload.email.lower().strip(),
            name=(payload.name.strip() if payload.name and payload.name.strip() else "Użytkownik"),
            hashed_password=hash_password(payload.password),
            is_active=True,
            token_version=1,
            # Dane profilu: tylko jeśli podano w żądaniu; przy braku pozostają None
            age=payload.age,
            height=payload.height,
            weight=payload.weight,
            start_weight=payload.weight,
            target_weight=payload.target_weight,
            gender=payload.gender,
            goal=payload.goal,
            frequency=payload.frequency,
            diet=payload.diet,
            role="free_user",
            plan="free",
        )

        # Oblicz kalorie/białko TYLKO jeśli użytkownik podał komplet danych biometrycznych
        if user.weight and user.height and user.age and user.gender:
            user.calories_target = calc_calories(user)
            user.protein_target = calc_protein(user)

        session.add(user)
        session.flush()

        # Atomowy numer użytkownika przez dedykowaną tabelę sekwencji
        seq_entry = UserNumberSequenceDB(user_id=user.id)
        session.add(seq_entry)
        session.flush()

        seq_num = seq_entry.id
        user.user_number = seq_num
        user.user_key = f"native:user:{seq_num}"
        session.commit()
        session.refresh(user)

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


@router.delete("/me")
def delete_account(
    payload: DeleteAccountRequest,
    user: UserDB = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Trwałe usunięcie konta użytkownika i wszystkich powiązanych danych.
    Wymaga podania aktualnego hasła w celu weryfikacji tożsamości.
    """
    if not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Podane hasło jest nieprawidłowe",
        )

    user_id = user.id

    # Usuwamy kaskadowo wszystkie powiązane rekordy użytkownika
    models_with_user_id = [
        DailyLogDB,
        NutritionEntryDB,
        NutritionAdaptationDB,
        TrainingSetResultDB,
        ExerciseResultDB,
        TrainingSessionDB,
        GoalDB,
        AdaptivePlanRevisionDB,
        DrillResultDB,
        SportAttemptDB,
        AssessmentDB,
        RefreshTokenDB,
    ]
    for model in models_with_user_id:
        records = session.exec(select(model).where(model.user_id == user_id)).all()
        for r in records:
            session.delete(r)

    # Sekwencja numeru
    sequences = session.exec(select(UserNumberSequenceDB).where(UserNumberSequenceDB.user_id == user_id)).all()
    for seq in sequences:
        session.delete(seq)

    # Rekord użytkownika
    db_user = session.get(UserDB, user_id)
    if db_user:
        session.delete(db_user)

    session.commit()
    return {"status": "ok", "message": "Konto oraz wszystkie powiązane dane zostały trwale usunięte."}


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
        db_user.updated_at = datetime.utcnow()
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


@router.post("/password-reset/request")
@limiter.limit("5/hour")
def password_reset_request(
    request: Request,
    payload: PasswordResetRequest,
    session: Session = Depends(get_session),
):
    """
    Żądanie resetu hasła.
    Celowo zwraca zawsze identyczny komunikat (brak ujawniania czy email istnieje w bazie).
    """
    clean_email = payload.email.lower().strip()
    user = session.exec(select(UserDB).where(UserDB.email == clean_email)).first()
    if user and user.is_active:
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        user.password_reset_token_hash = token_hash
        user.password_reset_expires_at = datetime.utcnow() + timedelta(hours=1)
        session.add(user)
        session.commit()
        send_password_reset(clean_email, token)

    return {
        "status": "ok",
        "message": "Jeśli konto powiązane z tym adresem e-mail istnieje, instrukcja resetu hasła została wysłana.",
    }


@router.post("/password-reset/confirm")
@limiter.limit("5/hour")
def password_reset_confirm(
    request: Request,
    payload: PasswordResetConfirmRequest,
    session: Session = Depends(get_session),
):
    """Potwierdzenie resetu hasła jednorazowym tokenem i ustawienie nowego hasła."""
    if len(payload.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Nowe hasło musi mieć co najmniej 8 znaków",
        )
    token_hash = hashlib.sha256(payload.token.strip().encode("utf-8")).hexdigest()
    user = session.exec(
        select(UserDB).where(UserDB.password_reset_token_hash == token_hash)
    ).first()

    now = datetime.utcnow()
    if not user or not user.password_reset_expires_at or user.password_reset_expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token resetu hasła jest nieprawidłowy lub wygasł",
        )

    user.hashed_password = hash_password(payload.new_password)
    user.password_reset_token_hash = None
    user.password_reset_expires_at = None
    user.token_version = (user.token_version or 1) + 1
    user.updated_at = now
    session.add(user)

    # Unieważnij wszystkie aktywne refresh tokeny
    active_tokens = session.exec(
        select(RefreshTokenDB)
        .where(RefreshTokenDB.user_id == user.id)
        .where(RefreshTokenDB.revoked == False)
    ).all()
    for rt in active_tokens:
        rt.revoked = True
        session.add(rt)

    session.commit()
    return {"status": "ok", "message": "Hasło zostało pomyślnie zresetowane. Możesz się zalogować."}


def _build_user_export(user: UserDB, session: Session) -> dict:
    """Buduje bezpieczny słownik ze wszystkimi danymi użytkownika (bez haseł i tokenów)."""
    profile = user.to_profile_dict()
    profile.pop("hashed_password", None)
    profile.pop("password_reset_token_hash", None)
    profile.pop("token_version", None)

    daily_logs = [
        log.model_dump()
        for log in session.exec(select(DailyLogDB).where(DailyLogDB.user_id == user.id)).all()
    ]
    sessions = [
        s.model_dump()
        for s in session.exec(select(TrainingSessionDB).where(TrainingSessionDB.user_id == user.id)).all()
    ]
    sets = [
        st.model_dump()
        for st in session.exec(select(TrainingSetResultDB).where(TrainingSetResultDB.user_id == user.id)).all()
    ]
    goals = [
        g.model_dump()
        for g in session.exec(select(GoalDB).where(GoalDB.user_id == user.id)).all()
    ]
    nutrition = [
        n.model_dump()
        for n in session.exec(select(NutritionEntryDB).where(NutritionEntryDB.user_id == user.id)).all()
    ]
    assessments = [
        a.model_dump()
        for a in session.exec(select(AssessmentDB).where(AssessmentDB.user_id == user.id)).all()
    ]

    return {
        "export_date": datetime.utcnow().isoformat(),
        "user_id": user.id,
        "profile": profile,
        "daily_logs": daily_logs,
        "training_sessions": sessions,
        "training_set_results": sets,
        "goals": goals,
        "nutrition_entries": nutrition,
        "assessments": assessments,
    }


@router.get("/export")
def export_user_data_auth(
    user: UserDB = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Eksportuje wszystkie dane użytkownika w formacie JSON."""
    return _build_user_export(user, session)


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
            "fitai_nickname",
        ],
    }


@router.post("/users/{user_id}", deprecated=True)
def create_or_update_user(user_id: str, profile: UserProfile):
    """DEPRECATED — wyłączony od FitAI v2.1. Użyj POST /auth/register."""
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Ten endpoint jest wyłączony. Użyj POST /auth/register.",
    )
