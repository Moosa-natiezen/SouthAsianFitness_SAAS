"""Settings service layer.

Provides business logic for reading and updating user settings
(profile, preferences) without mutating protected fields like
is_onboarded or is_active.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.currency import Currency
from app.models.enums import DietaryTagKind
from app.models.geography import Country, Region
from app.models.tags import CuisineTag
from app.models.user import User, UserPreferences, UserProfile
from app.services.auth_service import ensure_dietary_tag

logger = get_logger(__name__)


def get_user_settings(db: Session, user: User) -> dict[str, Any]:
    """Return the authenticated user's full settings as a dict.

    Constructs the response from User, UserProfile, and UserPreferences.
    """
    profile = user.profile
    prefs = user.preferences

    # Parse food_dislikes / preferred_foods from JSON notes
    food_dislikes: list[str] = []
    preferred_foods: list[str] = []
    budget_period: str | None = None
    if prefs and prefs.notes:
        try:
            notes_data = json.loads(prefs.notes)
            food_dislikes = notes_data.get("food_dislikes", [])
            preferred_foods = notes_data.get("preferred_foods", [])
            budget_period = notes_data.get("budget_period")
        except (json.JSONDecodeError, TypeError):
            pass

    # Dietary tags from profile (allergens + diet pattern tags)
    profile_dietary_tags: list[str] = []
    if profile and profile.dietary_tags:
        profile_dietary_tags = [tag.slug for tag in profile.dietary_tags]

    # Dietary tags from preferences
    prefs_dietary_tags: list[str] = []
    if prefs and prefs.dietary_tags:
        prefs_dietary_tags = [tag.slug for tag in prefs.dietary_tags]

    # Cuisine tags
    cuisine_tags: list[str] = []
    if prefs and prefs.cuisine_tags:
        cuisine_tags = [tag.slug for tag in prefs.cuisine_tags]

    # Preferred regions
    preferred_region_ids: list[str] = []
    if prefs and prefs.preferred_regions:
        preferred_region_ids = [str(r.id) for r in prefs.preferred_regions]

    settings_data: dict[str, Any] = {
        "display_name": user.display_name,
        "email": user.email,
        "country_id": str(user.country_id) if user.country_id else None,
        "region_id": str(user.region_id) if user.region_id else None,
        "preferred_language": user.preferred_language,
        "preferred_unit_system": (
            user.preferred_unit_system.value if user.preferred_unit_system else None
        ),
        "preferred_currency_code": user.preferred_currency_code,
    }

    if profile:
        settings_data["profile"] = {
            "age_years": profile.age_years,
            "sex": profile.sex.value if profile.sex else None,
            "height_cm": profile.height_cm,
            "weight_kg": profile.weight_kg,
            "activity_level": (
                profile.activity_level.value if profile.activity_level else None
            ),
            "fitness_goal": (
                profile.fitness_goal.value if profile.fitness_goal else None
            ),
            "diet_pattern": (
                profile.diet_pattern.value if profile.diet_pattern else None
            ),
            "dietary_tags": profile_dietary_tags,
        }
    else:
        settings_data["profile"] = None

    settings_data["preferences"] = {
        "weekly_budget_amount": prefs.weekly_budget_amount if prefs else None,
        "budget_currency_code": prefs.budget_currency_code if prefs else None,
        "budget_period": budget_period,
        "dietary_tags": prefs_dietary_tags,
        "cuisine_tags": cuisine_tags,
        "preferred_region_ids": preferred_region_ids,
        "food_dislikes": food_dislikes,
        "preferred_foods": preferred_foods,
    }

    return settings_data


def _validate_country_region(db: Session, country_id: Any, region_id: Any) -> None:
    """Validate that country exists and region belongs to the country."""
    country = db.query(Country).filter(Country.id == country_id).first()
    if country is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid country.",
        )
    if region_id is not None:
        region = (
            db.query(Region)
            .filter(Region.id == region_id, Region.country_id == country.id)
            .first()
        )
        if region is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected region is invalid for the chosen country.",
            )


def update_user_profile(db: Session, user: User, payload: dict[str, Any]) -> None:
    """Update user and UserProfile fields from the profile settings payload.

    Only supplied (non-None) fields are changed. Protected fields
    (is_onboarded, is_active, password, etc.) are never modified.
    """
    # ── User-level fields ────────────────────────────────────────────────
    country_id = payload.get("country_id")
    region_id = payload.get("region_id")

    # Validate country/region if either is being changed
    if country_id is not None or region_id is not None:
        effective_country = country_id if country_id is not None else user.country_id
        effective_region = region_id if "region_id" in payload else user.region_id
        if effective_country is not None:
            _validate_country_region(db, effective_country, effective_region)

    if country_id is not None:
        user.country_id = country_id
    if "region_id" in payload:
        user.region_id = region_id
    if payload.get("preferred_currency_code") is not None:
        # Validate currency exists
        currency = (
            db.query(Currency)
            .filter(
                Currency.code == payload["preferred_currency_code"].upper()
            )
            .first()
        )
        if currency is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid currency code.",
            )
        user.preferred_currency_code = currency.code
    if payload.get("preferred_language") is not None:
        user.preferred_language = payload["preferred_language"][:16]
    if payload.get("preferred_unit_system") is not None:
        user.preferred_unit_system = payload["preferred_unit_system"]
    if payload.get("display_name") is not None:
        user.display_name = payload["display_name"].strip()

    db.flush()

    # ── UserProfile fields ───────────────────────────────────────────────
    profile_fields = [
        "age_years",
        "sex",
        "height_cm",
        "weight_kg",
        "activity_level",
        "fitness_goal",
        "diet_pattern",
    ]
    has_profile_update = any(payload.get(f) is not None for f in profile_fields)

    if has_profile_update:
        profile = user.profile or UserProfile(user_id=user.id)
        if payload.get("age_years") is not None:
            profile.age_years = payload["age_years"]
        if payload.get("sex") is not None:
            profile.sex = payload["sex"]
        if payload.get("height_cm") is not None:
            profile.height_cm = payload["height_cm"]
        if payload.get("weight_kg") is not None:
            profile.weight_kg = payload["weight_kg"]
        if payload.get("activity_level") is not None:
            profile.activity_level = payload["activity_level"]
        if payload.get("fitness_goal") is not None:
            profile.fitness_goal = payload["fitness_goal"]
        if payload.get("diet_pattern") is not None:
            profile.diet_pattern = payload["diet_pattern"]
        db.add(profile)
        db.flush()

    db.commit()
    logger.info("Profile updated for user %s", user.id)


def update_user_preferences(
    db: Session, user: User, payload: dict[str, Any]
) -> None:
    """Update UserPreferences fields from the preferences settings payload.

    Only supplied (non-None) fields are changed. Existing values for
    omitted fields are preserved.
    """
    prefs = user.preferences or UserPreferences(user_id=user.id)

    # ── Scalar fields ────────────────────────────────────────────────────
    if payload.get("weekly_budget_amount") is not None:
        prefs.weekly_budget_amount = payload["weekly_budget_amount"]
    if payload.get("budget_currency_code") is not None:
        # Validate currency
        currency = (
            db.query(Currency)
            .filter(Currency.code == payload["budget_currency_code"].upper())
            .first()
        )
        if currency is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid budget currency code.",
            )
        prefs.budget_currency_code = currency.code

    # ── Notes JSON (food_dislikes, preferred_foods, budget_period) ──────
    # Parse existing notes
    existing_notes: dict[str, Any] = {}
    if prefs.notes:
        try:
            existing_notes = json.loads(prefs.notes)
        except (json.JSONDecodeError, TypeError):
            pass

    if payload.get("budget_period") is not None:
        existing_notes["budget_period"] = payload["budget_period"]
    if payload.get("food_dislikes") is not None:
        existing_notes["food_dislikes"] = payload["food_dislikes"]
    if payload.get("preferred_foods") is not None:
        existing_notes["preferred_foods"] = payload["preferred_foods"]

    if existing_notes:
        prefs.notes = json.dumps(existing_notes, ensure_ascii=False)

    # ── Dietary tags ─────────────────────────────────────────────────────
    if payload.get("dietary_tag_slugs") is not None:
        prefs.dietary_tags = []
        for slug in payload["dietary_tag_slugs"]:
            if not slug:
                continue
            tag = ensure_dietary_tag(db, slug, slug, DietaryTagKind.DIET_PATTERN)
            prefs.dietary_tags.append(tag)

    if payload.get("allergen_tag_slugs") is not None:
        # Merge with existing dietary tags — allergens are separate
        existing_slugs = {t.slug for t in prefs.dietary_tags}
        for slug in payload["allergen_tag_slugs"]:
            if not slug:
                continue
            tag = ensure_dietary_tag(db, slug, slug, DietaryTagKind.ALLERGEN)
            if tag.slug not in existing_slugs:
                prefs.dietary_tags.append(tag)
                existing_slugs.add(tag.slug)

    # ── Cuisine tags ─────────────────────────────────────────────────────
    if payload.get("cuisine_tag_slugs") is not None:
        prefs.cuisine_tags = []
        for slug in payload["cuisine_tag_slugs"]:
            if not slug:
                continue
            normalized = slug.strip().lower().replace(" ", "-")
            tag = (
                db.query(CuisineTag)
                .filter(CuisineTag.slug == normalized)
                .first()
            )
            if tag is None:
                tag = CuisineTag(
                    slug=normalized,
                    name=normalized.replace("-", " ").title(),
                )
                db.add(tag)
                db.flush()
            prefs.cuisine_tags.append(tag)

    # ── Preferred regions ────────────────────────────────────────────────
    if payload.get("preferred_region_ids") is not None:
        prefs.preferred_regions = []
        for rid in payload["preferred_region_ids"]:
            region = db.query(Region).filter(Region.id == rid).first()
            if region is not None:
                prefs.preferred_regions.append(region)

    db.add(prefs)
    db.flush()
    db.commit()
    logger.info("Preferences updated for user %s", user.id)
