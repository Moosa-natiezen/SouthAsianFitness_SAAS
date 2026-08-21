"""Nutrition and budget calculation API routes.

All endpoints require authentication.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.food import Food
from app.models.user import User
from app.schemas.nutrition import (
    BudgetTargetResponse,
    FoodEligibilityResponse,
    NutritionBudgetResponse,
    NutritionCalculateRequest,
    NutritionTargetResponse,
)
from app.services.budget_service import calculate_budget_targets
from app.services.food_filter_service import count_eligible_foods
from app.services.nutrition_service import calculate_nutrition_targets

router = APIRouter(prefix="/nutrition", tags=["nutrition"])


def _get_profile_data(user: User) -> dict:
    """Extract profile data from user model."""
    profile = user.profile
    if profile is None:
        return {}
    return {
        "sex": profile.sex.value if profile.sex else None,
        "age": profile.age_years,
        "height_cm": float(profile.height_cm) if profile.height_cm else None,
        "weight_kg": float(profile.weight_kg) if profile.weight_kg else None,
        "activity_level": profile.activity_level.value if profile.activity_level else None,
        "goal": profile.fitness_goal.value if profile.fitness_goal else None,
    }


def _get_budget_data(user: User) -> dict:
    """Extract budget data from user preferences."""
    prefs = user.preferences
    if prefs is None:
        return {}
    return {
        "weekly_budget_amount": prefs.weekly_budget_amount,
        "currency_code": prefs.budget_currency_code,
        "country_id": user.country_id,
        "region_id": user.region_id,
    }


@router.post("/calculate", response_model=NutritionBudgetResponse)
def calculate_targets(
    body: NutritionCalculateRequest | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Calculate nutrition targets and budget for the authenticated user.

    All fields in the request body are optional overrides.
    If omitted, values are fetched from the user's profile.
    """
    # Merge profile data with request overrides
    profile_data = _get_profile_data(user)

    sex = (body.sex if body and body.sex else profile_data.get("sex")) or "other"
    age = (body.age if body and body.age is not None else profile_data.get("age"))
    height_cm = (body.height_cm if body and body.height_cm is not None else profile_data.get("height_cm"))
    weight_kg = (body.weight_kg if body and body.weight_kg is not None else profile_data.get("weight_kg"))
    activity_level = (body.activity_level if body and body.activity_level else profile_data.get("activity_level")) or "sedentary"
    goal = (body.goal if body and body.goal else profile_data.get("goal")) or "general_fitness"

    # Validate required fields
    if age is None or height_cm is None or weight_kg is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User profile is incomplete. Please complete onboarding first, "
            "or provide age, height_cm, and weight_kg in the request body.",
        )

    # Calculate nutrition targets
    nutrition = calculate_nutrition_targets(
        sex=sex,
        age=int(age),
        height_cm=float(height_cm),
        weight_kg=float(weight_kg),
        activity_level=activity_level,
        goal=goal,
    )

    # Calculate budget targets
    budget_data = _get_budget_data(user)
    budget = calculate_budget_targets(
        weekly_budget_amount=budget_data.get("weekly_budget_amount"),
        currency_code=budget_data.get("currency_code"),
        country_id=budget_data.get("country_id"),
        region_id=budget_data.get("region_id"),
    )

    return NutritionBudgetResponse(
        nutrition=NutritionTargetResponse(
            calorie_target=nutrition.calorie_target,
            protein_g=nutrition.protein_g,
            carbs_g=nutrition.carbs_g,
            fat_g=nutrition.fat_g,
            bmr=nutrition.bmr,
            tdee=nutrition.tdee,
            goal_adjustment=nutrition.goal_adjustment,
            is_bounded=nutrition.is_bounded,
            warnings=nutrition.warnings,
            sex=nutrition.sex,
            age=nutrition.age,
            height_cm=nutrition.height_cm,
            weight_kg=nutrition.weight_kg,
            activity_level=nutrition.activity_level,
            goal=nutrition.goal,
        ),
        budget=BudgetTargetResponse(
            daily_budget=budget.daily_budget,
            weekly_budget=budget.weekly_budget,
            monthly_budget=budget.monthly_budget,
            currency_code=budget.currency_code,
            country_id=budget.country_id,
            region_id=budget.region_id,
            warnings=budget.warnings,
        ),
    )


@router.get("/targets", response_model=NutritionTargetResponse)
def get_nutrition_targets(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get nutrition targets for the authenticated user using their profile."""
    profile_data = _get_profile_data(user)

    if not all([profile_data.get("age"), profile_data.get("height_cm"), profile_data.get("weight_kg")]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User profile is incomplete. Please complete onboarding first.",
        )

    nutrition = calculate_nutrition_targets(
        sex=profile_data.get("sex", "other"),
        age=int(profile_data["age"]),
        height_cm=float(profile_data["height_cm"]),
        weight_kg=float(profile_data["weight_kg"]),
        activity_level=profile_data.get("activity_level", "sedentary"),
        goal=profile_data.get("goal", "general_fitness"),
    )

    return NutritionTargetResponse(
        calorie_target=nutrition.calorie_target,
        protein_g=nutrition.protein_g,
        carbs_g=nutrition.carbs_g,
        fat_g=nutrition.fat_g,
        bmr=nutrition.bmr,
        tdee=nutrition.tdee,
        goal_adjustment=nutrition.goal_adjustment,
        is_bounded=nutrition.is_bounded,
        warnings=nutrition.warnings,
        sex=nutrition.sex,
        age=nutrition.age,
        height_cm=nutrition.height_cm,
        weight_kg=nutrition.weight_kg,
        activity_level=nutrition.activity_level,
        goal=nutrition.goal,
    )


@router.get("/budget", response_model=BudgetTargetResponse)
def get_budget_targets(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get budget targets for the authenticated user."""
    budget_data = _get_budget_data(user)
    budget = calculate_budget_targets(
        weekly_budget_amount=budget_data.get("weekly_budget_amount"),
        currency_code=budget_data.get("currency_code"),
        country_id=budget_data.get("country_id"),
        region_id=budget_data.get("region_id"),
    )
    return BudgetTargetResponse(
        daily_budget=budget.daily_budget,
        weekly_budget=budget.weekly_budget,
        monthly_budget=budget.monthly_budget,
        currency_code=budget.currency_code,
        country_id=budget.country_id,
        region_id=budget.region_id,
        warnings=budget.warnings,
    )


@router.get("/eligible-foods", response_model=FoodEligibilityResponse)
def get_eligible_foods_summary(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a summary of foods eligible for calculations (verified only)."""
    eligible = count_eligible_foods(db)
    total = db.query(func.count()).select_from(Food).scalar() or 0

    return FoodEligibilityResponse(
        eligible_count=eligible,
        total_count=total,
    )
