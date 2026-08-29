from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class NutritionImport(BaseModel):
    calories: Decimal = Field(..., ge=0, le=100000)
    protein_g: Decimal = Field(..., ge=0, le=100000)
    carbs_g: Decimal = Field(..., ge=0, le=100000)
    fat_g: Decimal = Field(..., ge=0, le=100000)
    fiber_g: Decimal | None = Field(default=None, ge=0, le=100000)
    sugar_g: Decimal | None = Field(default=None, ge=0, le=100000)
    sodium_mg: Decimal | None = Field(default=None, ge=0, le=100000)


class ServingImport(BaseModel):
    amount: Decimal = Field(..., gt=0, le=100000)
    unit: str = Field(..., min_length=1, max_length=32)
    grams_equivalent: Decimal | None = Field(default=None, ge=0, le=100000)


class IngredientImport(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    slug: str | None = Field(default=None, max_length=200)
    quantity: Decimal = Field(..., gt=0, le=100000)
    unit: str = Field(..., min_length=1, max_length=32)
    notes: str | None = Field(default=None, max_length=255)


class PriceImport(BaseModel):
    country: str = Field(..., min_length=2, max_length=3)
    region: str | None = Field(default=None, max_length=120)
    currency: str = Field(..., min_length=3, max_length=3)
    amount: Decimal = Field(..., ge=0, le=1000000)
    quantity: Decimal = Field(..., gt=0, le=100000)
    unit: str = Field(..., min_length=1, max_length=32)
    observed_at: datetime | str = Field(...)

    @field_validator("country")
    @classmethod
    def normalize_country(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.strip().upper()


class SourceProvenanceImport(BaseModel):
    """Provenance metadata linking a food record to its data source."""

    source_name: str = Field(..., min_length=1, max_length=150)
    source_identifier: str | None = Field(default=None, max_length=255)
    source_version: str | None = Field(default=None, max_length=64)
    source_date: str | None = Field(default=None, max_length=32)
    verification_status: str = Field(
        default="unverified",
        pattern=r"^(unverified|pending_review|verified|verified_with_notes|conflict|retracted)$",
    )
    notes: str | None = Field(default=None, max_length=1000)


class FoodImportRecord(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    food_type: str = Field(default="ingredient", pattern=r"^(ingredient|composite)$")
    category: str = Field(..., min_length=1, max_length=100)
    country: str | None = Field(default=None, min_length=2, max_length=3)
    countries: list[str] = Field(default_factory=list)
    region: str | None = Field(default=None, max_length=120)
    regions: list[str] = Field(default_factory=list)
    nutrition: NutritionImport
    serving: ServingImport
    ingredients: list[IngredientImport] = Field(default_factory=list)
    prices: list[PriceImport] = Field(default_factory=list)
    source: SourceProvenanceImport | None = Field(default=None)

    @field_validator("country", "region")
    @classmethod
    def clean_optional_string(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip()

    @field_validator("countries", "regions")
    @classmethod
    def validate_location_lists(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for item in value:
            if item is None:
                continue
            text = str(item).strip()
            if text:
                cleaned.append(text)
        return cleaned

    @property
    def effective_countries(self) -> list[str]:
        values = []
        if self.country:
            values.append(self.country)
        values.extend(self.countries)
        return list(dict.fromkeys(values))

    @property
    def effective_regions(self) -> list[str]:
        values = []
        if self.region:
            values.append(self.region)
        values.extend(self.regions)
        return list(dict.fromkeys(values))


class DatasetSourceMeta(BaseModel):
    """Top-level source metadata for an entire dataset file."""

    name: str = Field(..., min_length=1, max_length=150)
    version: str | None = Field(default=None, max_length=64)
    reference_url: str | None = Field(default=None, max_length=2000)
    license_category: str = Field(
        default="unknown",
        pattern=r"^(public_domain|cc0|cc_by|cc_by_sa|open_data|proprietary_allow_redist|proprietary_no_redist|unknown)$",
    )
    attribution_text: str | None = Field(default=None, max_length=2000)
    can_store_raw_data: bool = Field(default=False)
    can_store_derived_values: bool = Field(default=True)
    source_date: str | None = Field(default=None, max_length=32)
    description: str | None = Field(default=None, max_length=2000)


class DatasetEnvelope(BaseModel):
    foods: list[FoodImportRecord]
    dataset_source: DatasetSourceMeta | None = Field(default=None)

    @field_validator("foods")
    @classmethod
    def ensure_non_empty(cls, value: list[FoodImportRecord]) -> list[FoodImportRecord]:
        if not value:
            raise ValueError("foods list cannot be empty")
        return value
