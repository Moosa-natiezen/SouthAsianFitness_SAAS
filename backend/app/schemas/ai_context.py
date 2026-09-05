"""Pydantic schemas for AI context management.

The :class:`UserAIContext` model captures the persistent facts an AI agent
needs to personalise meal-plan / workout generation — the user's physical
targets, dietary preferences, allergies, and current goal.  It is populated
from the database by :func:`app.services.ai_context_service.get_user_ai_context`
and rendered into the LLM system prompt by :meth:`UserAIContext.format_for_prompt`.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class UserAIContext(BaseModel):
    """Persistent user context injected into AI system prompts.

    Attributes:
        user_id: The user this context belongs to.
        target_calories: Daily calorie target (kcal), if calculated.
        target_protein: Daily protein target (g), if calculated.
        dietary_preferences: Dietary patterns / restrictions (e.g. "halal",
            "vegetarian", "vegan").
        allergies: Allergens to strictly exclude (e.g. "peanuts", "dairy").
        food_dislikes: Foods the user dislikes and wants avoided.
        preferred_foods: Foods the user explicitly enjoys.
        cuisine_preferences: Preferred cuisine tags (e.g. "north-indian",
            "punjabi").
        current_goal: The user's current fitness goal (e.g. "cutting",
            "maintenance", "bulking").
        activity_level: Activity level label (e.g. "moderately_active").
        sex: Biological sex used for TDEE math ("male"/"female"/...).
        age_years: User's age in years.
        height_cm: User's height in centimetres.
        weight_kg: User's weight in kilograms.
        is_pro: Whether the user holds a Pro subscription.
    """

    user_id: UUID
    target_calories: int | None = None
    target_protein: float | None = None
    dietary_preferences: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    food_dislikes: list[str] = Field(default_factory=list)
    preferred_foods: list[str] = Field(default_factory=list)
    cuisine_preferences: list[str] = Field(default_factory=list)
    current_goal: str | None = None
    activity_level: str | None = None
    sex: str | None = None
    age_years: int | None = None
    height_cm: Decimal | None = None
    weight_kg: Decimal | None = None
    is_pro: bool = False

    def format_for_prompt(self) -> str:
        """Render this context as a text block for an LLM system prompt.

        Produces a compact, natural-language summary such as:

            You are helping a user who is cutting at 2000 calories/day,
            eating a halal vegetarian diet, allergic to peanuts.
        """
        lines: list[str] = []

        # Goal + calorie/protein targets (the headline sentence).
        headline: list[str] = []
        if self.current_goal:
            headline.append(f"whose current goal is {self.current_goal}")
        if self.target_calories is not None:
            headline.append(f"targeting {self.target_calories} calories/day")
        if self.target_protein is not None:
            headline.append(f"{self.target_protein:g}g protein/day")

        if headline:
            lines.append("You are helping a user " + ", ".join(headline) + ".")

        # Dietary preferences.
        if self.dietary_preferences:
            lines.append(
                f"- Dietary preferences: {', '.join(sorted(self.dietary_preferences))}"
            )

        # Allergies — never suggest these.
        if self.allergies:
            lines.append(
                f"- Allergies / strict exclusions (NEVER suggest): "
                f"{', '.join(sorted(self.allergies))}"
            )

        if self.food_dislikes:
            lines.append(
                f"- Disliked foods (avoid unless requested): "
                f"{', '.join(sorted(self.food_dislikes))}"
            )

        if self.preferred_foods:
            lines.append(
                f"- Preferred foods (prioritise these): "
                f"{', '.join(sorted(self.preferred_foods))}"
            )

        if self.cuisine_preferences:
            lines.append(
                f"- Preferred cuisines: {', '.join(sorted(self.cuisine_preferences))}"
            )

        # Physical profile (used to sanity-check portion sizing).
        profile_bits: list[str] = []
        if self.age_years is not None:
            profile_bits.append(f"{self.age_years} years old")
        if self.sex:
            profile_bits.append(self.sex)
        if self.height_cm is not None:
            profile_bits.append(f"{self.height_cm:g} cm tall")
        if self.weight_kg is not None:
            profile_bits.append(f"{self.weight_kg:g} kg")
        if self.activity_level:
            profile_bits.append(f"{self.activity_level} activity level")

        if profile_bits:
            lines.append(f"- User profile: {', '.join(profile_bits)}.")

        if self.is_pro:
            lines.append("- Subscription: Pro member (full feature access).")

        return "\n".join(lines)