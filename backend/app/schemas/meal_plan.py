"""Pydantic schemas for meal plan generation API."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

# ── Request schemas ──────────────────────────────────────────────────────────


class MealPlanGenerateRequest(BaseModel):
    """Request to generate a new meal plan."""

    plan_days: int | None = Field(
        None, ge=1, le=30,
        description="Number of days (1-30). Default: 1",
    )
    meal_count: int | None = Field(
        None, ge=1, le=6,
        description="Number of meals per day (1-6). Default: 4",
    )


# ── Response sub-schemas ─────────────────────────────────────────────────────


class GeneratedFoodOut(BaseModel):
    """A single food in a generated meal."""

    food_id: str
    name: str
    slug: str
    serving_quantity: float
    serving_unit_code: str
    portion_grams: float
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    estimated_cost: Decimal | None = None
    cost_available: bool


class GeneratedMealOut(BaseModel):
    """A single meal in a generated plan."""

    meal_type: str
    foods: list[GeneratedFoodOut]
    subtotal_calories: float
    subtotal_protein_g: float
    subtotal_carbs_g: float
    subtotal_fat_g: float
    subtotal_estimated_cost: Decimal | None = None
    cost_complete: bool


class GeneratedDayOut(BaseModel):
    """A single day in a generated plan."""

    plan_date: date
    meals: list[GeneratedMealOut]
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    total_estimated_cost: Decimal | None = None
    cost_complete: bool
    warnings: list[str] = Field(default_factory=list)


class NutritionTargetOut(BaseModel):
    """Nutrition targets used for the plan."""

    calorie_target: float
    protein_g: float
    carbs_g: float
    fat_g: float
    goal: str
    is_bounded: bool
    warnings: list[str] = Field(default_factory=list)


class BudgetTargetOut(BaseModel):
    """Budget targets used for the plan."""

    daily_budget: Decimal | None = None
    weekly_budget: Decimal | None = None
    monthly_budget: Decimal | None = None
    currency_code: str | None = None


class MealPlanResponse(BaseModel):
    """Full meal plan generation response."""

    plan_id: str
    plan_name: str
    start_date: date
    end_date: date
    days: list[GeneratedDayOut]
    nutrition: NutritionTargetOut
    budget: BudgetTargetOut
    warnings: list[str] = Field(default_factory=list)


class MealPlanFailureResponse(BaseModel):
    """Structured failure when no valid plan can be generated."""

    success: bool = False
    reason: str
    conflict_details: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


# ── List / summary schemas ─────────────────────────────────────────────────


class MealPlanSummaryOut(BaseModel):
    """Lightweight representation of a meal plan for the list view."""

    id: str
    name: str | None
    start_date: date
    end_date: date
    day_count: int
    status: str
    calorie_target: float | None
    created_at: str


class MealPlanListResponse(BaseModel):
    """Paginated list of meal plan summaries."""

    items: list[MealPlanSummaryOut]
    total: int
    limit: int
    offset: int
