"""Read-only Decision Engine API boundary."""
from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.auth.dependencies import get_current_user
from app.database import get_session
from app.decision_service import decision_for_user
from app.models import UserDB

router = APIRouter(prefix="/app/decision", tags=["decision"])


@router.get("/today")
def decision_today(user: UserDB = Depends(get_current_user), db: Session = Depends(get_session)):
    return decision_for_user(user=user, db=db)
