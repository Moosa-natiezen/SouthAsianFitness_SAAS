from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-1234567890abcdefg")
os.environ.setdefault("CSRF_SECRET_KEY", "test-csrf-secret-key-1234567890abcdef")
os.environ.setdefault("ENVIRONMENT", "testing")

from datetime import UTC, datetime

from app import models as app_models  # noqa: F401
from app.db.base import Base
from app.main import app
from app.models.currency import Currency
from app.models.enums import UnitDimension, UnitSystem
from app.models.geography import Country, Region
from app.models.tags import FoodCategory
from app.models.unit import Unit
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


def reset_db() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    # update the app's db session to use this in-memory engine
    from app.core.config import settings
    from app.db import session as db_session

    db_session.engine = engine
    db_session.SessionLocal = sessionmaker(
        bind=engine, autocommit=False, autoflush=False, class_=Session
    )
    settings.database_url = str(engine.url)


def make_client() -> TestClient:
    reset_db()
    return TestClient(app)


def seed_basics(db: Session):
    # Ensure schema exists on the current connection (tests may run with isolated in-memory engines)
    from app.db.base import Base

    bind = db.get_bind()
    from sqlalchemy import inspect

    inspector = inspect(bind)
    if not inspector.has_table("currencies"):
        Base.metadata.create_all(bind=bind)

    # add currency, country, region, units, category
    currency = Currency(code="PKR", name="Pakistani Rupee", symbol="Rs", minor_units=2)
    db.add(currency)
    country = Country(
        name="Pakistan", iso_code="PK", currency_code="PKR", default_unit_system=UnitSystem.METRIC
    )
    db.add(country)
    db.flush()
    region = Region(name="Punjab", country_id=country.id)
    db.add(region)
    unit_g = Unit(code="g", name="gram", dimension=UnitDimension.MASS, to_base_factor=1)
    unit_piece = Unit(code="pc", name="piece", dimension=UnitDimension.COUNT, to_base_factor=None)
    db.add_all([unit_g, unit_piece])
    category = FoodCategory(name="grains", slug="grains")
    db.add(category)
    db.commit()
    return {
        "currency": currency,
        "country": country,
        "region": region,
        "unit_g": unit_g,
        "unit_piece": unit_piece,
        "category": category,
    }


def test_create_and_list_foods():
    client = make_client()
    # seed
    from app.db import session as db_session

    db = db_session.SessionLocal()
    basics = seed_basics(db)

    # create sample food via direct DB insertion
    from app.models.food import Food, FoodPrice

    rice = Food(
        slug="basmati-rice",
        name="Basmati rice",
        description="Long grain rice",
        category_id=basics["category"].id,
        serving_size=100,
        serving_unit_id=basics["unit_g"].id,
        grams_per_serving=100,
        calories=130,
        protein_g=2.5,
        carbs_g=28,
        fat_g=0.4,
        is_active=True,
    )
    db.add(rice)
    db.flush()

    # add price
    price = FoodPrice(
        food_id=rice.id,
        country_id=basics["country"].id,
        region_id=basics["region"].id,
        amount=200,
        currency_code="PKR",
        quantity=1,
        unit_id=basics["unit_g"].id,
        observed_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    db.add(price)
    db.commit()

    # list foods
    resp = client.get("/api/foods")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Basmati rice"

    # get by id
    resp = client.get(f"/api/foods/{rice.id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Basmati rice"

    # nutrition
    resp = client.get(f"/api/foods/{rice.id}/nutrition")
    assert resp.status_code == 200
    assert resp.json()["calories"] == 130

    # prices
    resp = client.get(f"/api/foods/{rice.id}/prices?country_id={basics['country'].id}")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    db.close()
