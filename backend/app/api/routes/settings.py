"""Settings API routes.

Provides endpoints for reading and updating the authenticated user's
profile and preferences.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_auth, require_csrf
from app.db.session import get_db
from app.models.user import User
from app.schemas.settings import (
    PreferencesUpdateRequest,
    ProfileUpdateRequest,
    SettingsResponse,
)
from app.services.settings_service import (
    get_user_settings,
    update_user_preferences,
    update_user_profile,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/settings", response_model=SettingsResponse)
def get_settings(
    user: Annotated[User, Depends(require_auth)],
    db: Annotated[Session, Depends(get_db)],
):
    """Return the authenticated user's current settings."""
    data = get_user_settings(db, user)
    return SettingsResponse(**data)


@router.patch("/profile")
def update_profile(
    payload: ProfileUpdateRequest,
    user: Annotated[User, Depends(require_csrf)],
    db: Annotated[Session, Depends(get_db)],
):
    """Update the authenticated user's profile and user-level settings."""
    update_user_profile(db, user, payload.model_dump(exclude_unset=True))
    return {"status": "ok"}


@router.patch("/preferences")
def update_preferences(
    payload: PreferencesUpdateRequest,
    user: Annotated[User, Depends(require_csrf)],
    db: Annotated[Session, Depends(get_db)],
):
    """Update the authenticated user's dietary and budget preferences."""
    update_user_preferences(db, user, payload.model_dump(exclude_unset=True))
    return {"status": "ok"}
