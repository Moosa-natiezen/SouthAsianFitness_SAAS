"""AI-powered meal plan generation routes.

Provides SSE streaming of AI-generated meal plans via GPT-4o-mini.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.deps import require_pro
from app.core.logging import get_logger
from app.models.user import User
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
