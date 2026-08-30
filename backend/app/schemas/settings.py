"""Pydantic schemas for Settings API."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import (
    ActivityLevel,
    DietPattern,
    FitnessGoal,
    Sex,
    UnitSystem,
)

# ── Response ─────────────────────────────────────────────────────────────────


class SettingsUserProfile(BaseModel):
    """User profile data returned by GET /api/auth/settings."""

    age_years: int | None = None
    sex: str | None = None
    height_cm: Decimal | None = None
    weight_kg: Decimal | None = None
    activity_level: str | None = None
    fitness_goal: str | None = None
    diet_pattern: str | None = None
    dietary_tags: list[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class SettingsUserPreferences(BaseModel):
    """User preferences data returned by GET /api/auth/settings."""

    weekly_budget_amount: Decimal | None = None
    budget_currency_code: str | None = None
    budget_period: str | None = None
    dietary_tags: list[str] = Field(default_factory=list)
    cuisine_tags: list[str] = Field(default_factory=list)
    preferred_region_ids: list[str] = Field(default_factory=list)
    food_dislikes: list[str] = Field(default_factory=list)
    preferred_foods: list[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class SettingsResponse(BaseModel):
    """Full settings response for the authenticated user."""

    display_name: str
    email: str
    country_id: str | None = None
    region_id: str | None = None
    preferred_language: str = "en"
    preferred_unit_system: str | None = None
    preferred_currency_code: str | None = None
    profile: SettingsUserProfile | None = None
    preferences: SettingsUserPreferences | None = None


# ── Request ──────────────────────────────────────────────────────────────────


class ProfileUpdateRequest(BaseModel):
    """Partial update for user + UserProfile fields."""

    display_name: str | None = Field(None, min_length=2, max_length=150)
    country_id: UUID | None = None
    region_id: UUID | None = None
    preferred_language: str | None = Field(None, min_length=2, max_length=16)
    preferred_unit_system: UnitSystem | None = None
    preferred_currency_code: str | None = Field(None, min_length=3, max_length=3)

    # UserProfile fields
    age_years: int | None = Field(None, ge=13, le=120)
    sex: Sex | None = None
    height_cm: Decimal | None = Field(None, gt=0)
    weight_kg: Decimal | None = Field(None, gt=0)
    activity_level: ActivityLevel | None = None
    fitness_goal: FitnessGoal | None = None
    diet_pattern: DietPattern | None = None


class PreferencesUpdateRequest(BaseModel):
    """Partial update for UserPreferences fields."""

    weekly_budget_amount: Decimal | None = Field(None, ge=0)
    budget_currency_code: str | None = Field(None, min_length=3, max_length=3)
    budget_period: str | None = Field(None, min_length=2, max_length=32)
    dietary_tag_slugs: list[str] | None = None
    allergen_tag_slugs: list[str] | None = None
    cuisine_tag_slugs: list[str] | None = None
    preferred_region_ids: list[UUID] | None = None
    food_dislikes: list[str] | None = None
    preferred_foods: list[str] | None = None
