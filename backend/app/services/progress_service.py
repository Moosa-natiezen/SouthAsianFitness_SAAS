"""Progress tracking service layer."""

from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.progress import ProgressEntry
from app.models.user import User

logger = get_logger(__name__)


def create_progress_entry(
    db: Session,
    user: User,
    *,
    recorded_on: date,
    weight_kg: Decimal,
    waist_cm: Decimal | None = None,
    hip_cm: Decimal | None = None,
    body_fat_percent: Decimal | None = None,
    notes: str | None = None,
) -> ProgressEntry:
    """Create a new progress entry for the user.

    Raises ValueError with a user-friendly message on duplicate date.
    """
    entry = ProgressEntry(
        user_id=user.id,
        recorded_on=recorded_on,
        weight_kg=weight_kg,
        waist_cm=waist_cm,
        hip_cm=hip_cm,
        body_fat_percent=body_fat_percent,
        notes=notes,
    )
    db.add(entry)
    try:
        db.flush()
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError(
            f"A progress entry for {recorded_on.isoformat()} already exists."
        )
    return entry


def list_progress_entries(
    db: Session,
    user_id: UUID,
    *,
    limit: int = 100,
    offset: int = 0,
) -> list[ProgressEntry]:
    """Return the user's progress entries ordered by date descending."""
    return (
        db.query(ProgressEntry)
        .filter(ProgressEntry.user_id == user_id)
        .order_by(ProgressEntry.recorded_on.desc(), ProgressEntry.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )


def delete_progress_entry(db: Session, user: User, entry_id: UUID) -> None:
    """Delete a progress entry owned by the user.

    Raises HTTPException 404 if the entry does not exist or does not belong to the user.
    """
    from fastapi import HTTPException, status

    entry = (
        db.query(ProgressEntry)
        .filter(ProgressEntry.id == entry_id, ProgressEntry.user_id == user.id)
        .first()
    )
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Progress entry not found",
        )
    db.delete(entry)
    db.commit()


def get_progress_summary(db: Session, user: User) -> dict:
    """Calculate the user's progress summary.

    Uses onboarding profile weight as starting weight and the latest
    progress entry weight as current weight.
    """
    profile = user.profile

    starting_weight = profile.weight_kg if profile else None
    height_cm = profile.height_cm if profile else None
    fitness_goal = profile.fitness_goal.value if profile and profile.fitness_goal else None

    # Get latest entry
    latest_entry = (
        db.query(ProgressEntry)
        .filter(ProgressEntry.user_id == user.id)
        .order_by(ProgressEntry.recorded_on.desc())
        .first()
    )

    entry_count = (
        db.query(func.count(ProgressEntry.id))
        .filter(ProgressEntry.user_id == user.id)
        .scalar()
        or 0
    )

    current_weight = latest_entry.weight_kg if latest_entry else starting_weight

    # Calculate weight change
    weight_change = None
    if starting_weight is not None and current_weight is not None:
        weight_change = current_weight - starting_weight

    # Calculate BMI
    bmi = None
    if height_cm is not None and current_weight is not None and height_cm > 0:
        height_m = height_cm / Decimal(100)
        bmi = (current_weight / (height_m * height_m)).quantize(
            Decimal("0.1"), rounding=ROUND_HALF_UP
        )

    return {
        "starting_weight_kg": starting_weight,
        "current_weight_kg": current_weight,
        "weight_change_kg": weight_change,
        "bmi": bmi,
        "fitness_goal": fitness_goal,
        "entry_count": int(entry_count),
        "height_cm": height_cm,
    }
