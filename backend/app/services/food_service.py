from __future__ import annotations

from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.associations import food_cuisine_tags, food_dietary_tags, food_regions
from app.models.food import Food, FoodPrice
from app.models.tags import FoodCategory
from app.schemas.food import FoodSearchRequest


def _to_uuid(value: str | UUID) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (ValueError, TypeError):
        return None


def get_food_by_id(db: Session, food_id: str | UUID) -> Food | None:
    pk = _to_uuid(food_id)
    if pk is None:
        return None
    return db.get(Food, pk)


def search_foods(db: Session, req: FoodSearchRequest) -> tuple[list[Food], int]:
    q = db.query(Food)

    # Text search on name and description
    if req.q:
        pattern = f"%{req.q.strip().lower()}%"
        q = q.filter(
            func.lower(Food.name).like(pattern) | func.lower(Food.description).like(pattern)
        )

    # Category filter (by ID)
    if req.category_id:
        cat_uuid = _to_uuid(req.category_id)
        if cat_uuid is not None:
            q = q.filter(Food.category_id == cat_uuid)

    # Category filter (by slug)
    if req.category_slug:
        q = q.join(FoodCategory, Food.category_id == FoodCategory.id).filter(
            FoodCategory.slug == req.category_slug
        )

    # Country filter via food_regions association
    if req.country_id:
        country_uuid = _to_uuid(req.country_id)
        if country_uuid is not None:
            q = q.join(food_regions).filter(food_regions.c.country_id == country_uuid)

    # Dietary tag filter
    if req.dietary_tag_slug:
        from app.models.tags import DietaryTag

        q = (
            q.join(food_dietary_tags, Food.id == food_dietary_tags.c.food_id)
            .join(DietaryTag, food_dietary_tags.c.dietary_tag_id == DietaryTag.id)
            .filter(DietaryTag.slug == req.dietary_tag_slug)
        )

    # Cuisine tag filter
    if req.cuisine_tag_slug:
        from app.models.tags import CuisineTag

        q = (
            q.join(food_cuisine_tags, Food.id == food_cuisine_tags.c.food_id)
            .join(CuisineTag, food_cuisine_tags.c.cuisine_tag_id == CuisineTag.id)
            .filter(CuisineTag.slug == req.cuisine_tag_slug)
        )

    # Verification status filter
    if req.verification_status:
        from app.models.enums import VerificationStatus

        try:
            status_enum = VerificationStatus(req.verification_status)
            q = q.filter(Food.verification_status == status_enum)
        except ValueError:
            # Invalid status — return no results
            return [], 0

    # Count before pagination
    total = q.count()

    # Eager-load relationships for serialization (avoids N+1)
    q = (
        q.options(
            joinedload(Food.category),
            joinedload(Food.serving_unit),
            joinedload(Food.dietary_tags),
            joinedload(Food.cuisine_tags),
        )
        .order_by(Food.name)
        .limit(req.limit)
        .offset(req.offset)
        .distinct()
    )

    items = q.all()
    return items, total


def get_food_categories(db: Session) -> list[FoodCategory]:
    """Return all food categories sorted alphabetically by name."""
    return db.query(FoodCategory).order_by(FoodCategory.name).all()


def get_food_prices_for_location(
    db: Session, food_id: str | UUID, country_id: str | None = None, region_id: str | None = None
) -> list[FoodPrice]:
    food_uuid = _to_uuid(food_id)
    if food_uuid is None:
        return []
    q = db.query(FoodPrice).filter(FoodPrice.food_id == food_uuid)
    if country_id:
        c_uuid = _to_uuid(country_id)
        if c_uuid is not None:
            q = q.filter(FoodPrice.country_id == c_uuid)
    if region_id:
        r_uuid = _to_uuid(region_id)
        if r_uuid is not None:
            q = q.filter(FoodPrice.region_id == r_uuid)
    return q.order_by(FoodPrice.observed_at.desc()).limit(50).all()
