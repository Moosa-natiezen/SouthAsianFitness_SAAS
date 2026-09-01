"""Pydantic schemas for nutrition and budget calculation API."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

# ── Request schemas ──────────────────────────────────────────────────────────


class NutritionCalculateRequest(BaseModel):
    """Request to calculate nutrition targets.

    If omitted, values are fetched from the user's profile.
    All fields are optional overrides.
    """

    sex: str | None = Field(
        None,
        pattern=r"^(male|female|other|prefer_not_to_say)$",
        description="User sex for BMR calculation",
    )
    age: int | None = Field(None, ge=14, le=100, description="Age in years")
    height_cm: float | None = Field(None, ge=100, le=250, description="Height in cm")
    weight_kg: float | None = Field(None, ge=30, le=300, description="Weight in kg")
    activity_level: str | None = Field(
        None,
        pattern=r"^(sedentary|lightly_active|moderately_active|very_active|extra_active)$",
        description="Activity level",
    )
    goal: str | None = Field(
        None,
        pattern=r"^(weight_loss|weight_gain|muscle_building|general_fitness)$",
        description="Fitness goal",
    )


class BudgetCalculateRequest(BaseModel):
    """Request to calculate budget targets."""

    weekly_budget_amount: Decimal | None = Field(
        None, ge=0, description="Weekly food budget amount"
    )
    currency_code: str | None = Field(None, max_length=3, description="Currency code (e.g., PKR)")
    country_id: str | None = Field(None, description="Country UUID")
    region_id: str | None = Field(None, description="Region UUID")


# ── Response schemas ─────────────────────────────────────────────────────────


class NutritionTargetResponse(BaseModel):
    """Deterministic nutrition target calculation result."""

    calorie_target: float = Field(..., description="Daily calorie target in kcal")
    protein_g: float = Field(..., description="Daily protein target in grams")
    carbs_g: float = Field(..., description="Daily carbohydrate target in grams")
    fat_g: float = Field(..., description="Daily fat target in grams")
    bmr: float = Field(..., description="Basal Metabolic Rate in kcal")
    tdee: float = Field(..., description="Total Daily Energy Expenditure in kcal")
    goal_adjustment: float = Field(..., description="Calorie adjustment applied for goal")
    is_bounded: bool = Field(
        ..., description="Whether safety bounds were applied"
    )
    warnings: list[str] = Field(
        default_factory=list, description="Explanation of any adjustments or issues"
    )

    # Input echo (for transparency)
    sex: str
    age: int
    height_cm: float
    weight_kg: float
    activity_level: str
    goal: str


class BudgetTargetResponse(BaseModel):
    """Budget calculation result."""

    daily_budget: Decimal | None = Field(None, description="Estimated daily food budget")
    weekly_budget: Decimal | None = Field(None, description="Estimated weekly food budget")
    monthly_budget: Decimal | None = Field(None, description="Estimated monthly food budget")
    currency_code: str | None = Field(None, description="Currency code")
    country_id: str | None = Field(None, description="Country UUID")
    region_id: str | None = Field(None, description="Region UUID")
    warnings: list[str] = Field(
        default_factory=list, description="Any warnings about budget calculation"
    )


class NutritionBudgetResponse(BaseModel):
    """Combined nutrition + budget response."""

    nutrition: NutritionTargetResponse
    budget: BudgetTargetResponse


class MealPlanRequest(BaseModel):
    """Request for AI-generated streaming meal plan."""

    target_calories: float | None = Field(
        None, ge=500, le=10000,
        description="Daily calorie target in kcal",
    )
    protein_g: float | None = Field(
        None, ge=0, le=500,
        description="Daily protein target in grams",
    )
    dietary_preferences: list[str] = Field(
        default_factory=list,
        description="Dietary preferences (e.g., vegetarian, vegan, halal, keto)",
    )
    allergies: list[str] = Field(
        default_factory=list,
        description="Allergies to exclude (e.g., peanuts, shellfish, gluten)",
    )
    cuisine_type: str | None = Field(
        None,
        description="Preferred cuisine type (e.g., South Asian, Mediterranean, East Asian)",
    )


class FoodEligibilityResponse(BaseModel):
    """Food verification eligibility summary."""

    eligible_count: int = Field(..., description="Number of eligible foods")
    total_count: int = Field(..., description="Total foods in database")
    eligible_statuses: list[str] = Field(
        default=["verified", "verified_with_notes"],
        description="Statuses that pass the filter",
    )
