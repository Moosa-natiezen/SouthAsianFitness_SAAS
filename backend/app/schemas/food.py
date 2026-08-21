from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class Nutrition(BaseModel):
    calories: float = Field(..., ge=0)
    protein_g: float = Field(..., ge=0)
    carbs_g: float = Field(..., ge=0)
    fat_g: float = Field(..., ge=0)
    fiber_g: float | None = Field(None, ge=0)


class Serving(BaseModel):
    amount: Decimal
    unit_code: str
    grams_equivalent: Decimal | None = None


class ProvenanceOut(BaseModel):
    source_name: str | None = None
    source_identifier: str | None = None
    source_version: str | None = None
    source_date: datetime | None = None
    verification_status: str = "unverified"
    imported_at: datetime | None = None

    model_config = {"from_attributes": True}


class FoodOut(BaseModel):
    id: str
    slug: str
    name: str
    description: str | None
    category: str | None
    is_active: bool
    serving_size: Decimal
    serving_unit: str
    grams_per_serving: Decimal | None
    nutrition: Nutrition
    provenance: ProvenanceOut | None = None

    model_config = {"from_attributes": True}


class FoodListResponse(BaseModel):
    items: list[FoodOut]
    total: int
    limit: int
    offset: int


class FoodSearchRequest(BaseModel):
    q: str | None = Field(None, max_length=120)
    category_id: str | None
    country_id: str | None
    region_id: str | None
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)


class PriceOut(BaseModel):
    amount: Decimal
    currency_code: str
    quantity: Decimal
    unit_code: str
    country_id: str
    region_id: str | None
    observed_at: str

    model_config = {"from_attributes": True}
