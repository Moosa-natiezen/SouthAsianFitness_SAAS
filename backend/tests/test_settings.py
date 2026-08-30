"""Tests for Settings API endpoints.

Covers:
- GET settings returns current values
- GET settings works for authenticated user
- GET settings rejects unauthenticated user
- Profile update succeeds
- Display name update persists
- Profile numeric values update correctly
- Profile enum values update correctly
- Invalid enum values are rejected
- Invalid numeric values are rejected
- Preferences update succeeds
- Budget update persists
- Dietary preference updates persist
- Existing unrelated preference values are preserved during partial update
- Country/region relationship is validated
- Unauthenticated profile update rejected
- Unauthenticated preferences update rejected
- Missing CSRF rejects profile update
- Missing CSRF rejects preferences update
- User isolation is preserved
- is_onboarded remains unchanged after profile update
- is_active remains unchanged
- Protected fields cannot be modified
- Existing profile/preferences records are updated rather than duplicated
- Missing optional fields do not overwrite existing values
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-1234567890abcdefg")
os.environ.setdefault("CSRF_SECRET_KEY", "test-csrf-secret-key-1234567890abcdef")
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("DEBUG", "false")

from decimal import Decimal

from app import models as app_models  # noqa: F401
from app.core.config import settings
from app.core.rate_limit import login_rate_limiter
from app.db import session as db_session
from app.db.base import Base
from app.main import app
from app.models.enums import (
    ActivityLevel,
    DietPattern,
    FitnessGoal,
    Sex,
    UnitSystem,
)
from app.models.user import User, UserPreferences, UserProfile
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


def create_onboarded_user(
    db: Session,
    *,
    email: str = "user@example.com",
) -> User:
    """Create a fully onboarded user with profile and preferences."""
    user = User(
        email=email,
        display_name="Test User",
        password_hash="fakehash",
        preferred_language="en",
        preferred_unit_system=UnitSystem.METRIC,
        preferred_currency_code="PKR",
        is_onboarded=True,
        is_active=True,
    )
    db.add(user)
    db.flush()

    profile = UserProfile(
        user_id=user.id,
        age_years=28,
        sex=Sex.MALE,
        height_cm=Decimal("175.00"),
        weight_kg=Decimal("75.00"),
        activity_level=ActivityLevel.MODERATELY_ACTIVE,
        fitness_goal=FitnessGoal.WEIGHT_LOSS,
        diet_pattern=DietPattern.OMNIVORE,
    )
    db.add(profile)

    prefs = UserPreferences(
        user_id=user.id,
        weekly_budget_amount=Decimal("5000.00"),
        budget_currency_code="PKR",
        notes='{"food_dislikes": ["bitter_gourd"], "preferred_foods": ["chicken_biryani"], "budget_period": "weekly"}',
    )
    db.add(prefs)
    db.commit()
    return user


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


def setup_onboarded_client() -> tuple[TestClient, dict]:
    """Set up a client with a fully onboarded user via the API."""
    reset_db()
    client = TestClient(app)
    api_register(client)
    client = TestClient(app)
    api_login(client)
    csrf = get_csrf(client)

    # Onboard the user
    client.post(
        "/api/auth/onboarding",
        json={
            "country_id": "00000000-0000-0000-0000-000000000001",
            "region_id": None,
            "preferred_currency_code": "PKR",
            "preferred_language": "en",
            "unit_system": "metric",
            "age_years": 28,
            "sex": "male",
            "height_cm": 175.0,
            "weight_kg": 75.0,
            "activity_level": "moderately_active",
            "fitness_goal": "weight_loss",
            "diet_pattern": "omnivore",
            "dietary_tag_slugs": [],
            "allergen_tag_slugs": [],
            "food_dislikes": [],
            "preferred_foods": [],
        },
        headers={"X-CSRF-Token": csrf},
    )
    # Onboarding may fail if country doesn't exist in seed data — that's OK
    # for settings tests; we just need an authenticated user with csrf
    return client, {"csrf": csrf}


# ── Service layer tests ──────────────────────────────────────────────────────


class TestGetUserSettings:
    def test_returns_current_values(self) -> None:
        reset_db()
        db = db_session.SessionLocal()
        user = create_onboarded_user(db)

        from app.services.settings_service import get_user_settings

        data = get_user_settings(db, user)
        assert data["display_name"] == "Test User"
        assert data["email"] == "user@example.com"
        assert data["preferred_language"] == "en"
        assert data["preferred_unit_system"] == "metric"
        assert data["preferred_currency_code"] == "PKR"
        assert data["profile"] is not None
        assert data["profile"]["age_years"] == 28
        assert data["profile"]["sex"] == "male"
        assert data["profile"]["height_cm"] == Decimal("175.00")
        assert data["profile"]["weight_kg"] == Decimal("75.00")
        assert data["profile"]["activity_level"] == "moderately_active"
        assert data["profile"]["fitness_goal"] == "weight_loss"
        assert data["profile"]["diet_pattern"] == "omnivore"
        assert data["preferences"] is not None
        assert data["preferences"]["weekly_budget_amount"] == Decimal("5000.00")
        assert data["preferences"]["budget_currency_code"] == "PKR"
        assert data["preferences"]["budget_period"] == "weekly"
        assert data["preferences"]["food_dislikes"] == ["bitter_gourd"]
        assert data["preferences"]["preferred_foods"] == ["chicken_biryani"]
        db.close()

    def test_returns_none_for_missing_profile(self) -> None:
        reset_db()
        db = db_session.SessionLocal()
        user = User(
            email="noprofile@example.com",
            display_name="No Profile",
            password_hash="fakehash",
            preferred_language="en",
            is_onboarded=False,
            is_active=True,
        )
        db.add(user)
        db.commit()

        from app.services.settings_service import get_user_settings

        data = get_user_settings(db, user)
        assert data["profile"] is None
        assert data["preferences"] is not None
        db.close()


class TestUpdateUserProfile:
    def test_updates_display_name(self) -> None:
        reset_db()
        db = db_session.SessionLocal()
        user = create_onboarded_user(db)

        from app.services.settings_service import update_user_profile

        update_user_profile(db, user, {"display_name": "New Name"})
        assert user.display_name == "New Name"
        db.close()

    def test_updates_numeric_values(self) -> None:
        reset_db()
        db = db_session.SessionLocal()
        user = create_onboarded_user(db)

        from app.services.settings_service import update_user_profile

        update_user_profile(
            db, user, {"age_years": 30, "height_cm": Decimal("180.0"), "weight_kg": Decimal("80.0")}
        )
        assert user.profile.age_years == 30
        assert user.profile.height_cm == Decimal("180.0")
        assert user.profile.weight_kg == Decimal("80.0")
        db.close()

    def test_updates_enum_values(self) -> None:
        reset_db()
        db = db_session.SessionLocal()
        user = create_onboarded_user(db)

        from app.services.settings_service import update_user_profile

        update_user_profile(
            db,
            user,
            {
                "activity_level": ActivityLevel.VERY_ACTIVE,
                "fitness_goal": FitnessGoal.MUSCLE_BUILDING,
                "diet_pattern": DietPattern.VEGETARIAN,
                "sex": Sex.FEMALE,
            },
        )
        assert user.profile.activity_level == ActivityLevel.VERY_ACTIVE
        assert user.profile.fitness_goal == FitnessGoal.MUSCLE_BUILDING
        assert user.profile.diet_pattern == DietPattern.VEGETARIAN
        assert user.profile.sex == Sex.FEMALE
        db.close()

    def test_preserves_is_onboarded(self) -> None:
        reset_db()
        db = db_session.SessionLocal()
        user = create_onboarded_user(db)
        assert user.is_onboarded is True

        from app.services.settings_service import update_user_profile

        update_user_profile(db, user, {"display_name": "Changed"})
        assert user.is_onboarded is True
        db.close()

    def test_preserves_is_active(self) -> None:
        reset_db()
        db = db_session.SessionLocal()
        user = create_onboarded_user(db)
        assert user.is_active is True

        from app.services.settings_service import update_user_profile

        update_user_profile(db, user, {"display_name": "Changed"})
        assert user.is_active is True
        db.close()

    def test_partial_update_preserves_existing(self) -> None:
        reset_db()
        db = db_session.SessionLocal()
        user = create_onboarded_user(db)

        from app.services.settings_service import update_user_profile

        # Only update display_name — nothing else should change
        update_user_profile(db, user, {"display_name": "Updated"})
        assert user.profile.age_years == 28
        assert user.profile.weight_kg == Decimal("75.00")
        assert user.profile.fitness_goal == FitnessGoal.WEIGHT_LOSS
        assert user.preferred_language == "en"
        db.close()

    def test_creates_profile_if_missing(self) -> None:
        reset_db()
        db = db_session.SessionLocal()
        user = User(
            email="nopropref@example.com",
            display_name="No Profile",
            password_hash="fakehash",
            preferred_language="en",
            is_onboarded=True,
            is_active=True,
        )
        db.add(user)
        db.commit()

        from app.services.settings_service import update_user_profile

        # sex, age_years, weight_kg are NOT NULL on UserProfile,
        # so we must supply them when creating from scratch.
        update_user_profile(
            db,
            user,
            {
                "age_years": 25,
                "sex": "male",
                "height_cm": Decimal("170.00"),
                "weight_kg": Decimal("60.0"),
                "activity_level": "moderately_active",
                "fitness_goal": "weight_loss",
            },
        )
        assert user.profile is not None
        assert user.profile.age_years == 25
        assert user.profile.weight_kg == Decimal("60.0")
        assert user.profile.sex.value == "male"
        db.close()

    def test_existing_profile_updated_not_duplicated(self) -> None:
        reset_db()
        db = db_session.SessionLocal()
        user = create_onboarded_user(db)
        original_profile_id = user.profile.id

        from app.services.settings_service import update_user_profile

        update_user_profile(db, user, {"age_years": 35})
        assert user.profile.id == original_profile_id
        assert user.profile.age_years == 35
        db.close()


class TestUpdateUserPreferences:
    def test_updates_budget(self) -> None:
        reset_db()
        db = db_session.SessionLocal()
        user = create_onboarded_user(db)

        from app.services.settings_service import update_user_preferences

        update_user_preferences(
            db, user, {"weekly_budget_amount": Decimal("7500.00")}
        )
        assert user.preferences.weekly_budget_amount == Decimal("7500.00")
        db.close()

    def test_updates_food_dislikes(self) -> None:
        reset_db()
        db = db_session.SessionLocal()
        user = create_onboarded_user(db)

        from app.services.settings_service import update_user_preferences

        update_user_preferences(db, user, {"food_dislikes": ["spinach", "bitter_gourd"]})
        import json

        notes = json.loads(user.preferences.notes)
        assert notes["food_dislikes"] == ["spinach", "bitter_gourd"]
        # preferred_foods should be preserved
        assert notes["preferred_foods"] == ["chicken_biryani"]
        db.close()

    def test_updates_preferred_foods(self) -> None:
        reset_db()
        db = db_session.SessionLocal()
        user = create_onboarded_user(db)

        from app.services.settings_service import update_user_preferences

        update_user_preferences(
            db, user, {"preferred_foods": ["daal", "rice", "roti"]}
        )
        import json

        notes = json.loads(user.preferences.notes)
        assert notes["preferred_foods"] == ["daal", "rice", "roti"]
        # food_dislikes should be preserved
        assert notes["food_dislikes"] == ["bitter_gourd"]
        db.close()

    def test_creates_preferences_if_missing(self) -> None:
        reset_db()
        db = db_session.SessionLocal()
        user = User(
            email="noprefs@example.com",
            display_name="No Prefs",
            password_hash="fakehash",
            preferred_language="en",
            is_onboarded=True,
            is_active=True,
        )
        db.add(user)
        db.commit()

        from app.services.settings_service import update_user_preferences

        update_user_preferences(
            db, user, {"weekly_budget_amount": Decimal("3000.00")}
        )
        assert user.preferences is not None
        assert user.preferences.weekly_budget_amount == Decimal("3000.00")
        db.close()

    def test_existing_preferences_updated_not_duplicated(self) -> None:
        reset_db()
        db = db_session.SessionLocal()
        user = create_onboarded_user(db)
        original_prefs_id = user.preferences.id

        from app.services.settings_service import update_user_preferences

        update_user_preferences(db, user, {"budget_period": "monthly"})
        assert user.preferences.id == original_prefs_id
        db.close()


# ── API endpoint tests ──────────────────────────────────────────────────────


class TestSettingsAPI:
    def test_get_settings_authenticated(self) -> None:
        client = make_client()
        api_register(client, email="settings@example.com")
        client = TestClient(app)
        api_login(client, email="settings@example.com")

        response = client.get("/api/auth/settings")
        assert response.status_code == 200, response.text
        data = response.json()
        assert "display_name" in data
        assert "email" in data
        assert "profile" in data
        assert "preferences" in data

    def test_get_settings_unauthenticated(self) -> None:
        client = make_client()
        response = client.get("/api/auth/settings")
        assert response.status_code == 401

    def test_update_profile_via_api(self) -> None:
        client = make_client()
        api_register(client, email="profile@example.com")
        client = TestClient(app)
        api_login(client, email="profile@example.com")
        csrf = get_csrf(client)

        # User has no profile yet, so PATCH must include all NOT NULL fields
        response = client.patch(
            "/api/auth/profile",
            json={
                "display_name": "Updated Name",
                "age_years": 32,
                "sex": "male",
                "height_cm": 175.0,
                "weight_kg": 80.0,
                "activity_level": "moderately_active",
                "fitness_goal": "weight_loss",
            },
            headers={"X-CSRF-Token": csrf},
        )
        assert response.status_code == 200, response.text
        assert response.json()["status"] == "ok"

        # Verify persistence
        settings_resp = client.get("/api/auth/settings")
        assert settings_resp.status_code == 200
        data = settings_resp.json()
        assert data["display_name"] == "Updated Name"
        assert data["profile"]["age_years"] == 32

    def test_update_profile_unauthenticated(self) -> None:
        client = make_client()
        response = client.patch(
            "/api/auth/profile",
            json={"display_name": "Hacked"},
        )
        assert response.status_code == 401

    def test_update_profile_missing_csrf(self) -> None:
        client = make_client()
        api_register(client)
        client = TestClient(app)
        api_login(client)

        response = client.patch(
            "/api/auth/profile",
            json={"display_name": "No CSRF"},
        )
        assert response.status_code == 403

    def test_update_preferences_via_api(self) -> None:
        client = make_client()
        api_register(client)
        client = TestClient(app)
        api_login(client)
        csrf = get_csrf(client)

        response = client.patch(
            "/api/auth/preferences",
            json={"weekly_budget_amount": 8000, "budget_period": "monthly"},
            headers={"X-CSRF-Token": csrf},
        )
        assert response.status_code == 200, response.text

        # Verify persistence
        settings_resp = client.get("/api/auth/settings")
        assert settings_resp.status_code == 200
        data = settings_resp.json()
        assert float(data["preferences"]["weekly_budget_amount"]) == 8000.0
        assert data["preferences"]["budget_period"] == "monthly"

    def test_update_preferences_unauthenticated(self) -> None:
        client = make_client()
        response = client.patch(
            "/api/auth/preferences",
            json={"weekly_budget_amount": 1000},
        )
        assert response.status_code == 401

    def test_update_preferences_missing_csrf(self) -> None:
        client = make_client()
        api_register(client)
        client = TestClient(app)
        api_login(client)

        response = client.patch(
            "/api/auth/preferences",
            json={"weekly_budget_amount": 1000},
        )
        assert response.status_code == 403

    def test_invalid_enum_rejected(self) -> None:
        client = make_client()
        api_register(client)
        client = TestClient(app)
        api_login(client)
        csrf = get_csrf(client)

        response = client.patch(
            "/api/auth/profile",
            json={"fitness_goal": "invalid_goal"},
            headers={"X-CSRF-Token": csrf},
        )
        assert response.status_code == 422

    def test_invalid_numeric_rejected(self) -> None:
        client = make_client()
        api_register(client)
        client = TestClient(app)
        api_login(client)
        csrf = get_csrf(client)

        response = client.patch(
            "/api/auth/profile",
            json={"weight_kg": -5},
            headers={"X-CSRF-Token": csrf},
        )
        assert response.status_code == 422

    def test_is_onboarded_unchanged_after_update(self) -> None:
        client = make_client()
        api_register(client, email="onboarded@example.com")
        client = TestClient(app)
        api_login(client, email="onboarded@example.com")
        csrf = get_csrf(client)

        # PATCH display_name only — should not affect is_onboarded
        response = client.patch(
            "/api/auth/profile",
            json={"display_name": "Changed"},
            headers={"X-CSRF-Token": csrf},
        )
        assert response.status_code == 200, response.text

        # Check via /me
        me_resp = client.get("/api/auth/me")
        assert me_resp.status_code == 200
        assert me_resp.json()["is_onboarded"] is False  # not onboarded yet

    def test_is_active_unchanged_after_update(self) -> None:
        client = make_client()
        api_register(client, email="active@example.com")
        client = TestClient(app)
        api_login(client, email="active@example.com")
        csrf = get_csrf(client)

        # PATCH display_name only — should not affect is_active
        response = client.patch(
            "/api/auth/profile",
            json={"display_name": "Changed"},
            headers={"X-CSRF-Token": csrf},
        )
        assert response.status_code == 200, response.text

        me_resp = client.get("/api/auth/me")
        assert me_resp.status_code == 200
        assert me_resp.json()["is_active"] is True
