from __future__ import annotations

from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.associations import food_regions
from app.models.food import Food, FoodPrice
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

    if req.q:
        pattern = f"%{req.q.strip().lower()}%"
        q = q.filter(
            func.lower(Food.name).like(pattern) | func.lower(Food.description).like(pattern)
        )

    if req.category_id:
        cat_uuid = _to_uuid(req.category_id)
        if cat_uuid is not None:
            q = q.filter(Food.category_id == cat_uuid)

    if req.country_id:
        country_uuid = _to_uuid(req.country_id)
        if country_uuid is not None:
            # join regions association to filter foods relevant to a country via regions table
            q = q.join(food_regions).filter(food_regions.c.country_id == country_uuid)

    total = q.count()
    items = q.order_by(Food.name).limit(req.limit).offset(req.offset).all()
    return items, total


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
