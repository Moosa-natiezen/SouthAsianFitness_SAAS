"""Pydantic schemas for progress tracking API."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ProgressEntryCreate(BaseModel):
    """Request to create a progress entry."""

    recorded_on: date = Field(..., description="Date of the measurement")
    weight_kg: Decimal = Field(..., gt=0, description="Body weight in kg")
    waist_cm: Decimal | None = Field(None, ge=0, description="Waist circumference in cm")
    hip_cm: Decimal | None = Field(None, ge=0, description="Hip circumference in cm")
    body_fat_percent: Decimal | None = Field(
        None, ge=0, le=100, description="Body fat percentage"
    )
    notes: str | None = Field(None, max_length=1000, description="Optional notes")


class ProgressEntryResponse(BaseModel):
    """Response for a single progress entry."""

    id: UUID
    recorded_on: date
    weight_kg: Decimal
    waist_cm: Decimal | None
    hip_cm: Decimal | None
    body_fat_percent: Decimal | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProgressSummaryResponse(BaseModel):
    """Calculated progress summary for the authenticated user."""

    starting_weight_kg: Decimal | None = Field(
        None, description="Weight at onboarding"
    )
    current_weight_kg: Decimal | None = Field(
        None, description="Latest recorded weight or profile weight"
    )
    weight_change_kg: Decimal | None = Field(
        None, description="Current minus starting weight"
    )
    bmi: Decimal | None = Field(
        None, description="Body Mass Index (if height is known)"
    )
    fitness_goal: str | None = Field(
        None, description="User's fitness goal from profile"
    )
    entry_count: int = Field(..., description="Total number of progress entries")
    height_cm: Decimal | None = Field(
        None, description="User height from profile (for reference)"
    )
