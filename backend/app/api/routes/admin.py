"""Admin utility routes.

Currently hosts the one-shot seed endpoint used to populate the prepared
South Asian dish catalog on hosts without shell access (Render free tier).
Intentionally unauthenticated — it only INSERTs the fixed dish catalog and
is idempotent (re-running skips existing slugs), so it can never mutate or
expose user data. Remove this router once production data is seeded.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.logging import get_logger
from app.services.dish_seed import seed_prepared_dishes

logger = get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


class SeedFoodsResponse(BaseModel):
    status: str
    message: str
    created: int
    skipped: int


@router.get("/seed-foods", response_model=SeedFoodsResponse)
def seed_foods(db: Session = Depends(get_db)) -> SeedFoodsResponse:
    """Seed the prepared South Asian dish catalog. Idempotent.

    Exists because Render's free tier has no shell access — hit this URL
    from a browser once after deploying to populate the dish catalog.
    Safe to call repeatedly: existing slugs are skipped, never duplicated.
    """
    try:
        created, skipped = seed_prepared_dishes(db)
    except SQLAlchemyError:
        logger.exception("Prepared-dish seed failed")
        raise HTTPException(
            status_code=503,
            detail="Seeding failed due to a database error. Please try again.",
        ) from None

    return SeedFoodsResponse(
        status="success",
        message=f"South Asian foods seeded: {created} created, {skipped} skipped",
        created=created,
        skipped=skipped,
    )
