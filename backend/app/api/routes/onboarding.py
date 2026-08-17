from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_csrf
from app.db.session import get_db
from app.models.user import User
from app.schemas.onboarding import OnboardingRequest, OnboardingResponse
from app.services.auth_service import submit_onboarding

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/onboarding", response_model=OnboardingResponse)
def save_onboarding(
    payload: OnboardingRequest,
    user: User = Depends(require_csrf),
    db: Session = Depends(get_db),
):
    submit_onboarding(db, user, payload.model_dump())
    return OnboardingResponse(status="ok", is_onboarded=True)
