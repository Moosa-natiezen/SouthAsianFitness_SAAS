"""Integration tests for meal plan generation → persistence → retrieval.

Verifies that POST /api/meal-plans/generate persists the plan,
and GET /api/meal-plans/today can retrieve it.
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-1234567890abcdefg")
os.environ.setdefault("CSRF_SECRET_KEY", "test-csrf-secret-key-1234567890abcdef")
os.environ.setdefault("ENVIRONMENT", "testing")

from app import models as app_models  # noqa: F401
from app.core.config import settings
from app.core.rate_limit import login_rate_limiter
from app.db import session as db_session
from app.db.base import Base
from app.main import app
from app.models.enums import (
    UnitSystem,
)
from app.models.meal_plan import MealPlan
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# ── Test helpers ─────────────────────────────────────────────────────────────


def reset_db() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db_session.engine = engine
    db_session.SessionLocal = sessionmaker(
        bind=engine, autocommit=False, autoflush=False, class_=Session
    )
    settings.database_url = str(engine.url)


def make_client() -> TestClient:
    reset_db()
    login_rate_limiter.clear()
    return TestClient(app)


def api_register(client: TestClient, email: str = "user@example.com") -> dict:
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "StrongPass!123",
            "display_name": "Test User",
        },
    )
    assert response.status_code == 201, response.text
    client.get("/api/auth/csrf")
    return response.json()


def api_login(client: TestClient, email: str = "user@example.com") -> dict:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "StrongPass!123"},
    )
    if response.status_code == 401:
        api_register(client, email)
        response = client.post(
            "/api/auth/login",
            json={"email": email, "password": "StrongPass!123"},
        )
    assert response.status_code == 200, response.text
    client.get("/api/auth/csrf")
    return response.json()


def get_csrf(client: TestClient) -> str:
    return client.get("/api/auth/csrf").json()["csrf_token"]


def onboard_user(client: TestClient) -> TestClient:
    """Register + login + onboard on the given client. Returns the client."""
    api_register(client)
    # Fresh client to pick up session cookie from register
    client = TestClient(app)
    api_login(client)

    csrf = get_csrf(client)
    response = client.post(
        "/api/auth/onboarding",
        json=_onboarding_payload(),
        headers={"X-CSRF-Token": csrf},
    )
    assert response.status_code == 200, response.text
    return client


def setup_test_db_with_user(email: str = "user@example.com") -> TestClient:
    """Reset DB, seed foods, onboard user. Returns an authenticated client."""
    reset_db()
    seed_food_dataset()
    # Create client without reset_db (which make_client does)
    client = TestClient(app)
    api_register(client, email)
    # Fresh client to pick up session cookie from register
    client = TestClient(app)
    api_login(client, email)
    csrf = get_csrf(client)
    onboard_response = client.post(
        "/api/auth/onboarding",
        json=_onboarding_payload(),
        headers={"X-CSRF-Token": csrf},
    )
    assert onboard_response.status_code == 200, onboard_response.text
    return client


def seed_food_dataset():
    """Seed a minimal food dataset for meal plan generation."""
    from app.models.enums import UnitDimension, VerificationStatus
    from app.models.food import Food
    from app.models.tags import FoodCategory
    from app.models.unit import Unit

    db = db_session.SessionLocal()
    try:
        unit_g = Unit(code="g", name="gram", dimension=UnitDimension.MASS, to_base_factor=1)
        db.add(unit_g)
        db.flush()

        categories = {}
        for slug in ["grains", "meats", "dairy", "vegetables", "fruits", "legumes", "oils"]:
            cat = FoodCategory(name=slug.title(), slug=slug)
            db.add(cat)
            categories[slug] = cat
        db.flush()

        foods_data = [
            ("basmati-rice", "Basmati Rice", "grains", 130, 2.7, 28, 0.3),
            ("roti", "Roti (Chapati)", "grains", 105, 3.0, 18, 2.5),
            ("chicken-curry", "Chicken Curry", "meats", 180, 25, 3, 8),
            ("moong-dal", "Moong Dal", "legumes", 104, 7.0, 18, 0.4),
            ("yogurt", "Plain Yogurt", "dairy", 60, 3.5, 5, 3),
            ("sabzi-mix", "Mixed Vegetable Sabzi", "vegetables", 65, 2.5, 8, 2.5),
            ("banana", "Banana", "fruits", 89, 1.1, 23, 0.3),
            ("ghee", "Ghee", "oils", 900, 0, 0, 100),
        ]

        for slug, name, cat_slug, cal, pro, carb, fat in foods_data:
            food = Food(
                slug=slug,
                name=name,
                category_id=categories[cat_slug].id,
                serving_size=100,
                serving_unit_id=unit_g.id,
                grams_per_serving=100,
                calories=cal,
                protein_g=pro,
                carbs_g=carb,
                fat_g=fat,
                is_active=True,
                verification_status=VerificationStatus.VERIFIED,
            )
            db.add(food)

        db.commit()
    finally:
        db.close()


def setup_test_db() -> TestClient:
    """Reset DB, seed foods, create client, register, login, and onboard."""
    reset_db()
    seed_food_dataset()
    client = make_client()
    api_register(client)
    client = TestClient(app)
    api_login(client)
    csrf = get_csrf(client)
    onboard_response = client.post(
        "/api/auth/onboarding",
        json=_onboarding_payload(),
        headers={"X-CSRF-Token": csrf},
    )
    assert onboard_response.status_code == 200, onboard_response.text
    return client


def _onboarding_payload() -> dict:
    db = db_session.SessionLocal()
    try:
        from app.models.currency import Currency
        from app.models.geography import Country

        currency = db.query(Currency).filter(Currency.code == "PKR").first()
        if currency is None:
            currency = Currency(code="PKR", name="Pakistani Rupee", symbol="Rs", minor_units=2)
            db.add(currency)
            db.flush()

        country = db.query(Country).filter(Country.iso_code == "PK").first()
        if country is None:
            country = Country(
                name="Pakistan",
                iso_code="PK",
                currency_code="PKR",
                default_unit_system=UnitSystem.METRIC,
            )
            db.add(country)
            db.flush()
        country_id = str(country.id)
    finally:
        db.commit()
        db.close()

    return {
        "country_id": country_id,
        "region_id": None,
        "preferred_currency_code": "PKR",
        "preferred_language": "en",
        "unit_system": "metric",
        "age_years": 28,
        "sex": "male",
        "height_cm": 175,
        "weight_kg": 72,
        "activity_level": "moderately_active",
        "fitness_goal": "general_fitness",
        "diet_pattern": "omnivore",
        "dietary_tag_slugs": [],
        "allergen_tag_slugs": [],
        "food_dislikes": [],
        "preferred_foods": [],
    }


# ── Tests ────────────────────────────────────────────────────────────────────


class TestGeneratePersistRetrieve:
    """Full flow: generate → persist → retrieve."""

    def test_generate_then_today(self):
        """POST /generate persists the plan, GET /today retrieves it."""
        client = setup_test_db_with_user()
        csrf = get_csrf(client)

        # Generate
        gen_resp = client.post(
            "/api/meal-plans/generate",
            json={"plan_days": 1, "meal_count": 4},
            headers={"X-CSRF-Token": csrf},
        )
        assert gen_resp.status_code == 200, gen_resp.text
        gen_data = gen_resp.json()
        assert "plan_id" in gen_data
        assert len(gen_data["days"]) == 1

        # Verify plan exists in database
        db = db_session.SessionLocal()
        try:
            plan_count = db.query(MealPlan).count()
            assert plan_count == 1, f"Expected 1 MealPlan, got {plan_count}"
        finally:
            db.close()

        # Retrieve via /today
        today_resp = client.get("/api/meal-plans/today")
        assert today_resp.status_code == 200, today_resp.text
        today_data = today_resp.json()
        assert today_data["plan_id"] == gen_data["plan_id"]
        assert today_data["plan_name"] == gen_data["plan_name"]
        assert len(today_data["days"]) == 1

    def test_generate_persists_meal_plan_records(self):
        """Generated plan should create MealPlan, MealPlanDay, Meal, MealFood records."""
        client = setup_test_db_with_user()
        csrf = get_csrf(client)

        gen_resp = client.post(
            "/api/meal-plans/generate",
            json={"plan_days": 1, "meal_count": 4},
            headers={"X-CSRF-Token": csrf},
        )
        assert gen_resp.status_code == 200, gen_resp.text

        from app.models.meal import Meal, MealFood
        from app.models.meal_plan import MealPlanDay, MealPlanDayMeal

        db = db_session.SessionLocal()
        try:
            assert db.query(MealPlan).count() == 1
            assert db.query(MealPlanDay).count() >= 1
            assert db.query(MealPlanDayMeal).count() >= 1
            assert db.query(Meal).count() >= 1
            assert db.query(MealFood).count() >= 1
        finally:
            db.close()

    def test_generate_failure_does_not_create_meal_plan(self):
        """When generation fails, no MealPlan should be created."""
        reset_db()
        seed_food_dataset()
        # Register a user WITHOUT onboarding (no profile)
        client = TestClient(app)
        api_register(client, "noprofile@example.com")
        client = TestClient(app)
        api_login(client, "noprofile@example.com")
        csrf = get_csrf(client)

        # Generate should fail because user has no profile
        gen_resp = client.post(
            "/api/meal-plans/generate",
            json={"plan_days": 1, "meal_count": 4},
            headers={"X-CSRF-Token": csrf},
        )
        assert gen_resp.status_code == 200
        gen_data = gen_resp.json()
        assert gen_data.get("success") is False

        db = db_session.SessionLocal()
        try:
            assert db.query(MealPlan).count() == 0
        finally:
            db.close()

    def test_today_returns_404_when_no_plan(self):
        """GET /today returns 404 when no plan exists."""
        client = setup_test_db_with_user()

        resp = client.get("/api/meal-plans/today")
        assert resp.status_code == 404

    def test_user_isolation(self):
        """User A's plan should not be visible to User B."""
        client_a = setup_test_db_with_user("alice@example.com")
        csrf_a = get_csrf(client_a)
        gen_resp = client_a.post(
            "/api/meal-plans/generate",
            json={"plan_days": 1},
            headers={"X-CSRF-Token": csrf_a},
        )
        assert gen_resp.status_code == 200

        # User B should not see User A's plan
        client_b = setup_test_db_with_user("bob@example.com")
        today_resp = client_b.get("/api/meal-plans/today")
        assert today_resp.status_code == 404

    def test_generate_then_today_does_not_create_second_plan(self):
        """GET /today after generation should not create another plan."""
        client = setup_test_db_with_user()
        csrf = get_csrf(client)

        # Generate
        gen_resp = client.post(
            "/api/meal-plans/generate",
            json={"plan_days": 1},
            headers={"X-CSRF-Token": csrf},
        )
        assert gen_resp.status_code == 200

        db = db_session.SessionLocal()
        try:
            count_before = db.query(MealPlan).count()
        finally:
            db.close()

        # Retrieve
        today_resp = client.get("/api/meal-plans/today")
        assert today_resp.status_code == 200

        db = db_session.SessionLocal()
        try:
            count_after = db.query(MealPlan).count()
            assert count_after == count_before, (
                f"GET /today should not create plans: before={count_before}, after={count_after}"
            )
        finally:
            db.close()

    def test_unauthenticated_generate_rejected(self):
        """POST /generate without auth should return 401."""
        reset_db()
        client = TestClient(app)
        resp = client.post("/api/meal-plans/generate", json={"plan_days": 1})
        assert resp.status_code == 401

    def test_no_csrf_generate_rejected(self):
        """POST /generate without CSRF should return 403."""
        client = setup_test_db_with_user()

        resp = client.post(
            "/api/meal-plans/generate",
            json={"plan_days": 1},
        )
        assert resp.status_code == 403

    def test_generated_plan_has_valid_nutrition(self):
        """The persisted plan should have valid nutrition targets."""
        client = setup_test_db_with_user()
        csrf = get_csrf(client)

        gen_resp = client.post(
            "/api/meal-plans/generate",
            json={"plan_days": 1, "meal_count": 4},
            headers={"X-CSRF-Token": csrf},
        )
        assert gen_resp.status_code == 200
        data = gen_resp.json()
        assert data["nutrition"]["calorie_target"] > 0
        assert data["nutrition"]["protein_g"] > 0
        assert data["nutrition"]["carbs_g"] > 0
        assert data["nutrition"]["fat_g"] > 0
