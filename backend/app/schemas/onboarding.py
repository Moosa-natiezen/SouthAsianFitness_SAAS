from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import ActivityLevel, DietPattern, FitnessGoal, Sex, UnitSystem


class OnboardingRequest(BaseModel):
    country_id: UUID
    region_id: UUID | None = None
    preferred_currency_code: str = Field(..., min_length=3, max_length=3)
    preferred_language: str = Field(default="en", min_length=2, max_length=16)
    unit_system: UnitSystem
    age_years: int = Field(..., ge=13, le=120)
    sex: Sex
    height_cm: Decimal = Field(..., gt=0)
    weight_kg: Decimal = Field(..., gt=0)
    activity_level: ActivityLevel
    fitness_goal: FitnessGoal
    diet_pattern: DietPattern = Field(default=DietPattern.OMNIVORE)
    dietary_tag_slugs: list[str] = Field(default_factory=list)
    allergen_tag_slugs: list[str] = Field(default_factory=list)
    food_dislikes: list[str] = Field(default_factory=list)
    preferred_foods: list[str] = Field(default_factory=list)
    weekly_budget_amount: Decimal | None = Field(default=None, ge=0)
    budget_period: str = Field(default="weekly", min_length=2, max_length=32)


class OnboardingResponse(BaseModel):
    status: str = "ok"
    is_onboarded: bool = True
