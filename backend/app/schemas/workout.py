"""Pydantic schemas for AI workout generation and saved workout plans."""

from __future__ import annotations

from pydantic import BaseModel, Field


class WorkoutGenerateRequest(BaseModel):
    """Request for AI-generated streaming workout plan."""

    goal: str = Field(
        ...,
        pattern=r"^(strength|hypertrophy|endurance|fat_loss)$",
        description="Fitness goal: strength, hypertrophy, endurance, or fat_loss",
    )
    experience_level: str = Field(
        default="intermediate",
        pattern=r"^(beginner|intermediate|advanced)$",
        description="Training experience level",
    )
    split: str = Field(
        default="push_pull_legs",
        pattern=r"^(upper_lower|push_pull_legs|full_body)$",
        description="Training split type",
    )
    equipment: str = Field(
        default="gym",
        pattern=r"^(gym|bodyweight|dumbbells)$",
        description="Available equipment",
    )


class SaveWorkoutPlanRequest(BaseModel):
    """Request to save a generated workout plan."""

    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    goal: str | None = Field(None, max_length=50)
    split: str | None = Field(None, max_length=50)
    equipment: str | None = Field(None, max_length=50)


class SavedWorkoutPlanOut(BaseModel):
    """Serialized saved workout plan for list view."""

    id: str
    title: str
    content: str
    goal: str | None = None
    split: str | None = None
    equipment: str | None = None
    created_at: str


class SavedWorkoutPlanListResponse(BaseModel):
    """Paginated list of saved workout plans."""

    items: list[SavedWorkoutPlanOut]
    total: int
    limit: int
    offset: int
