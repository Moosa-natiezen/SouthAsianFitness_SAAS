"""Idempotent seed script for reference data required by the onboarding system.

Creates currencies, countries, and regions if they don't already exist.
Safe to run multiple times — detects existing records and skips duplicates.

Usage:
    uv run python -m app.scripts.seed_reference_data
    uv run python app/scripts/seed_reference_data.py
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.currency import Currency
from app.models.enums import UnitSystem
from app.models.geography import Country, Region

# ── Seed data ────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class CurrencySeed:
    code: str
    name: str
    symbol: str
    minor_units: int = 2


CURRENCIES: list[CurrencySeed] = [
    CurrencySeed(code="PKR", name="Pakistani Rupee", symbol="Rs"),
    CurrencySeed(code="INR", name="Indian Rupee", symbol="₹"),
    CurrencySeed(code="BDT", name="Bangladeshi Taka", symbol="৳"),
    CurrencySeed(code="NPR", name="Nepalese Rupee", symbol="₨"),
    CurrencySeed(code="LKR", name="Sri Lankan Rupee", symbol="Rs"),
    CurrencySeed(code="AED", name="United Arab Emirates Dirham", symbol="د.إ"),
]


@dataclass(frozen=True)
class RegionSeed:
    name: str
    code: str


@dataclass(frozen=True)
class CountrySeed:
    name: str
    iso_code: str
    currency_code: str
    regions: tuple[RegionSeed, ...]


COUNTRIES: list[CountrySeed] = [
    CountrySeed(
        name="Pakistan",
        iso_code="PK",
        currency_code="PKR",
        regions=(
            RegionSeed(name="Punjab", code="PK-PB"),
            RegionSeed(name="Sindh", code="PK-SD"),
            RegionSeed(name="Khyber Pakhtunkhwa", code="PK-KP"),
            RegionSeed(name="Balochistan", code="PK-BA"),
            RegionSeed(name="Islamabad Capital Territory", code="PK-IS"),
        ),
    ),
    CountrySeed(
        name="India",
        iso_code="IN",
        currency_code="INR",
        regions=(
            RegionSeed(name="Maharashtra", code="IN-MH"),
            RegionSeed(name="Karnataka", code="IN-KA"),
            RegionSeed(name="Tamil Nadu", code="IN-TN"),
            RegionSeed(name="West Bengal", code="IN-WB"),
            RegionSeed(name="Punjab", code="IN-PB"),
            RegionSeed(name="Uttar Pradesh", code="IN-UP"),
            RegionSeed(name="Gujarat", code="IN-GJ"),
            RegionSeed(name="Rajasthan", code="IN-RJ"),
            RegionSeed(name="Kerala", code="IN-KL"),
            RegionSeed(name="Delhi", code="IN-DL"),
        ),
    ),
    CountrySeed(
        name="Bangladesh",
        iso_code="BD",
        currency_code="BDT",
        regions=(
            RegionSeed(name="Dhaka", code="BD-13"),
            RegionSeed(name="Chittagong", code="BD-11"),
            RegionSeed(name="Rajshahi", code="BD-12"),
            RegionSeed(name="Khulna", code="BD-14"),
            RegionSeed(name="Sylhet", code="BD-10"),
        ),
    ),
    CountrySeed(
        name="Nepal",
        iso_code="NP",
        currency_code="NPR",
        regions=(
            RegionSeed(name="Bagmati", code="NP-03"),
            RegionSeed(name="Lumbini", code="NP-05"),
            RegionSeed(name="Koshi", code="NP-01"),
            RegionSeed(name="Gandaki", code="NP-04"),
            RegionSeed(name="Madhesh", code="NP-02"),
            RegionSeed(name="Karnali", code="NP-06"),
            RegionSeed(name="Sudurpashchim", code="NP-07"),
        ),
    ),
    CountrySeed(
        name="Sri Lanka",
        iso_code="LK",
        currency_code="LKR",
        regions=(
            RegionSeed(name="Western", code="LK-1"),
            RegionSeed(name="Central", code="LK-2"),
            RegionSeed(name="Southern", code="LK-3"),
            RegionSeed(name="Northern", code="LK-4"),
            RegionSeed(name="Eastern", code="LK-5"),
            RegionSeed(name="North Western", code="LK-6"),
            RegionSeed(name="North Central", code="LK-7"),
            RegionSeed(name="Uva", code="LK-8"),
            RegionSeed(name="Sabaragamuwa", code="LK-9"),
        ),
    ),
    CountrySeed(
        name="United Arab Emirates",
        iso_code="AE",
        currency_code="AED",
        regions=(
            RegionSeed(name="Dubai", code="AE-DU"),
            RegionSeed(name="Abu Dhabi", code="AE-AZ"),
            RegionSeed(name="Sharjah", code="AE-SH"),
            RegionSeed(name="Ajman", code="AE-AJ"),
            RegionSeed(name="Ras Al Khaimah", code="AE-RK"),
            RegionSeed(name="Fujairah", code="AE-FU"),
            RegionSeed(name="Umm Al Quwain", code="AE-UQ"),
        ),
    ),
]


# ── Seed functions ───────────────────────────────────────────────────────


@dataclass
class SeedResult:
    currencies_created: int = 0
    countries_created: int = 0
    regions_created: int = 0
    currencies_skipped: int = 0
    countries_skipped: int = 0
    regions_skipped: int = 0


def seed_currencies(db: Session) -> SeedResult:
    """Create missing currencies. Idempotent."""
    result = SeedResult()
    for seed in CURRENCIES:
        existing = db.execute(
            select(Currency).where(Currency.code == seed.code)
        ).scalars().first()
        if existing is not None:
            result.currencies_skipped += 1
            continue
        currency = Currency(
            code=seed.code,
            name=seed.name,
            symbol=seed.symbol,
            minor_units=seed.minor_units,
        )
        db.add(currency)
        result.currencies_created += 1
    db.flush()
    return result


def seed_countries(db: Session) -> SeedResult:
    """Create missing countries. Idempotent — matches on iso_code."""
    result = SeedResult()
    for seed in COUNTRIES:
        existing = db.execute(
            select(Country).where(Country.iso_code == seed.iso_code)
        ).scalars().first()
        if existing is not None:
            result.countries_skipped += 1
            continue
        country = Country(
            name=seed.name,
            iso_code=seed.iso_code,
            currency_code=seed.currency_code,
            default_unit_system=UnitSystem.METRIC,
        )
        db.add(country)
        result.countries_created += 1
    db.flush()
    return result


def seed_regions(db: Session) -> SeedResult:
    """Create missing regions. Idempotent — matches on (country_id, name)."""
    result = SeedResult()
    for country_seed in COUNTRIES:
        country = db.execute(
            select(Country).where(Country.iso_code == country_seed.iso_code)
        ).scalars().first()
        if country is None:
            # Country doesn't exist — skip its regions
            continue
        for region_seed in country_seed.regions:
            existing = db.execute(
                select(Region).where(
                    Region.country_id == country.id,
                    Region.name == region_seed.name,
                )
            ).scalars().first()
            if existing is not None:
                result.regions_skipped += 1
                continue
            region = Region(
                name=region_seed.name,
                code=region_seed.code,
                country_id=country.id,
            )
            db.add(region)
            result.regions_created += 1
    db.flush()
    return result


def seed_all(db: Session, *, commit: bool = True) -> SeedResult:
    """Run all seed operations in order: currencies → countries → regions."""
    total = SeedResult()

    c = seed_currencies(db)
    total.currencies_created += c.currencies_created
    total.currencies_skipped += c.currencies_skipped

    c = seed_countries(db)
    total.countries_created += c.countries_created
    total.countries_skipped += c.countries_skipped

    c = seed_regions(db)
    total.regions_created += c.regions_created
    total.regions_skipped += c.regions_skipped

    if commit:
        db.commit()
    return total


# ── CLI entrypoint ───────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Seed reference data (currencies, countries, regions) for onboarding."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without committing changes",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.dry_run:
            result = seed_all(db, commit=False)
            mode = "dry-run"
        else:
            result = seed_all(db, commit=True)
            mode = "seed"

        print(f"Mode: {mode}")
        print(f"Currencies: {result.currencies_created} created, {result.currencies_skipped} skipped")
        print(f"Countries:  {result.countries_created} created, {result.countries_skipped} skipped")
        print(f"Regions:    {result.regions_created} created, {result.regions_skipped} skipped")
    except (ValueError, OSError) as exc:
        db.rollback()
        print(f"Seed failed: {exc}")
        return 1
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
