"""Meal plan generation API routes.

All endpoints require authentication.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.meal_plan import (
    MealPlanFailureResponse,
    MealPlanGenerateRequest,
    MealPlanResponse,
)
from app.services.meal_plan_service import generate_meal_plan

router = APIRouter(prefix="/meal-plans", tags=["meal-plans"])


def _build_plan_response(result) -> MealPlanResponse | MealPlanFailureResponse:
    """Convert a GenerationResult to the appropriate response."""
    if not result.success or result.failure is not None:
        failure = result.failure
        return MealPlanFailureResponse(
            success=False,
            reason=failure.reason,
            conflict_details=failure.conflict_details,
            suggestions=failure.suggestions,
        )

    plan = result.plan
    from app.schemas.meal_plan import (
        BudgetTargetOut,
        GeneratedDayOut,
        GeneratedFoodOut,
        GeneratedMealOut,
        NutritionTargetOut,
    )

    days = []
    for day in plan.days:
        meals = []
        for meal in day.meals:
            foods = [
                GeneratedFoodOut(
                    food_id=f.food_id,
                    name=f.name,
                    slug=f.slug,
                    serving_quantity=f.serving_quantity,
                    serving_unit_code=f.serving_unit_code,
                    portion_grams=f.portion_grams,
                    calories=f.calories,
                    protein_g=f.protein_g,
                    carbs_g=f.carbs_g,
                    fat_g=f.fat_g,
                    estimated_cost=f.estimated_cost,
                    cost_available=f.cost_available,
                )
                for f in meal.foods
            ]
            meals.append(
                GeneratedMealOut(
                    meal_type=meal.meal_type,
                    foods=foods,
                    subtotal_calories=meal.subtotal_calories,
                    subtotal_protein_g=meal.subtotal_protein_g,
                    subtotal_carbs_g=meal.subtotal_carbs_g,
                    subtotal_fat_g=meal.subtotal_fat_g,
                    subtotal_estimated_cost=meal.subtotal_estimated_cost,
                    cost_complete=meal.cost_complete,
                )
            )
        days.append(
            GeneratedDayOut(
                plan_date=day.plan_date,
                meals=meals,
                total_calories=day.total_calories,
                total_protein_g=day.total_protein_g,
                total_carbs_g=day.total_carbs_g,
                total_fat_g=day.total_fat_g,
                total_estimated_cost=day.total_estimated_cost,
                cost_complete=day.cost_complete,
                warnings=day.warnings,
            )
        )

    return MealPlanResponse(
        plan_id=str(plan.plan_id),
        plan_name=plan.plan_name,
        start_date=plan.start_date,
        end_date=plan.end_date,
        days=days,
        nutrition=NutritionTargetOut(
            calorie_target=plan.nutrition.calorie_target,
            protein_g=plan.nutrition.protein_g,
            carbs_g=plan.nutrition.carbs_g,
            fat_g=plan.nutrition.fat_g,
            goal=plan.nutrition.goal,
            is_bounded=plan.nutrition.is_bounded,
            warnings=plan.nutrition.warnings,
        ),
        budget=BudgetTargetOut(
            daily_budget=plan.budget.daily_budget,
            weekly_budget=plan.budget.weekly_budget,
            monthly_budget=plan.budget.monthly_budget,
            currency_code=plan.budget.currency_code,
        ),
        warnings=plan.warnings,
    )


@router.post(
    "/generate",
    response_model=MealPlanResponse | MealPlanFailureResponse,
)
def generate(
    body: MealPlanGenerateRequest | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate a meal plan for the authenticated user.

    Uses server-side nutrition targets (not client-provided).
    All foods are verified-only. Respects diet pattern, allergies, and dislikes.
    """
    plan_days = body.plan_days if body else None
    meal_count = body.meal_count if body else None

    result = generate_meal_plan(
        db=db,
        user_id=user.id,
        plan_days=plan_days,
        meal_count=meal_count,
    )

    return _build_plan_response(result)
