from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.currency import Currency
from app.models.enums import FoodSourceLicense, UnitDimension, UnitSystem, VerificationStatus
from app.models.food import Food, FoodIngredient, FoodPrice
from app.models.food_source import FoodSource
from app.models.geography import Country, Region
from app.models.tags import FoodCategory
from app.models.unit import Unit
from app.schemas.food_import import (
    DatasetSourceMeta,
    FoodImportRecord,
    PriceImport,
    SourceProvenanceImport,
)

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


# Canonical country name lookup — prevents ISO codes from being used as names.
_COUNTRY_NAMES: dict[str, str] = {
    "PK": "Pakistan",
    "IN": "India",
    "BD": "Bangladesh",
    "NP": "Nepal",
    "LK": "Sri Lanka",
    "AE": "United Arab Emirates",
}

# Canonical currency per country — prevents defaulting everything to PKR.
_COUNTRY_CURRENCIES: dict[str, str] = {
    "PK": "PKR",
    "IN": "INR",
    "BD": "BDT",
    "NP": "NPR",
    "LK": "LKR",
    "AE": "AED",
}


def _ensure_country(db: Session, country_code: str, country_name: str | None = None) -> Country:
    normalized = country_code.strip().upper()
    # Always look up by natural key first (idempotent).
    country = db.execute(select(Country).where(Country.iso_code == normalized)).scalars().first()
    if country is not None:
        return country
    # Resolve currency from canonical mapping, fall back to PKR.
    currency_code = _COUNTRY_CURRENCIES.get(normalized, "PKR")
    currency = _ensure_currency(db, currency_code)
    # Use provided name, canonical lookup, or fall back to ISO code.
    name = country_name or _COUNTRY_NAMES.get(normalized, normalized)
    country = Country(
        name=name,
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
    # Always look up by natural key first (idempotent).
    existing = (
        db.execute(
            select(Region).where(Region.country_id == country.id, Region.name == cleaned)
        )
        .scalars()
        .first()
    )
    if existing is not None:
        return existing
    # Only create a region if it doesn't already exist — prefer seeded data.
    # Use a stable slug-based code for food-imported regions.
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


def _ensure_food_source(
    db: Session,
    source_meta: SourceProvenanceImport | DatasetSourceMeta,
) -> FoodSource:
    """Get or create a FoodSource record from import metadata."""
    # SourceProvenanceImport uses 'source_name', DatasetSourceMeta uses 'name'
    name = getattr(source_meta, "source_name", None) or getattr(source_meta, "name", "unknown")
    name = name.strip()
    # SourceProvenanceImport uses 'source_version', DatasetSourceMeta uses 'version'
    raw_version = getattr(source_meta, "source_version", None) or getattr(source_meta, "version", None)
    version = raw_version.strip() if raw_version else "1.0"

    existing = (
        db.execute(
            select(FoodSource).where(FoodSource.name == name, FoodSource.version == version)
        )
        .scalars()
        .first()
    )
    if existing is not None:
        return existing

    license_cat = FoodSourceLicense.UNKNOWN
    if hasattr(source_meta, "license_category"):
        try:
            license_cat = FoodSourceLicense(source_meta.license_category)
        except ValueError:
            license_cat = FoodSourceLicense.UNKNOWN

    can_raw = getattr(source_meta, "can_store_raw_data", False)
    can_derived = getattr(source_meta, "can_store_derived_values", True)
    ref_url = getattr(source_meta, "reference_url", None)
    attr_text = getattr(source_meta, "attribution_text", None)
    desc = getattr(source_meta, "description", None)
    src_date = None
    raw_date = getattr(source_meta, "source_date", None)
    if raw_date:
        try:
            src_date = datetime.fromisoformat(str(raw_date))
        except (ValueError, TypeError):
            src_date = None

    source = FoodSource(
        name=name,
        version=version,
        reference_url=ref_url,
        license_category=license_cat,
        attribution_text=attr_text,
        can_store_raw_data=can_raw,
        can_store_derived_values=can_derived,
        description=desc,
        source_date=src_date,
        imported_at=datetime.now(tz=UTC),
    )
    db.add(source)
    db.flush()
    return source


def _upsert_food(
    db: Session,
    record: FoodImportRecord,
    source: FoodSource | None = None,
) -> tuple[Food, str]:
    normalized_slug = _normalize_slug(record.slug)
    food = db.execute(select(Food).where(Food.slug == normalized_slug)).scalars().first()
    category = _ensure_category(db, record.category)
    serving_unit = _ensure_unit(db, record.serving.unit)

    # Determine source and verification from per-record or dataset-level metadata
    food_source_id = None
    source_identifier = None
    source_version = None
    source_date = None
    verification = VerificationStatus.UNVERIFIED
    now = datetime.now(tz=UTC)

    if record.source is not None:
        per_source = _ensure_food_source(db, record.source)
        food_source_id = per_source.id
        source_identifier = record.source.source_identifier
        source_version = record.source.source_version
        try:
            verification = VerificationStatus(record.source.verification_status)
        except ValueError:
            verification = VerificationStatus.UNVERIFIED
        if record.source.source_date:
            try:
                source_date = datetime.fromisoformat(record.source.source_date)
            except (ValueError, TypeError):
                source_date = None
    elif source is not None:
        food_source_id = source.id
        source_version = source.version
        source_date = source.source_date

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
            food_source_id=food_source_id,
            source_identifier=source_identifier,
            source_version=source_version,
            source_date=source_date,
            imported_at=now,
            verification_status=verification,
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
    if food_source_id is not None:
        food.food_source_id = food_source_id
        food.source_identifier = source_identifier
        food.source_version = source_version
        food.source_date = source_date
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
    # Support both raw list and envelope with dataset_source metadata
    if isinstance(dataset, list):
        payload = dataset
        dataset_source: DatasetSourceMeta | None = None
    else:
        payload = dataset.get("foods", [])
        raw_meta = dataset.get("dataset_source")
        dataset_source = DatasetSourceMeta.model_validate(raw_meta) if raw_meta else None

    try:
        records = _dataset_to_records(payload)
    except ImportValidationError as exc:
        raise ImportValidationError(str(exc)) from exc

    # Resolve dataset-level source if present
    dataset_source_obj: FoodSource | None = None
    if dataset_source is not None:
        dataset_source_obj = _ensure_food_source(db, dataset_source)

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

            food, action = _upsert_food(db, record, source=dataset_source_obj)
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
