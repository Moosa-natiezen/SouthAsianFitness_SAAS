"""AI context injection service.

Queries the database for a user's persistent profile, dietary preferences,
and subscription state, then returns a populated
:class:`app.schemas.ai_context.UserAIContext` ready for injection into LLM
system prompts.
"""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.core.logging import get_logger
from app.models.enums import DietaryTagKind, FitnessGoal
from app.models.user import User, UserPreferences, UserProfile
from app.schemas.ai_context import UserAIContext

logger = get_logger(__name__)

# Map the DB FitnessGoal enum onto the friendly goal vocabulary used in
# system prompts (cutting / maintenance / bulking).
_GOAL_LABELS: dict[str, str] = {
    FitnessGoal.WEIGHT_LOSS.value: "cutting",
    FitnessGoal.GENERAL_FITNESS.value: "maintenance",
    FitnessGoal.MUSCLE_BUILDING.value: "bulking",
    FitnessGoal.WEIGHT_GAIN.value: "bulking",
}


def _parse_notes_arrays(prefs: UserPreferences | None) -> tuple[list[str], list[str]]:
    """Extract ``food_dislikes`` / ``preferred_foods`` from preferences notes JSON."""
    if prefs is None or not prefs.notes:
        return [], []

    try:
        notes_data: dict[str, Any] = json.loads(prefs.notes)
    except (json.JSONDecodeError, TypeError):
        return [], []

    dislikes = notes_data.get("food_dislikes", []) or []
    preferred = notes_data.get("preferred_foods", []) or []
    return list(dislikes), list(preferred)


def get_user_ai_context(user_id: UUID | str, db: Session) -> UserAIContext | None:
    """Load the user's persistent AI context from the database.

    Args:
        user_id: UUID of the user to load (a string form is also accepted,
            e.g. when coming from a URL path parameter).
        db: Active SQLAlchemy session.

    Returns:
        A populated :class:`UserAIContext`, or ``None`` if the user (or their
        profile) does not exist.
    """
    if isinstance(user_id, str):
        user_id = UUID(user_id)

    user = (
        db.query(User)
        .options(
            joinedload(User.profile).joinedload(UserProfile.dietary_tags),
            joinedload(User.preferences).joinedload(UserPreferences.dietary_tags),
            joinedload(User.preferences).joinedload(UserPreferences.cuisine_tags),
        )
        .filter(User.id == user_id)
        .first()
    )

    if user is None:
        logger.warning("get_user_ai_context: user %s not found", user_id)
        return None

    profile = user.profile
    prefs = user.preferences

    # ── Dietary preferences & allergies from tags ─────────────────────
    dietary_preferences: list[str] = []
    allergies: list[str] = []

    if profile is not None and profile.dietary_tags:
        for tag in profile.dietary_tags:
            if tag.kind == DietaryTagKind.ALLERGEN:
                allergies.append(tag.slug)
            else:
                dietary_preferences.append(tag.slug)

    if prefs is not None and prefs.dietary_tags:
        for tag in prefs.dietary_tags:
            if tag.kind == DietaryTagKind.ALLERGEN:
                if tag.slug not in allergies:
                    allergies.append(tag.slug)
            elif tag.slug not in dietary_preferences:
                dietary_preferences.append(tag.slug)

    # Always reflect the diet pattern (e.g. vegetarian / vegan).
    if profile is not None and profile.diet_pattern:
        pattern = profile.diet_pattern.value
        if pattern not in dietary_preferences:
            dietary_preferences.append(pattern)

    food_dislikes, preferred_foods = _parse_notes_arrays(prefs)

    cuisine_preferences: list[str] = []
    if prefs is not None and prefs.cuisine_tags:
        cuisine_preferences = [tag.slug for tag in prefs.cuisine_tags]

    current_goal: str | None = None
    if profile is not None and profile.fitness_goal:
        current_goal = _GOAL_LABELS.get(profile.fitness_goal.value)

    context = UserAIContext(
        user_id=user.id,
        target_calories=(
            int(profile.target_calories) if profile and profile.target_calories else None
        ),
        target_protein=(
            float(profile.target_protein_g) if profile and profile.target_protein_g else None
        ),
        dietary_preferences=sorted(dietary_preferences),
        allergies=sorted(allergies),
        food_dislikes=sorted(food_dislikes),
        preferred_foods=sorted(preferred_foods),
        cuisine_preferences=sorted(cuisine_preferences),
        current_goal=current_goal,
        activity_level=(
            profile.activity_level.value if profile and profile.activity_level else None
        ),
        sex=(profile.sex.value if profile and profile.sex else None),
        age_years=(profile.age_years if profile else None),
        height_cm=(profile.height_cm if profile else None),
        weight_kg=(profile.weight_kg if profile else None),
        is_pro=(user.subscription_tier == "pro"),
    )

    logger.debug(
        "AI context loaded for user %s: goal=%s calories=%s protein=%s "
        "prefs=%d allergies=%d",
        user.id,
        context.current_goal,
        context.target_calories,
        context.target_protein,
        len(context.dietary_preferences),
        len(context.allergies),
    )
    return context