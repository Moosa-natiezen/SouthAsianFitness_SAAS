"""Tests for the reference data seed script.

Verifies idempotent creation of currencies, countries, and regions.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.db.base import Base
from app.models.currency import Currency
from app.models.food import Food
from app.models.geography import Country, Region
from app.models.unit import Unit
from app.scripts.seed_reference_data import (
    COUNTRIES,
    CURRENCIES,
    seed_all,
    seed_countries,
    seed_currencies,
    seed_regions,
)
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker

# ── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture()
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Patch JSONB → JSON for SQLite compatibility
    from sqlalchemy import JSON
    from sqlalchemy.dialects.postgresql import JSONB

    for table in Base.metadata.tables.values():
        for col in table.columns:
            if isinstance(col.type, JSONB):
                col.type = JSON()

    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)
    session = TestSession()
    yield session
    session.close()
    engine.dispose()


# ── Currency seeding ─────────────────────────────────────────────────────


class TestCurrencySeed:
    def test_creates_all_currencies(self, db_session: Session):
        result = seed_currencies(db_session)
        assert result.currencies_created == len(CURRENCIES)
        assert result.currencies_skipped == 0

        for seed in CURRENCIES:
            currency = db_session.get(Currency, seed.code)
            assert currency is not None
            assert currency.name == seed.name
            assert currency.symbol == seed.symbol

    def test_idempotent第二次_does_not_duplicate(self, db_session: Session):
        first = seed_currencies(db_session)
        db_session.commit()
        second = seed_currencies(db_session)
        db_session.commit()

        assert first.currencies_created == len(CURRENCIES)
        assert second.currencies_created == 0
        assert second.currencies_skipped == len(CURRENCIES)


# ── Country seeding ──────────────────────────────────────────────────────


class TestCountrySeed:
    def test_creates_all_countries(self, db_session: Session):
        seed_currencies(db_session)
        result = seed_countries(db_session)
        db_session.commit()

        assert result.countries_created == len(COUNTRIES)
        assert result.countries_skipped == 0

        for seed in COUNTRIES:
            country = db_session.execute(
                select(Country).where(Country.iso_code == seed.iso_code)
            ).scalars().first()
            assert country is not None, f"Country {seed.iso_code} not found"
            assert country.name == seed.name
            assert country.currency_code == seed.currency_code

    def test_uses_correct_names_not_iso_codes(self, db_session: Session):
        seed_currencies(db_session)
        seed_countries(db_session)
        db_session.commit()

        for seed in COUNTRIES:
            country = db_session.execute(
                select(Country).where(Country.iso_code == seed.iso_code)
            ).scalars().first()
            # Must NOT use ISO code as name
            assert country.name != seed.iso_code, (
                f"Country {seed.iso_code} has ISO code as name: {country.name}"
            )

    def test_correct_currencies_per_country(self, db_session: Session):
        seed_currencies(db_session)
        seed_countries(db_session)
        db_session.commit()

        expected = {"PK": "PKR", "IN": "INR", "BD": "BDT", "NP": "NPR", "LK": "LKR", "AE": "AED"}
        for iso, currency_code in expected.items():
            country = db_session.execute(
                select(Country).where(Country.iso_code == iso)
            ).scalars().first()
            assert country is not None
            assert country.currency_code == currency_code, (
                f"{iso} should use {currency_code}, got {country.currency_code}"
            )

    def test_uae_is_included(self, db_session: Session):
        seed_currencies(db_session)
        seed_countries(db_session)
        db_session.commit()

        uae = db_session.execute(
            select(Country).where(Country.iso_code == "AE")
        ).scalars().first()
        assert uae is not None
        assert uae.name == "United Arab Emirates"
        assert uae.currency_code == "AED"

    def test_idempotent第二次_does_not_duplicate(self, db_session: Session):
        seed_currencies(db_session)
        first = seed_countries(db_session)
        db_session.commit()
        second = seed_countries(db_session)
        db_session.commit()

        assert first.countries_created == len(COUNTRIES)
        assert second.countries_created == 0
        assert second.countries_skipped == len(COUNTRIES)


# ── Region seeding ───────────────────────────────────────────────────────


class TestRegionSeed:
    def test_creates_regions_for_all_countries(self, db_session: Session):
        seed_currencies(db_session)
        seed_countries(db_session)
        result = seed_regions(db_session)
        db_session.commit()

        total_regions = sum(len(c.regions) for c in COUNTRIES)
        assert result.regions_created == total_regions
        assert result.regions_skipped == 0

    def test_regions_linked_to_correct_countries(self, db_session: Session):
        seed_currencies(db_session)
        seed_countries(db_session)
        seed_regions(db_session)
        db_session.commit()

        for country_seed in COUNTRIES:
            country = db_session.execute(
                select(Country).where(Country.iso_code == country_seed.iso_code)
            ).scalars().first()
            regions = db_session.execute(
                select(Region).where(Region.country_id == country.id)
            ).scalars().all()
            region_names = {r.name for r in regions}
            expected_names = {r.name for r in country_seed.regions}
            assert region_names == expected_names, (
                f"{country_seed.iso_code}: expected {expected_names}, got {region_names}"
            )

    def test_region_codes_are_populated(self, db_session: Session):
        seed_currencies(db_session)
        seed_countries(db_session)
        seed_regions(db_session)
        db_session.commit()

        for country_seed in COUNTRIES:
            for region_seed in country_seed.regions:
                country = db_session.execute(
                    select(Country).where(Country.iso_code == country_seed.iso_code)
                ).scalars().first()
                region = db_session.execute(
                    select(Region).where(
                        Region.country_id == country.id,
                        Region.name == region_seed.name,
                    )
                ).scalars().first()
                assert region is not None
                assert region.code == region_seed.code, (
                    f"Region {region_seed.name} code: expected {region_seed.code}, got {region.code}"
                )

    def test_idempotent第二次_does_not_duplicate(self, db_session: Session):
        seed_currencies(db_session)
        seed_countries(db_session)
        first = seed_regions(db_session)
        db_session.commit()
        second = seed_regions(db_session)
        db_session.commit()

        total_regions = sum(len(c.regions) for c in COUNTRIES)
        assert first.regions_created == total_regions
        assert second.regions_created == 0
        assert second.regions_skipped == total_regions


# ── Full seed ────────────────────────────────────────────────────────────


class TestSeedAll:
    def test_full_seed_creates_everything(self, db_session: Session):
        result = seed_all(db_session)

        assert result.currencies_created == len(CURRENCIES)
        assert result.countries_created == len(COUNTRIES)
        total_regions = sum(len(c.regions) for c in COUNTRIES)
        assert result.regions_created == total_regions

    def test_full_seed_is_idempotent(self, db_session: Session):
        first = seed_all(db_session)
        second = seed_all(db_session)

        assert first.currencies_created > 0
        assert first.countries_created > 0
        assert first.regions_created > 0

        assert second.currencies_created == 0
        assert second.countries_created == 0
        assert second.regions_created == 0

    def test_seed_does_not_break_food_import_schema(self, db_session: Session):
        """After seeding, we can still create food-related records."""
        seed_all(db_session)

        # Create a unit (needed for food)
        unit = Unit(code="g", name="Gram", dimension="mass", to_base_factor=Decimal("1.0"))
        db_session.add(unit)
        db_session.flush()

        # Get the seeded Pakistan country
        pk = db_session.execute(
            select(Country).where(Country.iso_code == "PK")
        ).scalars().first()
        assert pk is not None

        # Create a food referencing the seeded country's currency
        food = Food(
            slug="test-food",
            name="Test Food",
            serving_size=Decimal(100),
            serving_unit_id=unit.id,
            grams_per_serving=Decimal(100),
            calories=Decimal(100),
            protein_g=Decimal(5),
            carbs_g=Decimal(15),
            fat_g=Decimal(3),
        )
        db_session.add(food)
        db_session.commit()

        assert food.id is not None



