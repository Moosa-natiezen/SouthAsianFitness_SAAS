"""Pydantic schemas for the Orchestrator chat endpoint."""

from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel, Field


class AgentChatRequest(BaseModel):
    """Request for the Orchestrator chat endpoint.

    Accepts free-form user messages and routes them to the appropriate
    domain worker(s) via the OrchestratorAgent.
    """

    message: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="The user's natural language request",
    )

    # Optional domain-specific overrides
    # These are forwarded to workers when the Orchestrator routes to them.
    target_calories: float | None = Field(
        None, ge=500, le=10000,
        description="Daily calorie target (nutrition domain)",
    )
    protein_g: float | None = Field(
        None, ge=0, le=500,
        description="Daily protein target in grams (nutrition domain)",
    )
    dietary_preferences: list[str] = Field(
        default_factory=list,
        description="Dietary preferences (nutrition domain)",
    )
    allergies: list[str] = Field(
        default_factory=list,
        description="Allergies to exclude (nutrition domain)",
    )
    cuisine_type: str | None = Field(
        None, description="Preferred cuisine type (nutrition domain)",
    )

    # Workout-specific overrides
    goal: str | None = Field(
        None,
        pattern=r"^(strength|hypertrophy|endurance|fat_loss)$",
        description="Training goal (workout domain)",
    )
    experience_level: str | None = Field(
        None,
        pattern=r"^(beginner|intermediate|advanced)$",
        description="Training experience level (workout domain)",
    )
    split: str | None = Field(
        None,
        pattern=r"^(upper_lower|push_pull_legs|full_body)$",
        description="Training split (workout domain)",
    )
    equipment: str | None = Field(
        None,
        pattern=r"^(gym|bodyweight|dumbbells)$",
        description="Available equipment (workout domain)",
    )

    model_config: ClassVar[dict] = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Create a meal plan and workout for me",
                    "target_calories": 2200,
                    "protein_g": 140,
                    "goal": "hypertrophy",
                    "split": "push_pull_legs",
                    "equipment": "gym",
                }
            ]
        }
    }
