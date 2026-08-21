"""Food filter service.

Enforces the rule that only verified and verified_with_notes foods
may be used in calculations and meal planning.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.enums import VerificationStatus
from app.models.food import Food

# Foods with these statuses are eligible for calculations
ELIGIBLE_STATUSES = frozenset({
    VerificationStatus.VERIFIED,
    VerificationStatus.VERIFIED_WITH_NOTES,
})

# Foods with these statuses are EXCLUDED from calculations
EXCLUDED_STATUSES = frozenset({
    VerificationStatus.UNVERIFIED,
    VerificationStatus.PENDING_REVIEW,
    VerificationStatus.CONFLICT,
    VerificationStatus.RETRACTED,
    VerificationStatus.REJECTED,
})


def get_verified_foods(
    db: Session,
    *,
    category_id: str | None = None,
    country_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[Food], int]:
    """Get foods that pass the verification filter.

    Returns (foods, total_count).
    """
    q = db.query(Food).filter(
        Food.verification_status.in_(ELIGIBLE_STATUSES),
        Food.is_active.is_(True),
    )

    if category_id:
        from uuid import UUID

        try:
            cat_uuid = UUID(category_id)
            q = q.filter(Food.category_id == cat_uuid)
        except ValueError:
            pass

    total = q.count()
    items = q.order_by(Food.name).limit(limit).offset(offset).all()
    return items, total


def is_food_eligible(food: Food) -> bool:
    """Check if a single food passes the verification filter."""
    return food.verification_status in ELIGIBLE_STATUSES and food.is_active


def get_eligible_food_slugs(db: Session) -> set[str]:
    """Get all eligible food slugs as a set for fast lookup."""
    foods = db.query(Food.slug).filter(
        Food.verification_status.in_(ELIGIBLE_STATUSES),
        Food.is_active.is_(True),
    ).all()
    return {f[0] for f in foods}


def count_eligible_foods(db: Session) -> int:
    """Count foods that pass the verification filter."""
    return db.query(Food).filter(
        Food.verification_status.in_(ELIGIBLE_STATUSES),
        Food.is_active.is_(True),
    ).count()
