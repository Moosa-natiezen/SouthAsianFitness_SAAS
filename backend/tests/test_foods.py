"""Tests for Food Library API endpoints.

Covers:
- GET /api/foods/ — list/search foods
- GET /api/foods/categories — list categories
- GET /api/foods/{food_id} — get single food
- GET /api/foods/{food_id}/nutrition — get nutrition
- GET /api/foods/{food_id}/prices — get prices
- New: sugar_g, sodium_mg, verification_status, category_slug, dietary_tags, cuisine_tags
- New: category_slug filter, verification_status filter
"""

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
from app.models.enums import DietaryTagKind, UnitDimension, UnitSystem, VerificationStatus
from app.models.food import Food, FoodPrice
from app.models.geography import Country, Region
from app.models.tags import CuisineTag, DietaryTag, FoodCategory
from app.models.unit import Unit
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# ── Helpers ───────────────────────────────────────────────────────────────


def reset_db() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
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
    bind = db.get_bind()
    from sqlalchemy import inspect

    inspector = inspect(bind)
    if not inspector.has_table("currencies"):
        Base.metadata.create_all(bind=bind)

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
    category = FoodCategory(name="Grains", slug="grains")
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


def create_food(
    db: Session,
    *,
    slug: str = "basmati-rice",
    name: str = "Basmati rice",
    description: str = "Long grain rice",
    category=None,
    serving_unit=None,
    verification_status: VerificationStatus = VerificationStatus.VERIFIED,
    sugar_g=None,
    sodium_mg=None,
    is_active: bool = True,
) -> Food:
    cat = category or FoodCategory.query.first()
    unit = serving_unit or Unit.query.first()
    food = Food(
        slug=slug,
        name=name,
        description=description,
        category_id=cat.id if cat else None,
        serving_size=100,
        serving_unit_id=unit.id if unit else None,
        grams_per_serving=100,
        calories=130,
        protein_g=2.5,
        carbs_g=28,
        fat_g=0.4,
        fiber_g=1.2,
        sugar_g=sugar_g,
        sodium_mg=sodium_mg,
        is_active=is_active,
        verification_status=verification_status,
    )
    db.add(food)
    db.flush()
    return food


# ── Basic CRUD tests ─────────────────────────────────────────────────────


def test_create_and_list_foods():
    client = make_client()
    from app.db import session as db_session

    db = db_session.SessionLocal()
    basics = seed_basics(db)

    rice = create_food(
        db,
        slug="basmati-rice",
        name="Basmati rice",
        category=basics["category"],
        serving_unit=basics["unit_g"],
    )

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


# ── Extended serialization tests ──────────────────────────────────────────


def test_food_serialization_includes_new_fields():
    """Verify sugar_g, sodium_mg, verification_status, category_slug are serialized."""
    client = make_client()
    from app.db import session as db_session

    db = db_session.SessionLocal()
    basics = seed_basics(db)

    food = create_food(
        db,
        slug="test-food",
        name="Test Food",
        category=basics["category"],
        serving_unit=basics["unit_g"],
        sugar_g=5.5,
        sodium_mg=120.0,
        verification_status=VerificationStatus.VERIFIED,
    )
    db.commit()

    # Check list endpoint serialization
    resp = client.get("/api/foods")
    assert resp.status_code == 200
    item = resp.json()["items"][0]
    assert item["verification_status"] == "verified"
    assert item["category_slug"] == "grains"
    assert item["nutrition"]["sugar_g"] == 5.5
    assert item["nutrition"]["sodium_mg"] == 120.0
    assert isinstance(item["dietary_tags"], list)
    assert isinstance(item["cuisine_tags"], list)

    # Check single food endpoint serialization
    resp = client.get(f"/api/foods/{food.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["verification_status"] == "verified"
    assert data["category_slug"] == "grains"
    assert data["nutrition"]["sugar_g"] == 5.5
    assert data["nutrition"]["sodium_mg"] == 120.0

    db.close()


def test_food_with_tags_serialized():
    """Verify dietary and cuisine tags are returned in the food serialization."""
    client = make_client()
    from app.db import session as db_session

    db = db_session.SessionLocal()
    basics = seed_basics(db)

    # Create tags
    dietary = DietaryTag(slug="nuts", name="Nuts", kind=DietaryTagKind.ALLERGEN)
    cuisine = CuisineTag(slug="pakistani", name="Pakistani")
    db.add_all([dietary, cuisine])
    db.flush()

    food = create_food(
        db,
        slug="tagged-food",
        name="Tagged Food",
        category=basics["category"],
        serving_unit=basics["unit_g"],
    )
    food.dietary_tags.append(dietary)
    food.cuisine_tags.append(cuisine)
    db.commit()

    resp = client.get(f"/api/foods/{food.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert "nuts" in data["dietary_tags"]
    assert "pakistani" in data["cuisine_tags"]

    db.close()


# ── Categories endpoint tests ─────────────────────────────────────────────


def test_list_categories():
    """Verify GET /api/foods/categories returns categories sorted by name."""
    client = make_client()
    from app.db import session as db_session

    db = db_session.SessionLocal()
    seed_basics(db)

    # Add more categories
    cat2 = FoodCategory(name="Vegetables", slug="vegetables")
    cat3 = FoodCategory(name="Dairy", slug="dairy")
    db.add_all([cat2, cat3])
    db.commit()

    resp = client.get("/api/foods/categories")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    # Sorted alphabetically: Dairy, Grains, Vegetables
    assert data[0]["name"] == "Dairy"
    assert data[0]["slug"] == "dairy"
    assert data[1]["name"] == "Grains"
    assert data[2]["name"] == "Vegetables"
    # Each category has id, name, slug
    for cat in data:
        assert "id" in cat
        assert "name" in cat
        assert "slug" in cat

    db.close()


def test_list_categories_empty():
    """Verify categories endpoint works when no categories exist."""
    client = make_client()
    resp = client.get("/api/foods/categories")
    assert resp.status_code == 200
    assert resp.json() == []


# ── Filter tests ──────────────────────────────────────────────────────────


def test_filter_by_category_slug():
    """Verify category_slug filter correctly limits results."""
    client = make_client()
    from app.db import session as db_session

    db = db_session.SessionLocal()
    basics = seed_basics(db)

    cat_veg = FoodCategory(name="Vegetables", slug="vegetables")
    db.add(cat_veg)
    db.flush()

    create_food(
        db, slug="rice", name="Rice", category=basics["category"],
        serving_unit=basics["unit_g"],
    )
    create_food(
        db, slug="spinach", name="Spinach", category=cat_veg,
        serving_unit=basics["unit_g"],
    )
    db.commit()

    # Filter by grains
    resp = client.get("/api/foods?category_slug=grains")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["slug"] == "rice"

    # Filter by vegetables
    resp = client.get("/api/foods?category_slug=vegetables")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["slug"] == "spinach"

    db.close()


def test_filter_by_verification_status():
    """Verify verification_status filter correctly limits results."""
    client = make_client()
    from app.db import session as db_session

    db = db_session.SessionLocal()
    basics = seed_basics(db)

    create_food(
        db, slug="verified-food", name="Verified Food",
        category=basics["category"], serving_unit=basics["unit_g"],
        verification_status=VerificationStatus.VERIFIED,
    )
    create_food(
        db, slug="pending-food", name="Pending Food",
        category=basics["category"], serving_unit=basics["unit_g"],
        verification_status=VerificationStatus.PENDING_REVIEW,
    )
    db.commit()

    # Filter verified only
    resp = client.get("/api/foods?verification_status=verified")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["slug"] == "verified-food"
    assert data["items"][0]["verification_status"] == "verified"

    # Filter pending_review only
    resp = client.get("/api/foods?verification_status=pending_review")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["slug"] == "pending-food"

    # Invalid status returns empty
    resp = client.get("/api/foods?verification_status=bogus")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0

    db.close()


def test_filter_by_dietary_tag_slug():
    """Verify dietary_tag_slug filter returns only foods with that tag."""
    client = make_client()
    from app.db import session as db_session

    db = db_session.SessionLocal()
    basics = seed_basics(db)

    tag = DietaryTag(slug="gluten-free", name="Gluten Free", kind=DietaryTagKind.RESTRICTION)
    db.add(tag)
    db.flush()

    food_with_tag = create_food(
        db, slug="rice", name="Rice", category=basics["category"],
        serving_unit=basics["unit_g"],
    )
    food_with_tag.dietary_tags.append(tag)

    create_food(
        db, slug="bread", name="Bread", category=basics["category"],
        serving_unit=basics["unit_g"],
    )
    db.commit()

    resp = client.get("/api/foods?dietary_tag_slug=gluten-free")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["slug"] == "rice"

    db.close()


def test_filter_by_cuisine_tag_slug():
    """Verify cuisine_tag_slug filter returns only foods with that tag."""
    client = make_client()
    from app.db import session as db_session

    db = db_session.SessionLocal()
    basics = seed_basics(db)

    tag = CuisineTag(slug="pakistani", name="Pakistani")
    db.add(tag)
    db.flush()

    food_with_tag = create_food(
        db, slug="biryani", name="Biryani", category=basics["category"],
        serving_unit=basics["unit_g"],
    )
    food_with_tag.cuisine_tags.append(tag)

    create_food(
        db, slug="sushi", name="Sushi", category=basics["category"],
        serving_unit=basics["unit_g"],
    )
    db.commit()

    resp = client.get("/api/foods?cuisine_tag_slug=pakistani")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["slug"] == "biryani"

    db.close()


def test_search_by_text():
    """Verify text search works across name and description."""
    client = make_client()
    from app.db import session as db_session

    db = db_session.SessionLocal()
    basics = seed_basics(db)

    create_food(
        db, slug="basmati-rice", name="Basmati Rice",
        description="Aromatic long grain rice",
        category=basics["category"], serving_unit=basics["unit_g"],
    )
    create_food(
        db, slug="chicken-curry", name="Chicken Curry",
        description="Spicy chicken curry",
        category=basics["category"], serving_unit=basics["unit_g"],
    )
    db.commit()

    # Search by name
    resp = client.get("/api/foods?q=basmati")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1

    # Search by description
    resp = client.get("/api/foods?q=curry")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1

    # No match
    resp = client.get("/api/foods?q=xyz")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0

    db.close()


def test_pagination():
    """Verify limit and offset pagination works."""
    client = make_client()
    from app.db import session as db_session

    db = db_session.SessionLocal()
    basics = seed_basics(db)

    for i in range(5):
        create_food(
            db, slug=f"food-{i}", name=f"Food {i}",
            category=basics["category"], serving_unit=basics["unit_g"],
        )
    db.commit()

    # First page
    resp = client.get("/api/foods?limit=2&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["items"][0]["name"] == "Food 0"

    # Second page
    resp = client.get("/api/foods?limit=2&offset=2")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["items"][0]["name"] == "Food 2"

    db.close()
