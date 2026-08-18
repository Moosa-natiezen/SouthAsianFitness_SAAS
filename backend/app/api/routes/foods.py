from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.food import (
    FoodListResponse,
    FoodOut,
    FoodSearchRequest,
    Nutrition,
    PriceOut,
)
from app.services.food_service import (
    get_food_by_id,
    get_food_prices_for_location,
    search_foods,
)

router = APIRouter(prefix="/foods", tags=["foods"])


@router.get("/", response_model=FoodListResponse)
def list_foods(
    q: str | None = Query(None, max_length=120),
    category_id: str | None = Query(None),
    country_id: str | None = Query(None),
    region_id: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    req = FoodSearchRequest(
        q=q,
        category_id=category_id,
        country_id=country_id,
        region_id=region_id,
        limit=limit,
        offset=offset,
    )
    items, total = search_foods(db, req)

    def serialize_food(f):
        return {
            "id": str(f.id),
            "slug": f.slug,
            "name": f.name,
            "description": f.description,
            "category": f.category.name if f.category else None,
            "is_active": bool(f.is_active),
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
            },
        }

    return FoodListResponse(
        items=[serialize_food(i) for i in items], total=total, limit=limit, offset=offset
    )


@router.get("/{food_id}", response_model=FoodOut)
def get_food(food_id: str, db: Session = Depends(get_db)):
    food = get_food_by_id(db, food_id)
    if not food:
        raise HTTPException(status_code=404, detail="Food not found")
    return {
        "id": str(food.id),
        "slug": food.slug,
        "name": food.name,
        "description": food.description,
        "category": food.category.name if food.category else None,
        "is_active": bool(food.is_active),
        "serving_size": food.serving_size,
        "serving_unit": food.serving_unit.code
        if getattr(food, "serving_unit", None) is not None
        else None,
        "grams_per_serving": food.grams_per_serving,
        "nutrition": {
            "calories": food.calories,
            "protein_g": food.protein_g,
            "carbs_g": food.carbs_g,
            "fat_g": food.fat_g,
            "fiber_g": food.fiber_g,
        },
    }


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
