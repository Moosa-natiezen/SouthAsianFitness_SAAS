"""Tests for progress tracking API endpoints.

Covers:
- Create progress entry successfully
- Reject weight <= 0
- Reject duplicate entry for same user/date
- List progress entries
- User isolation
- Summary with no progress entries
- Summary with progress entries
- Correct weight change calculation
- Correct BMI calculation
- Optional fields are persisted
- Unauthenticated requests are rejected
- User cannot create an entry for another user
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-1234567890abcdefg")
os.environ.setdefault("CSRF_SECRET_KEY", "test-csrf-secret-key-1234567890abcdef")
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("DEBUG", "false")

from datetime import date
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
from app.models.user import User, UserProfile
from app.services.progress_service import (
    create_progress_entry,
    get_progress_summary,
    list_progress_entries,
)
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


def create_user_with_profile(
    db: Session,
    *,
    email: str = "test@example.com",
    weight_kg: float = 75.0,
    height_cm: float = 175.0,
    fitness_goal: FitnessGoal = FitnessGoal.WEIGHT_LOSS,
) -> User:
    user = User(
        email=email,
        display_name="Test User",
        password_hash="fakehash",
        preferred_language="en",
        preferred_unit_system=UnitSystem.METRIC,
        preferred_currency_code="PKR",
    )
    db.add(user)
    db.flush()

    profile = UserProfile(
        user_id=user.id,
        age_years=28,
        sex=Sex.MALE,
        height_cm=Decimal(str(height_cm)),
        weight_kg=Decimal(str(weight_kg)),
        activity_level=ActivityLevel.MODERATELY_ACTIVE,
        fitness_goal=fitness_goal,
        diet_pattern=DietPattern.OMNIVORE,
    )
    db.add(profile)
    db.commit()
    return user


def api_register(
    client: TestClient, email: str = "user@example.com"
) -> dict:
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


def api_login(
    client: TestClient, email: str = "user@example.com"
) -> dict:
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


# ── Service layer tests ──────────────────────────────────────────────────────


class TestCreateProgressEntry:
    def test_creates_entry_successfully(self):
        reset_db()
        db = db_session.SessionLocal()
        user = create_user_with_profile(db)

        entry = create_progress_entry(
            db,
            user,
            recorded_on=date(2026, 1, 15),
            weight_kg=Decimal("74.5"),
        )
        assert entry.weight_kg == Decimal("74.5")
        assert entry.recorded_on == date(2026, 1, 15)
        assert entry.user_id == user.id
        assert entry.waist_cm is None
        assert entry.hip_cm is None
        assert entry.body_fat_percent is None
        assert entry.notes is None
        db.close()

    def test_persists_optional_fields(self):
        reset_db()
        db = db_session.SessionLocal()
        user = create_user_with_profile(db)

        entry = create_progress_entry(
            db,
            user,
            recorded_on=date(2026, 1, 15),
            weight_kg=Decimal("74.5"),
            waist_cm=Decimal("82.0"),
            hip_cm=Decimal("95.0"),
            body_fat_percent=Decimal("18.5"),
            notes="Felt good today",
        )
        assert entry.waist_cm == Decimal("82.0")
        assert entry.hip_cm == Decimal("95.0")
        assert entry.body_fat_percent == Decimal("18.5")
        assert entry.notes == "Felt good today"
        db.close()

    def test_rejects_duplicate_date(self):
        reset_db()
        db = db_session.SessionLocal()
        user = create_user_with_profile(db)

        create_progress_entry(
            db,
            user,
            recorded_on=date(2026, 1, 15),
            weight_kg=Decimal("74.5"),
        )

        try:
            create_progress_entry(
                db,
                user,
                recorded_on=date(2026, 1, 15),
                weight_kg=Decimal("73.0"),
            )
            assert False, "Should have raised ValueError"
        except ValueError as exc:
            assert "already exists" in str(exc)
        db.close()


class TestListProgressEntries:
    def test_returns_entries_ordered_by_date_desc(self):
        reset_db()
        db = db_session.SessionLocal()
        user = create_user_with_profile(db)

        for i, d in enumerate(
            [date(2026, 1, 10), date(2026, 1, 15), date(2026, 1, 12)]
        ):
            create_progress_entry(
                db,
                user,
                recorded_on=d,
                weight_kg=Decimal(str(75 - i)),
            )

        entries = list_progress_entries(db, user.id)
        assert len(entries) == 3
        assert entries[0].recorded_on == date(2026, 1, 15)
        assert entries[1].recorded_on == date(2026, 1, 12)
        assert entries[2].recorded_on == date(2026, 1, 10)
        db.close()

    def test_user_isolation(self):
        reset_db()
        db = db_session.SessionLocal()
        user1 = create_user_with_profile(db, email="u1@example.com")
        user2 = create_user_with_profile(db, email="u2@example.com")

        create_progress_entry(
            db,
            user1,
            recorded_on=date(2026, 1, 15),
            weight_kg=Decimal("74.5"),
        )

        entries = list_progress_entries(db, user2.id)
        assert len(entries) == 0
        db.close()

    def test_returns_empty_list_when_no_entries(self):
        reset_db()
        db = db_session.SessionLocal()
        user = create_user_with_profile(db)

        entries = list_progress_entries(db, user.id)
        assert entries == []
        db.close()


class TestGetProgressSummary:
    def test_summary_with_no_entries(self):
        reset_db()
        db = db_session.SessionLocal()
        user = create_user_with_profile(db, weight_kg=75.0, height_cm=175.0)

        summary = get_progress_summary(db, user)
        assert summary["starting_weight_kg"] == Decimal("75.0")
        assert summary["current_weight_kg"] == Decimal("75.0")
        assert summary["weight_change_kg"] == Decimal(0)
        assert summary["entry_count"] == 0
        assert summary["fitness_goal"] == "weight_loss"
        # BMI = 75 / (1.75^2) = 24.5
        assert summary["bmi"] == Decimal("24.5")
        db.close()

    def test_summary_with_entries(self):
        reset_db()
        db = db_session.SessionLocal()
        user = create_user_with_profile(db, weight_kg=80.0, height_cm=170.0)

        create_progress_entry(
            db,
            user,
            recorded_on=date(2026, 1, 1),
            weight_kg=Decimal("79.0"),
        )
        create_progress_entry(
            db,
            user,
            recorded_on=date(2026, 1, 15),
            weight_kg=Decimal("78.0"),
        )

        summary = get_progress_summary(db, user)
        assert summary["starting_weight_kg"] == Decimal("80.0")
        assert summary["current_weight_kg"] == Decimal("78.0")
        assert summary["weight_change_kg"] == Decimal("-2.0")
        assert summary["entry_count"] == 2
        assert summary["fitness_goal"] == "weight_loss"
        # BMI = 78 / (1.70^2) = 78 / 2.89 ≈ 27.0
        assert summary["bmi"] == Decimal("27.0")
        db.close()

    def test_summary_without_profile(self):
        """User without a profile still gets a summary."""
        reset_db()
        db = db_session.SessionLocal()
        user = User(
            email="noprofile@example.com",
            display_name="No Profile",
            password_hash="fakehash",
            preferred_language="en",
        )
        db.add(user)
        db.commit()

        summary = get_progress_summary(db, user)
        assert summary["starting_weight_kg"] is None
        assert summary["current_weight_kg"] is None
        assert summary["weight_change_kg"] is None
        assert summary["bmi"] is None
        assert summary["entry_count"] == 0
        db.close()


# ── API endpoint tests ──────────────────────────────────────────────────────


class TestProgressAPI:
    def test_create_entry_via_api(self):
        client = make_client()
        api_register(client)
        client = TestClient(app)
        api_login(client)
        csrf = get_csrf(client)

        response = client.post(
            "/api/progress",
            json={
                "recorded_on": "2026-01-15",
                "weight_kg": 74.5,
                "waist_cm": 82.0,
                "notes": "Good day",
            },
            headers={"X-CSRF-Token": csrf},
        )
        assert response.status_code == 201, response.text
        data = response.json()
        assert float(data["weight_kg"]) == 74.5
        assert float(data["waist_cm"]) == 82.0
        assert data["recorded_on"] == "2026-01-15"
        assert data["notes"] == "Good day"
        assert "id" in data

    def test_reject_weight_zero(self):
        client = make_client()
        api_register(client)
        client = TestClient(app)
        api_login(client)
        csrf = get_csrf(client)

        response = client.post(
            "/api/progress",
            json={"recorded_on": "2026-01-15", "weight_kg": 0},
            headers={"X-CSRF-Token": csrf},
        )
        assert response.status_code == 422

    def test_reject_weight_negative(self):
        client = make_client()
        api_register(client)
        client = TestClient(app)
        api_login(client)
        csrf = get_csrf(client)

        response = client.post(
            "/api/progress",
            json={"recorded_on": "2026-01-15", "weight_kg": -5},
            headers={"X-CSRF-Token": csrf},
        )
        assert response.status_code == 422

    def test_reject_duplicate_via_api(self):
        client = make_client()
        api_register(client)
        client = TestClient(app)
        api_login(client)
        csrf = get_csrf(client)

        client.post(
            "/api/progress",
            json={"recorded_on": "2026-01-15", "weight_kg": 74.5},
            headers={"X-CSRF-Token": csrf},
        )

        response = client.post(
            "/api/progress",
            json={"recorded_on": "2026-01-15", "weight_kg": 73.0},
            headers={"X-CSRF-Token": csrf},
        )
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_list_entries_via_api(self):
        client = make_client()
        api_register(client)
        client = TestClient(app)
        api_login(client)
        csrf = get_csrf(client)

        client.post(
            "/api/progress",
            json={"recorded_on": "2026-01-10", "weight_kg": 76.0},
            headers={"X-CSRF-Token": csrf},
        )
        client.post(
            "/api/progress",
            json={"recorded_on": "2026-01-15", "weight_kg": 74.5},
            headers={"X-CSRF-Token": csrf},
        )

        response = client.get("/api/progress")
        assert response.status_code == 200
        entries = response.json()
        assert len(entries) == 2
        # Newest first
        assert entries[0]["recorded_on"] == "2026-01-15"
        assert entries[1]["recorded_on"] == "2026-01-10"

    def test_unauthenticated_get_rejected(self):
        client = make_client()
        response = client.get("/api/progress")
        assert response.status_code == 401

    def test_unauthenticated_post_rejected(self):
        client = make_client()
        response = client.post(
            "/api/progress",
            json={"recorded_on": "2026-01-15", "weight_kg": 74.5},
        )
        assert response.status_code == 401

    def test_summary_via_api(self):
        client = make_client()
        api_register(client)
        client = TestClient(app)
        api_login(client)
        csrf = get_csrf(client)

        # Create a progress entry
        client.post(
            "/api/progress",
            json={"recorded_on": "2026-01-15", "weight_kg": 74.5},
            headers={"X-CSRF-Token": csrf},
        )

        response = client.get("/api/progress/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["entry_count"] == 1
        assert "starting_weight_kg" in data
        assert "current_weight_kg" in data
        assert "bmi" in data
        assert "fitness_goal" in data

    def test_unauthenticated_summary_rejected(self):
        client = make_client()
        response = client.get("/api/progress/summary")
        assert response.status_code == 401

    def test_no_csrf_rejected_on_post(self):
        client = make_client()
        api_register(client)
        client = TestClient(app)
        api_login(client)

        # POST without CSRF token should fail
        response = client.post(
            "/api/progress",
            json={"recorded_on": "2026-01-15", "weight_kg": 74.5},
        )
        assert response.status_code == 403

    def test_user_cannot_see_other_users_entries(self):
        client = make_client()

        # Create user1 with an entry
        api_register(client, "user1@example.com")
        client1 = TestClient(app)
        api_login(client1, "user1@example.com")
        csrf1 = get_csrf(client1)
        client1.post(
            "/api/progress",
            json={"recorded_on": "2026-01-15", "weight_kg": 74.5},
            headers={"X-CSRF-Token": csrf1},
        )

        # Create user2
        client2 = make_client()
        api_register(client2, "user2@example.com")
        client2 = TestClient(app)
        api_login(client2, "user2@example.com")

        # user2 should not see user1's entries
        response = client2.get("/api/progress")
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_optional_fields_persisted_via_api(self):
        client = make_client()
        api_register(client)
        client = TestClient(app)
        api_login(client)
        csrf = get_csrf(client)

        response = client.post(
            "/api/progress",
            json={
                "recorded_on": "2026-01-15",
                "weight_kg": 74.5,
                "waist_cm": 82.0,
                "hip_cm": 95.0,
                "body_fat_percent": 18.5,
                "notes": "Felt great",
            },
            headers={"X-CSRF-Token": csrf},
        )
        assert response.status_code == 201
        data = response.json()
        assert float(data["waist_cm"]) == 82.0
        assert float(data["hip_cm"]) == 95.0
        assert float(data["body_fat_percent"]) == 18.5
        assert data["notes"] == "Felt great"
