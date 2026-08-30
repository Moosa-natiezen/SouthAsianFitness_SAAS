from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.food import (
    CategoryOut,
    FoodListResponse,
    FoodOut,
    FoodSearchRequest,
    Nutrition,
    PriceOut,
)
from app.services.food_service import (
    get_food_by_id,
    get_food_categories,
    get_food_prices_for_location,
    search_foods,
)

router = APIRouter(prefix="/foods", tags=["foods"])


def _serialize_food(f) -> dict:
    """Serialize a Food ORM object to a FoodOut-compatible dict."""
    return {
        "id": str(f.id),
        "slug": f.slug,
        "name": f.name,
        "description": f.description,
        "category": f.category.name if f.category else None,
        "category_slug": f.category.slug if f.category else None,
        "is_active": bool(f.is_active),
        "verification_status": f.verification_status.value
        if f.verification_status is not None
        else "unverified",
        "serving_size": f.serving_size,
        "serving_unit": f.serving_unit.code
        if getattr(f, "serving_unit", None) is not None
        else None,
        "grams_per_serving": f.grams_per_serving,
        "nutrition": {
            "calories": f.calories,
            "protein_g": f.protein_g,
            "carbs_g": f.carbs_g,
            "fat_g": f.fat_g,
            "fiber_g": f.fiber_g,
            "sugar_g": f.sugar_g,
            "sodium_mg": f.sodium_mg,
        },
        "dietary_tags": [tag.slug for tag in f.dietary_tags] if f.dietary_tags else [],
        "cuisine_tags": [tag.slug for tag in f.cuisine_tags] if f.cuisine_tags else [],
    }


@router.get("/", response_model=FoodListResponse)
def list_foods(
    q: str | None = Query(None, max_length=120),
    category_id: str | None = Query(None),
    category_slug: str | None = Query(None),
    country_id: str | None = Query(None),
    region_id: str | None = Query(None),
    dietary_tag_slug: str | None = Query(None),
    cuisine_tag_slug: str | None = Query(None),
    verification_status: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    req = FoodSearchRequest(
        q=q,
        category_id=category_id,
        category_slug=category_slug,
        country_id=country_id,
        region_id=region_id,
        dietary_tag_slug=dietary_tag_slug,
        cuisine_tag_slug=cuisine_tag_slug,
        verification_status=verification_status,
        limit=limit,
        offset=offset,
    )
    items, total = search_foods(db, req)

    return FoodListResponse(
        items=[_serialize_food(i) for i in items], total=total, limit=limit, offset=offset
    )


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    """Return all food categories sorted alphabetically by name."""
    categories = get_food_categories(db)
    return [
        CategoryOut(id=str(c.id), name=c.name, slug=c.slug)
        for c in categories
    ]


@router.get("/{food_id}", response_model=FoodOut)
def get_food(food_id: str, db: Session = Depends(get_db)):
    food = get_food_by_id(db, food_id)
    if not food:
        raise HTTPException(status_code=404, detail="Food not found")
    # Eager-load relationships for serialization
    from sqlalchemy.orm import joinedload

    db.expire(food)
    food = (
        db.query(type(food))
        .options(
            joinedload(type(food).category),
            joinedload(type(food).serving_unit),
            joinedload(type(food).dietary_tags),
            joinedload(type(food).cuisine_tags),
        )
        .filter(type(food).id == food.id)
        .first()
    )
    return _serialize_food(food)


@router.get("/{food_id}/nutrition", response_model=Nutrition)
def get_nutrition(food_id: str, db: Session = Depends(get_db)):
    food = get_food_by_id(db, food_id)
    if not food:
        raise HTTPException(status_code=404, detail="Food not found")
    return Nutrition(
        calories=float(food.calories),
        protein_g=float(food.protein_g),
        carbs_g=float(food.carbs_g),
        fat_g=float(food.fat_g),
        fiber_g=float(food.fiber_g) if food.fiber_g is not None else None,
        sugar_g=float(food.sugar_g) if food.sugar_g is not None else None,
        sodium_mg=float(food.sodium_mg) if food.sodium_mg is not None else None,
    )


@router.get("/{food_id}/prices", response_model=list[PriceOut])
def food_prices(
    food_id: str,
    country_id: str | None = Query(None),
    region_id: str | None = Query(None),
    db: Session = Depends(get_db),
):
    prices = get_food_prices_for_location(db, food_id, country_id, region_id)

    def serialize_price(p):
        return {
            "amount": p.amount,
            "currency_code": p.currency_code,
            "quantity": p.quantity,
            "unit_code": p.unit.code if getattr(p, "unit", None) is not None else None,
            "country_id": str(p.country_id),
            "region_id": str(p.region_id) if p.region_id else None,
            "observed_at": p.observed_at.isoformat() if p.observed_at is not None else None,
        }

    return [serialize_price(p) for p in prices]
