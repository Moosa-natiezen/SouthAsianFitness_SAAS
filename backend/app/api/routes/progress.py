"""Progress tracking API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import require_auth, require_csrf
from app.db.session import get_db
from app.models.user import User
from app.schemas.progress import (
    ProgressEntryCreate,
    ProgressEntryResponse,
    ProgressSummaryResponse,
)
from app.services.progress_service import (
    create_progress_entry,
    delete_progress_entry,
    get_progress_summary,
    list_progress_entries,
)

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("", response_model=list[ProgressEntryResponse])
def list_entries(
    user: Annotated[User, Depends(require_auth)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
):
    """Return the authenticated user's progress entries, newest first."""
    limit = int(request.query_params.get("limit", 100))
    offset = int(request.query_params.get("offset", 0))
    entries = list_progress_entries(db, user.id, limit=limit, offset=offset)
    return entries


@router.post("", response_model=ProgressEntryResponse, status_code=status.HTTP_201_CREATED)
def create_entry(
    payload: ProgressEntryCreate,
    user: Annotated[User, Depends(require_csrf)],
    db: Annotated[Session, Depends(get_db)],
):
    """Create a new progress entry for the authenticated user."""
    try:
        entry = create_progress_entry(
            db,
            user,
            recorded_on=payload.recorded_on,
            weight_kg=payload.weight_kg,
            waist_cm=payload.waist_cm,
            hip_cm=payload.hip_cm,
            body_fat_percent=payload.body_fat_percent,
            notes=payload.notes,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
    return entry


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(
    entry_id: str,
    user: Annotated[User, Depends(require_csrf)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Delete a progress entry owned by the authenticated user."""
    from uuid import UUID as _UUID

    try:
        entry_uuid = _UUID(entry_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Progress entry not found",
        )
    delete_progress_entry(db, user, entry_uuid)


@router.get("/summary", response_model=ProgressSummaryResponse)
def summary(
    user: Annotated[User, Depends(require_auth)],
    db: Annotated[Session, Depends(get_db)],
):
    """Return the authenticated user's calculated progress summary."""
    data = get_progress_summary(db, user)
    return ProgressSummaryResponse(**data)
