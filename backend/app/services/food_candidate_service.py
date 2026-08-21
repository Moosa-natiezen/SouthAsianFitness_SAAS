"""Food candidate filtering for meal plan generation.

Applies all eligibility rules in sequence:
1. Verification status (verified/verified_with_notes only)
2. Diet pattern restrictions
3. Allergies (dietary tags with kind=ALLERGEN)
4. Dietary restrictions (dietary tags with kind=RESTRICTION)
5. Explicit user dislikes
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.enums import (
    DietaryTagKind,
    DietPattern,
    FoodPreferenceType,
    VerificationStatus,
)
from app.models.food import Food
from app.models.tags import DietaryTag
from app.models.user import UserFoodPreference
from app.services.meal_plan_config import DIET_EXCLUSIONS


@dataclass
class CandidateFood:
    """A food enriched with computed metadata for the optimizer."""

    food_id: UUID
    name: str
    slug: str
    category_name: str | None
    category_slug: str | None

    # Nutrition per serving (as stored in DB, typically per 100g reference)
    calories_per_serving: float
    protein_per_serving: float
    carbs_per_serving: float
    fat_per_serving: float
    fiber_per_serving: float

    # Serving info
    serving_size: float
    grams_per_serving: float
    serving_unit_code: str

    # Preference signal
    is_liked: bool = False
    is_disliked: bool = False


@dataclass
class FilterContext:
    """Context for filtering: user preferences, allergies, restrictions."""

    diet_pattern: DietPattern
    disliked_food_ids: frozenset[UUID] = field(default_factory=frozenset)
    liked_food_ids: frozenset[UUID] = field(default_factory=frozenset)
    allergen_slugs: frozenset[str] = field(default_factory=frozenset)
    restriction_slugs: frozenset[str] = field(default_factory=frozenset)


def build_filter_context(
    db: Session,
    user_id: UUID,
    diet_pattern: DietPattern,
) -> FilterContext:
    """Build a FilterContext from the user's profile and preferences."""
    # Disliked foods
    dislikes = (
        db.query(UserFoodPreference.food_id)
        .filter(
            UserFoodPreference.user_id == user_id,
            UserFoodPreference.preference_type == FoodPreferenceType.DISLIKE,
        )
        .all()
    )
    disliked_ids = frozenset(d[0] for d in dislikes)

    # Liked foods
    likes = (
        db.query(UserFoodPreference.food_id)
        .filter(
            UserFoodPreference.user_id == user_id,
            UserFoodPreference.preference_type == FoodPreferenceType.LIKE,
        )
        .all()
    )
    liked_ids = frozenset(l_[0] for l_ in likes)

    # Allergen slugs (from dietary_tags linked to user profile)
    allergen_slugs = _get_user_tag_slugs(db, user_id, DietaryTagKind.ALLERGEN)
    restriction_slugs = _get_user_tag_slugs(db, user_id, DietaryTagKind.RESTRICTION)

    return FilterContext(
        diet_pattern=diet_pattern,
        disliked_food_ids=disliked_ids,
        liked_food_ids=liked_ids,
        allergen_slugs=allergen_slugs,
        restriction_slugs=restriction_slugs,
    )


def _get_user_tag_slugs(
    db: Session,
    user_id: UUID,
    kind: DietaryTagKind,
) -> frozenset[str]:
    """Get dietary tag slugs of a given kind for a user's profile."""
    from app.models.associations import user_profile_dietary_tags
    from app.models.user import UserProfile

    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if profile is None:
        return frozenset()

    tag_slugs = (
        db.query(DietaryTag.slug)
        .join(user_profile_dietary_tags, DietaryTag.id == user_profile_dietary_tags.c.dietary_tag_id)
        .filter(
            user_profile_dietary_tags.c.user_profile_id == profile.id,
            DietaryTag.kind == kind,
        )
        .all()
    )
    return frozenset(t[0] for t in tag_slugs)


def get_candidate_foods(
    db: Session,
    ctx: FilterContext,
    *,
    limit: int = 500,
) -> list[CandidateFood]:
    """Get all eligible foods filtered by verification, diet, allergies, etc.

    Returns a list of CandidateFood sorted by name for deterministic ordering.
    """
    # Start with verified/active foods
    foods = (
        db.query(Food)
        .filter(
            Food.verification_status.in_({
                VerificationStatus.VERIFIED,
                VerificationStatus.VERIFIED_WITH_NOTES,
            }),
            Food.is_active.is_(True),
        )
        .order_by(Food.name)
        .limit(limit)
        .all()
    )

    candidates = []
    for food in foods:
        # Diet pattern exclusion
        if _violates_diet_pattern(food, ctx.diet_pattern):
            continue

        # Allergen exclusion (conservative: exclude if food has any matching allergen tag)
        if _has_allergen(food, ctx.allergen_slugs):
            continue

        # Dietary restriction exclusion
        if _has_restriction(food, ctx.restriction_slugs):
            continue

        # Dislike exclusion
        if food.id in ctx.disliked_food_ids:
            continue

        # Build candidate
        grams = float(food.grams_per_serving) if food.grams_per_serving else float(food.serving_size)

        cat_name = food.category.name if food.category else None
        cat_slug = food.category.slug if food.category else None

        candidates.append(
            CandidateFood(
                food_id=food.id,
                name=food.name,
                slug=food.slug,
                category_name=cat_name,
                category_slug=cat_slug,
                calories_per_serving=float(food.calories),
                protein_per_serving=float(food.protein_g),
                carbs_per_serving=float(food.carbs_g),
                fat_per_serving=float(food.fat_g),
                fiber_per_serving=float(food.fiber_g) if food.fiber_g else 0.0,
                serving_size=float(food.serving_size),
                grams_per_serving=grams,
                serving_unit_code=food.serving_unit.code if food.serving_unit else "g",
                is_liked=food.id in ctx.liked_food_ids,
                is_disliked=food.id in ctx.disliked_food_ids,
            )
        )

    return candidates


def _violates_diet_pattern(food: Food, pattern: DietPattern) -> bool:
    """Check if a food violates the user's diet pattern."""
    cat_slug = food.category.slug if food.category else ""

    if pattern == DietPattern.VEGAN:
        return cat_slug in DIET_EXCLUSIONS.vegan_exclude_categories
    elif pattern == DietPattern.VEGETARIAN:
        return cat_slug in DIET_EXCLUSIONS.vegetarian_exclude_categories
    elif pattern == DietPattern.EGGETARIAN:
        return cat_slug in DIET_EXCLUSIONS.eggetarian_exclude_categories
    elif pattern == DietPattern.PESCETARIAN:
        return cat_slug in DIET_EXCLUSIONS.pescetarian_exclude_categories

    return False


def _has_allergen(food: Food, allergen_slugs: frozenset[str]) -> bool:
    """Check if a food has a tag matching any of the user's allergens."""
    if not allergen_slugs:
        return False
    for tag in food.dietary_tags:
        if tag.slug in allergen_slugs:
            return True
    return False


def _has_restriction(food: Food, restriction_slugs: frozenset[str]) -> bool:
    """Check if a food has a tag matching any of the user's restrictions."""
    if not restriction_slugs:
        return False
    for tag in food.dietary_tags:
        if tag.slug in restriction_slugs:
            return True
    return False
