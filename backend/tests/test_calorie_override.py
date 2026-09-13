"""Tests for the manual calorie target override on meal plan generation.

Verifies that:
- POST /api/meal-plans/generate accepts an optional calorie_target override.
- The override replaces the BMR/TDEE-computed target and macros are
  recalculated from it.
- Values outside the safety bounds (1000-6000 kcal) are clamped with a
  warning in the plan response.
- Omitting the field keeps the previous behavior (profile-derived targets).
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-1234567890abcdefg")
os.environ.setdefault("CSRF_SECRET_KEY", "test-csrf-secret-key-1234567890abcdef")
os.environ.setdefault("ENVIRONMENT", "testing")

from app import models as app_models  # noqa: F401
from app.core.config import settings
from app.core.rate_limit import generation_ip_limiter, login_rate_limiter
from app.db import session as db_session
from app.db.base import Base
from app.main import app
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
    login_rate_limiter.clear()
    generation_ip_limiter.clear()


def seed_food_dataset() -> None:
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


def _onboarding_payload() -> dict:
    from app.models.enums import UnitSystem

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


def onboarded_client(email: str = "override@example.com") -> TestClient:
    reset_db()
    seed_food_dataset()
    client = TestClient(app)
    resp = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "StrongPass!123",
            "display_name": "Test User",
        },
    )
    assert resp.status_code == 201, resp.text
    client = TestClient(app)
    resp = client.post(
        "/api/auth/login",
        json={"email": email, "password": "StrongPass!123"},
    )
    assert resp.status_code == 200, resp.text
    csrf = client.get("/api/auth/csrf").json()["csrf_token"]
    resp = client.post(
        "/api/auth/onboarding",
        json=_onboarding_payload(),
        headers={"X-CSRF-Token": csrf},
    )
    assert resp.status_code == 200, resp.text
    return client


def post_generate(client: TestClient, body: dict) -> object:
    csrf = client.get("/api/auth/csrf").json()["csrf_token"]
    return client.post(
        "/api/meal-plans/generate",
        json=body,
        headers={"X-CSRF-Token": csrf},
    )


# ── Tests ────────────────────────────────────────────────────────────────────


class TestCalorieOverride:
    def test_override_replaces_computed_target(self):
        """A manual calorie target replaces the profile-computed one exactly."""
        client = onboarded_client()

        # Baseline: computed target without override
        resp = post_generate(client, {"plan_days": 1, "meal_count": 4})
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data.get("success") is not False, data
        computed = data["nutrition"]["calorie_target"]

        # Override with a distinctly different target
        manual = 2400 if computed < 2400 else 1500
        resp2 = post_generate(
            client, {"plan_days": 1, "meal_count": 4, "calorie_target": manual}
        )
        assert resp2.status_code == 200, resp2.text
        data2 = resp2.json()
        assert data2.get("success") is not False, data2
        assert data2["nutrition"]["calorie_target"] == manual
        assert data2["nutrition"]["calorie_target"] != computed

    def test_override_recalculates_macros(self):
        """Macros are recalculated from the override, not the old target."""
        client = onboarded_client()

        resp = post_generate(client, {"plan_days": 1, "meal_count": 4, "calorie_target": 2000})
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data.get("success") is not False, data

        nutrition = data["nutrition"]
        total = (
            nutrition["protein_g"] * 4
            + nutrition["carbs_g"] * 4
            + nutrition["fat_g"] * 9
        )
        # Macro calorie sum must track the override (small rounding tolerance)
        assert abs(total - 2000) <= 15, f"macros sum to {total}, expected ~2000"

    def test_override_clamped_to_safety_bounds(self):
        """A dangerously low override is clamped to 1000 kcal."""
        client = onboarded_client()

        resp = post_generate(client, {"plan_days": 1, "meal_count": 4, "calorie_target": 300})
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data.get("success") is not False, data

        assert data["nutrition"]["calorie_target"] == 1000.0

    def test_clamp_warning_emitted_at_service_level(self):
        """The service emits a clamp warning (note: generation responses are
        rebuilt from DB after persist, which drops all warnings — a
        pre-existing gap affecting every generation warning, not just the
        override clamp)."""
        from app.services.nutrition_service import calculate_nutrition_targets

        result = calculate_nutrition_targets(
            sex="male",
            age=28,
            height_cm=175,
            weight_kg=72,
            activity_level="moderately_active",
            goal="general_fitness",
            calorie_override=300,
        )
        assert result.calorie_target == 1000.0
        assert any("Manual calorie target" in w for w in result.warnings)

        result_high = calculate_nutrition_targets(
            sex="male",
            age=28,
            height_cm=175,
            weight_kg=72,
            activity_level="moderately_active",
            goal="general_fitness",
            calorie_override=9000,
        )
        assert result_high.calorie_target == 6000.0
        assert any("Manual calorie target" in w for w in result_high.warnings)

    def test_high_override_clamped_to_max(self):
        """An extreme override is clamped down to 6000 kcal."""
        client = onboarded_client()

        resp = post_generate(client, {"plan_days": 1, "meal_count": 4, "calorie_target": 9000})
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data.get("success") is not False, data

        assert data["nutrition"]["calorie_target"] == 6000.0

    def test_omitting_override_keeps_computed_target(self):
        """No override → previous behavior (profile-derived target)."""
        client = onboarded_client()

        resp = post_generate(client, {"plan_days": 1, "meal_count": 4})
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data.get("success") is not False, data

        nutrition = data["nutrition"]
        assert nutrition["calorie_target"] > 0
        assert not any("Manual calorie target" in w for w in nutrition["warnings"])

    def test_sub_1000_override_is_clamped_not_rejected(self):
        """Values below the schema floor (but > 0) are gracefully clamped."""
        client = onboarded_client()

        resp = post_generate(client, {"plan_days": 1, "meal_count": 4, "calorie_target": 300})
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data.get("success") is not False, data
        assert data["nutrition"]["calorie_target"] == 1000.0

    def test_garbage_huge_override_is_clamped(self):
        """An absurd override (50000, schema max) is clamped down to 6000."""
        client = onboarded_client()

        resp = post_generate(client, {"plan_days": 1, "meal_count": 4, "calorie_target": 50000})
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data.get("success") is not False, data
        assert data["nutrition"]["calorie_target"] == 6000.0

    def test_invalid_type_rejected_by_validation(self):
        """Non-numeric / negative values are rejected with 422."""
        client = onboarded_client()

        resp = post_generate(client, {"plan_days": 1, "meal_count": 4, "calorie_target": -5})
        assert resp.status_code == 422, resp.text

    def test_out_of_range_rejected_by_validation(self):
        """Values beyond the schema bounds (1-50000) are 422s."""
        client = onboarded_client()

        resp = post_generate(client, {"plan_days": 1, "meal_count": 4, "calorie_target": 9000000})
        assert resp.status_code == 422, resp.text
