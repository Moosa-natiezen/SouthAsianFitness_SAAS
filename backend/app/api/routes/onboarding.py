from __future__ import annotations

from typing import Annotated

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
    user: Annotated[User, Depends(require_csrf)],
    db: Annotated[Session, Depends(get_db)],
):
    submit_onboarding(db, user, payload.model_dump())
    # Re-fetch the profile to get the calculated TDEE targets
    db.refresh(user)
    profile = user.profile
    return OnboardingResponse(
        status="ok",
        is_onboarded=True,
        target_calories=profile.target_calories if profile else None,
        target_protein_g=float(profile.target_protein_g) if profile and profile.target_protein_g else None,
    )
