"""Tests for the reference data seed script.

Verifies idempotent creation of currencies, countries, and regions
from worldwide ISO 3166 / ISO 4217 data via pycountry.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.db.base import Base
from app.models.food import Food
from app.models.geography import Country, Region
from app.models.unit import Unit
from app.scripts.seed_reference_data import (
    COUNTRY_CURRENCY_MAP,
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
        expected_count = len(set(COUNTRY_CURRENCY_MAP.values()))
        result = seed_currencies(db_session)
        assert result.currencies_created == expected_count
        assert result.currencies_skipped == 0

    def test_idempotent_does_not_duplicate(self, db_session: Session):
        expected_count = len(set(COUNTRY_CURRENCY_MAP.values()))
        first = seed_currencies(db_session)
        db_session.commit()
        second = seed_currencies(db_session)
        db_session.commit()

        assert first.currencies_created == expected_count
        assert second.currencies_created == 0
        assert second.currencies_skipped == expected_count


# ── Country seeding ──────────────────────────────────────────────────────


class TestCountrySeed:
    def test_creates_all_countries(self, db_session: Session):
        seed_currencies(db_session)
        db_session.commit()
        result = seed_countries(db_session)
        db_session.commit()

        assert result.countries_created == len(COUNTRY_CURRENCY_MAP)
        assert result.countries_skipped == 0

        for iso_code, currency_code in COUNTRY_CURRENCY_MAP.items():
            country = db_session.execute(
                select(Country).where(Country.iso_code == iso_code)
            ).scalars().first()
            assert country is not None, f"Country {iso_code} not found"
            assert country.currency_code == currency_code

    def test_uses_correct_names_not_iso_codes(self, db_session: Session):
        seed_currencies(db_session)
        seed_countries(db_session)
        db_session.commit()

        for iso_code in COUNTRY_CURRENCY_MAP:
            country = db_session.execute(
                select(Country).where(Country.iso_code == iso_code)
            ).scalars().first()
            # Must NOT use ISO code as name
            assert country.name != iso_code, (
                f"Country {iso_code} has ISO code as name: {country.name}"
            )

    def test_south_asian_countries_present(self, db_session: Session):
        seed_currencies(db_session)
        seed_countries(db_session)
        db_session.commit()

        expected = {"PK": "PKR", "IN": "INR", "BD": "BDT", "NP": "NPR", "LK": "LKR", "AE": "AED"}
        for iso, currency_code in expected.items():
            country = db_session.execute(
                select(Country).where(Country.iso_code == iso)
            ).scalars().first()
            assert country is not None, f"South Asian country {iso} missing"
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
        assert "Arab Emirates" in uae.name
        assert uae.currency_code == "AED"

    def test_idempotent_does_not_duplicate(self, db_session: Session):
        seed_currencies(db_session)
        first = seed_countries(db_session)
        db_session.commit()
        second = seed_countries(db_session)
        db_session.commit()

        assert first.countries_created == len(COUNTRY_CURRENCY_MAP)
        assert second.countries_created == 0
        assert second.countries_skipped == len(COUNTRY_CURRENCY_MAP)


# ── Region seeding ───────────────────────────────────────────────────────


class TestRegionSeed:
    def test_creates_regions(self, db_session: Session):
        seed_currencies(db_session)
        seed_countries(db_session)
        result = seed_regions(db_session)
        db_session.commit()

        assert result.regions_created > 0
        assert result.regions_skipped == 0

    def test_regions_linked_to_correct_countries(self, db_session: Session):
        seed_currencies(db_session)
        seed_countries(db_session)
        seed_regions(db_session)
        db_session.commit()

        # Check India has regions
        india = db_session.execute(
            select(Country).where(Country.iso_code == "IN")
        ).scalars().first()
        assert india is not None
        india_regions = db_session.execute(
            select(Region).where(Region.country_id == india.id)
        ).scalars().all()
        assert len(india_regions) > 10, f"India should have many states, got {len(india_regions)}"

        # Check US has regions
        us = db_session.execute(
            select(Country).where(Country.iso_code == "US")
        ).scalars().first()
        assert us is not None
        us_regions = db_session.execute(
            select(Region).where(Region.country_id == us.id)
        ).scalars().all()
        assert len(us_regions) > 40, f"US should have 50+ states, got {len(us_regions)}"

    def test_region_codes_are_populated(self, db_session: Session):
        seed_currencies(db_session)
        seed_countries(db_session)
        seed_regions(db_session)
        db_session.commit()

        # Spot-check a few regions have ISO 3166-2 codes
        india = db_session.execute(
            select(Country).where(Country.iso_code == "IN")
        ).scalars().first()
        regions = db_session.execute(
            select(Region).where(Region.country_id == india.id)
        ).scalars().all()
        for region in regions:
            assert region.code and region.code.startswith("IN-"), (
                f"Region {region.name} should have IN-* code, got {region.code}"
            )

    def test_pakistan_has_all_provinces(self, db_session: Session):
        seed_currencies(db_session)
        seed_countries(db_session)
        seed_regions(db_session)
        db_session.commit()

        pk = db_session.execute(
            select(Country).where(Country.iso_code == "PK")
        ).scalars().first()
        assert pk is not None
        pk_regions = db_session.execute(
            select(Region).where(Region.country_id == pk.id)
        ).scalars().all()
        names = {r.name for r in pk_regions}
        # Pakistan should have at least its 4 provinces + territories
        assert len(names) >= 4, f"Pakistan should have 4+ regions, got {len(names)}: {names}"

    def test_idempotent_does_not_duplicate(self, db_session: Session):
        seed_currencies(db_session)
        seed_countries(db_session)
        first = seed_regions(db_session)
        db_session.commit()
        second = seed_regions(db_session)
        db_session.commit()

        assert first.regions_created > 0
        assert second.regions_created == 0
        assert second.regions_skipped == first.regions_created


# ── Full seed ────────────────────────────────────────────────────────────


class TestSeedAll:
    def test_full_seed_creates_everything(self, db_session: Session):
        result = seed_all(db_session)

        assert result.currencies_created > 0
        assert result.countries_created == len(COUNTRY_CURRENCY_MAP)
        assert result.regions_created > 0

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

    def test_unique_iso_codes(self, db_session: Session):
        """All countries must have unique ISO codes."""
        seed_all(db_session)

        countries = db_session.execute(select(Country)).scalars().all()
        iso_codes = [c.iso_code for c in countries]
        assert len(iso_codes) == len(set(iso_codes)), "Duplicate ISO codes found"

    def test_currency_countries_shared(self, db_session: Session):
        """Countries sharing a currency must reference the same Currency record."""
        seed_all(db_session)

        # Germany and France both use EUR
        de = db_session.execute(
            select(Country).where(Country.iso_code == "DE")
        ).scalars().first()
        fr = db_session.execute(
            select(Country).where(Country.iso_code == "FR")
        ).scalars().first()
        assert de is not None, "Germany should be seeded"
        assert fr is not None, "France should be seeded"
        assert de.currency_code == fr.currency_code == "EUR"

    def test_minimum_country_count(self, db_session: Session):
        """We should have at least 200 countries worldwide."""
        result = seed_all(db_session)
        total = result.countries_created + result.countries_skipped
        assert total >= 200, f"Expected 200+ countries, got {total}"
