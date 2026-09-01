"""AI-powered meal plan generation routes.

Provides SSE streaming of AI-generated meal plans via GPT-4o-mini,
and persistence for saved AI meal plans.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_auth, require_pro
from app.core.logging import get_logger
from app.models.meal_plan import SavedMealPlan
from app.models.user import User
from app.schemas.meal_plan import (
    SavedMealPlanListResponse,
    SavedMealPlanOut,
    SaveMealPlanRequest,
)
from app.schemas.nutrition import MealPlanRequest
from app.services.ai_service import generate_meal_plan_stream

logger = get_logger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/meal-plans/generate")
async def generate_ai_meal_plan(
    body: MealPlanRequest,
    user: Annotated[User, Depends(require_pro)],
) -> StreamingResponse:
    """Stream an AI-generated meal plan using GPT-4o-mini.

    Returns Server-Sent Events (SSE) with the meal plan content.
    Requires an active Pro subscription.
    """
    return StreamingResponse(
        generate_meal_plan_stream(body),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/meal-plans/save")
def save_ai_meal_plan(
    user: Annotated[User, Depends(require_auth)],
    db: Session = Depends(get_db),
    body: SaveMealPlanRequest = ...,
) -> dict:
    """Save an AI-generated meal plan to the database."""
    saved = SavedMealPlan(
        user_id=user.id,
        title=body.title,
        content=body.content,
        target_calories=body.target_calories,
        protein_g=body.protein_g,
    )
    db.add(saved)
    db.commit()
    db.refresh(saved)

    logger.info(
        "Saved AI meal plan for user %s: title=%s id=%s",
        user.id, body.title, saved.id,
    )
    return {"status": "success", "id": str(saved.id)}


@router.get("/meal-plans/saved")
def list_saved_ai_meal_plans(
    user: Annotated[User, Depends(require_auth)],
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> SavedMealPlanListResponse:
    """Return a paginated list of the user's saved AI meal plans."""
    from sqlalchemy import desc

    q = db.query(SavedMealPlan).filter(SavedMealPlan.user_id == user.id)
    total = q.count()
    items = (
        q.order_by(desc(SavedMealPlan.created_at))
        .limit(limit)
        .offset(offset)
        .all()
    )

    return SavedMealPlanListResponse(
        items=[
            SavedMealPlanOut(
                id=str(s.id),
                title=s.title,
                content=s.content,
                target_calories=s.target_calories,
                protein_g=s.protein_g,
                created_at=s.created_at.isoformat() if s.created_at else "",
            )
            for s in items
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.delete("/meal-plans/saved/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_ai_meal_plan(
    plan_id: str,
    user: Annotated[User, Depends(require_auth)],
    db: Session = Depends(get_db),
) -> None:
    """Delete a saved AI meal plan owned by the authenticated user."""
    from uuid import UUID

    try:
        plan_uuid = UUID(plan_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved plan not found",
        )

    saved = (
        db.query(SavedMealPlan)
        .filter(SavedMealPlan.id == plan_uuid, SavedMealPlan.user_id == user.id)
        .first()
    )
    if saved is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved plan not found",
        )

    db.delete(saved)
    db.commit()
    logger.info("Deleted saved AI plan %s for user %s", plan_id, user.id)
