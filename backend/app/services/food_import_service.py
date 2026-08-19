from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.currency import Currency
from app.models.enums import UnitDimension, UnitSystem
from app.models.food import Food, FoodIngredient, FoodPrice
from app.models.geography import Country, Region
from app.models.tags import FoodCategory
from app.models.unit import Unit
from app.schemas.food_import import FoodImportRecord, PriceImport

DEFAULT_CURRENCY_MAP = {
    "PKR": ("Pakistani Rupee", "Rs"),
    "INR": ("Indian Rupee", "₹"),
    "BDT": ("Bangladeshi Taka", "৳"),
    "LKR": ("Sri Lankan Rupee", "Rs"),
    "USD": ("US Dollar", "$"),
}

DEFAULT_UNIT_MAP = {
    "g": ("gram", UnitDimension.MASS, Decimal(1)),
    "kg": ("kilogram", UnitDimension.MASS, Decimal(1000)),
    "mg": ("milligram", UnitDimension.MASS, Decimal("0.001")),
    "ml": ("milliliter", UnitDimension.VOLUME, Decimal(1)),
    "l": ("liter", UnitDimension.VOLUME, Decimal(1000)),
    "cup": ("cup", UnitDimension.VOLUME, None),
    "tbsp": ("tablespoon", UnitDimension.VOLUME, None),
    "tsp": ("teaspoon", UnitDimension.VOLUME, None),
    "pc": ("piece", UnitDimension.COUNT, None),
    "piece": ("piece", UnitDimension.COUNT, None),
    "roti": ("roti", UnitDimension.COUNT, None),
    "serving": ("serving", UnitDimension.COUNT, None),
}


class ImportValidationError(ValueError):
    """Raised when a food dataset fails validation."""


@dataclass
class ImportSummary:
    imported: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "imported": self.imported,
            "updated": self.updated,
            "skipped": self.skipped,
            "failed": self.failed,
            "warnings": self.warnings,
        }


def _normalize_slug(value: str) -> str:
    cleaned = value.strip().lower().replace(" ", "-")
    cleaned = "".join(ch for ch in cleaned if ch.isalnum() or ch in {"-", "_"})
    return cleaned.strip("-") or "food"


def _coerce_decimal(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=None)
    if isinstance(value, str):
        normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
        return datetime.fromisoformat(normalized)
    raise TypeError("unsupported datetime value")


def _ensure_currency(db: Session, code: str) -> Currency:
    normalized = code.strip().upper()
    existing = db.get(Currency, normalized)
    if existing is not None:
        return existing
    name, symbol = DEFAULT_CURRENCY_MAP.get(normalized, (normalized, normalized))
    currency = Currency(code=normalized, name=name, symbol=symbol, minor_units=2)
    db.add(currency)
    db.flush()
    return currency


def _ensure_country(db: Session, country_code: str, country_name: str | None = None) -> Country:
    normalized = country_code.strip().upper()
    country = db.execute(select(Country).where(Country.iso_code == normalized)).scalars().first()
    if country is not None:
        return country
    currency = _ensure_currency(db, "PKR")
    country = Country(
        name=country_name or normalized,
        iso_code=normalized,
        currency_code=currency.code,
        default_unit_system=UnitSystem.METRIC,
    )
    db.add(country)
    db.flush()
    return country


def _ensure_region(db: Session, country: Country, region_name: str | None) -> Region | None:
    if region_name is None or not region_name.strip():
        return None
    cleaned = region_name.strip()
    existing = (
        db.execute(
            select(Region).where(Region.country_id == country.id, Region.name == cleaned)
        )
        .scalars()
        .first()
    )
    if existing is not None:
        return existing
    region = Region(name=cleaned, code=_normalize_slug(cleaned), country_id=country.id)
    db.add(region)
    db.flush()
    return region


def _ensure_unit(db: Session, code: str) -> Unit:
    normalized = code.strip().lower()
    existing = db.execute(select(Unit).where(Unit.code == normalized)).scalars().first()
    if existing is not None:
        return existing
    label, dimension, factor = DEFAULT_UNIT_MAP.get(normalized, (normalized, UnitDimension.COUNT, None))
    unit = Unit(code=normalized, name=label, dimension=dimension, to_base_factor=factor)
    db.add(unit)
    db.flush()
    return unit


def _ensure_category(db: Session, category_name: str) -> FoodCategory:
    cleaned = category_name.strip()
    slug = _normalize_slug(cleaned)
    category = db.execute(select(FoodCategory).where(FoodCategory.slug == slug)).scalars().first()
    if category is not None:
        return category
    category = FoodCategory(slug=slug, name=cleaned)
    db.add(category)
    db.flush()
    return category


def _load_dataset(path: str | Path) -> list[dict[str, Any]]:
    file_path = Path(path)
    data = json.loads(file_path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        if "foods" not in data:
            raise ImportValidationError("Dataset must contain a 'foods' list")
        payload = data["foods"]
    elif isinstance(data, list):
        payload = data
    else:
        raise ImportValidationError("Dataset root must be a JSON object or list")

    if not isinstance(payload, list):
        raise ImportValidationError("Dataset foods payload must be a list")
    return payload


def _dataset_to_records(raw_items: list[dict[str, Any]]) -> list[FoodImportRecord]:
    try:
        records = [FoodImportRecord.model_validate(item) for item in raw_items]
    except ValidationError as exc:
        raise ImportValidationError(str(exc)) from exc

    seen_slugs: set[str] = set()
    for record in records:
        slug = _normalize_slug(record.slug)
        if slug in seen_slugs:
            raise ImportValidationError(f"Duplicate slug in dataset: {slug}")
        seen_slugs.add(slug)
    return records


def _upsert_food(db: Session, record: FoodImportRecord) -> tuple[Food, str]:
    normalized_slug = _normalize_slug(record.slug)
    food = db.execute(select(Food).where(Food.slug == normalized_slug)).scalars().first()
    category = _ensure_category(db, record.category)
    serving_unit = _ensure_unit(db, record.serving.unit)

    if food is None:
        food = Food(
            slug=normalized_slug,
            name=record.name,
            description=record.description,
            category_id=category.id,
            serving_size=_coerce_decimal(record.serving.amount),
            serving_unit_id=serving_unit.id,
            grams_per_serving=record.serving.grams_equivalent,
            calories=_coerce_decimal(record.nutrition.calories),
            protein_g=_coerce_decimal(record.nutrition.protein_g),
            carbs_g=_coerce_decimal(record.nutrition.carbs_g),
            fat_g=_coerce_decimal(record.nutrition.fat_g),
            fiber_g=record.nutrition.fiber_g,
            sugar_g=record.nutrition.sugar_g,
            sodium_mg=record.nutrition.sodium_mg,
            is_active=True,
            translations=None,
        )
        db.add(food)
        db.flush()
        return food, "imported"

    food.name = record.name
    food.description = record.description
    food.category_id = category.id
    food.serving_size = _coerce_decimal(record.serving.amount)
    food.serving_unit_id = serving_unit.id
    food.grams_per_serving = record.serving.grams_equivalent
    food.calories = _coerce_decimal(record.nutrition.calories)
    food.protein_g = _coerce_decimal(record.nutrition.protein_g)
    food.carbs_g = _coerce_decimal(record.nutrition.carbs_g)
    food.fat_g = _coerce_decimal(record.nutrition.fat_g)
    food.fiber_g = record.nutrition.fiber_g
    food.sugar_g = record.nutrition.sugar_g
    food.sodium_mg = record.nutrition.sodium_mg
    return food, "updated"


def _upsert_food_price(
    db: Session,
    food: Food,
    pricing: PriceImport,
    region: Region | None,
    country: Country,
) -> None:
    unit = _ensure_unit(db, pricing.unit)

    existing = (
        db.execute(
            select(FoodPrice).where(
                FoodPrice.food_id == food.id,
                FoodPrice.country_id == country.id,
                FoodPrice.region_id == (region.id if region is not None else None),
                FoodPrice.currency_code == pricing.currency.upper(),
                FoodPrice.amount == _coerce_decimal(pricing.amount),
                FoodPrice.quantity == _coerce_decimal(pricing.quantity),
                FoodPrice.unit_id == unit.id,
                FoodPrice.observed_at == _parse_datetime(pricing.observed_at),
            )
        )
        .scalars()
        .first()
    )
    if existing is not None:
        return

    food_price = FoodPrice(
        food_id=food.id,
        country_id=country.id,
        region_id=region.id if region is not None else None,
        amount=_coerce_decimal(pricing.amount),
        currency_code=pricing.currency.upper(),
        quantity=_coerce_decimal(pricing.quantity),
        unit_id=unit.id,
        source="imported",
        observed_at=_parse_datetime(pricing.observed_at),
    )
    db.add(food_price)


def _upsert_ingredients(db: Session, record: FoodImportRecord, parent_food: Food) -> None:
    if not record.ingredients:
        return
    seen_pairs: set[tuple[UUID, UUID]] = set()
    for ingredient_record in record.ingredients:
        ingredient_slug = _normalize_slug(ingredient_record.slug or ingredient_record.name)
        ingredient_food = db.execute(select(Food).where(Food.slug == ingredient_slug)).scalars().first()
        if ingredient_food is None:
            ingredient_food = Food(
                slug=ingredient_slug,
                name=ingredient_record.name,
                description=f"Imported ingredient for {parent_food.name}",
                category_id=None,
                serving_size=_coerce_decimal(ingredient_record.quantity),
                serving_unit_id=_ensure_unit(db, ingredient_record.unit).id,
                grams_per_serving=None,
                calories=Decimal(0),
                protein_g=Decimal(0),
                carbs_g=Decimal(0),
                fat_g=Decimal(0),
                fiber_g=Decimal(0),
                is_active=True,
            )
            db.add(ingredient_food)
            db.flush()

        key = (parent_food.id, ingredient_food.id)
        if key in seen_pairs:
            continue
        seen_pairs.add(key)

        existing = (
            db.execute(
                select(FoodIngredient).where(
                    FoodIngredient.parent_food_id == parent_food.id,
                    FoodIngredient.ingredient_food_id == ingredient_food.id,
                )
            )
            .scalars()
            .first()
        )
        if existing is not None:
            continue

        db.add(
            FoodIngredient(
                parent_food_id=parent_food.id,
                ingredient_food_id=ingredient_food.id,
                quantity=_coerce_decimal(ingredient_record.quantity),
                unit_id=_ensure_unit(db, ingredient_record.unit).id,
                notes=ingredient_record.notes,
            )
        )


def import_food_dataset(db: Session, dataset: list[dict[str, Any]] | dict[str, Any], *, dry_run: bool = False) -> ImportSummary:
    payload = dataset if isinstance(dataset, list) else dataset.get("foods", [])
    try:
        records = _dataset_to_records(payload)
    except ImportValidationError as exc:
        raise ImportValidationError(str(exc)) from exc

    summary = ImportSummary()
    failed_records: list[str] = []

    for record in records:
        try:
            if not record.effective_countries:
                raise ImportValidationError(f"Food '{record.name}' must include at least one country")

            countries = [
                _ensure_country(db, country_code, country_name=None)
                for country_code in record.effective_countries
            ]

            slug = _normalize_slug(record.slug)
            existing = db.execute(select(Food).where(Food.slug == slug)).scalars().first()
            if existing is not None:
                summary.skipped += 1
                continue

            food, action = _upsert_food(db, record)
            if action == "updated":
                summary.updated += 1
            else:
                summary.imported += 1

            if record.effective_regions:
                region_objects = []
                for country in countries:
                    for region_name in record.effective_regions:
                        region = _ensure_region(db, country, region_name)
                        if region is not None:
                            region_objects.append(region)
                if region_objects:
                    food.regions = list(dict.fromkeys(region_objects))

            for country in countries:
                for price in record.prices:
                    price_country = _ensure_country(db, price.country)
                    price_region = _ensure_region(db, price_country, price.region) if price.region else None
                    _upsert_food_price(db, food, price, price_region, price_country)

            _upsert_ingredients(db, record, food)
            db.flush()
        except (ImportValidationError, ValueError, TypeError, IntegrityError) as exc:
            failed_records.append(f"{record.name}: {exc}")
            summary.failed += 1

    if failed_records:
        db.rollback()
        raise ImportValidationError("; ".join(failed_records))

    if dry_run:
        db.rollback()
        return summary

    db.commit()
    return summary


def import_foods_from_file(db: Session, path: str | Path, *, dry_run: bool = False) -> ImportSummary:
    raw_data = _load_dataset(path)
    return import_food_dataset(db, raw_data, dry_run=dry_run)
