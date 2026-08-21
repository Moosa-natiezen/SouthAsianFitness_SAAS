"""Tests for the verified food filter service.

Covers: eligibility rules, status filtering, and production import safety.
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-1234567890abcdefg")
os.environ.setdefault("CSRF_SECRET_KEY", "test-csrf-secret-key-1234567890abcdef")
os.environ.setdefault("ENVIRONMENT", "testing")

from app import models as app_models  # noqa: F401
from app.db import session as db_session
from app.db.base import Base
from app.models.enums import UnitDimension, VerificationStatus
from app.models.food import Food
from app.models.tags import FoodCategory
from app.models.unit import Unit
from app.services.food_filter_service import (
    ELIGIBLE_STATUSES,
    EXCLUDED_STATUSES,
    count_eligible_foods,
    get_eligible_food_slugs,
    get_verified_foods,
    is_food_eligible,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


def reset_db():
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
    return engine


def seed_food(db: Session, slug: str, name: str, status: VerificationStatus):
    """Helper to create a food with given verification status."""
    if not db.query(Unit).first():
        unit = Unit(code="g", name="gram", dimension=UnitDimension.MASS, to_base_factor=1)
        db.add(unit)
    if not db.query(FoodCategory).first():
        cat = FoodCategory(name="test", slug="test")
        db.add(cat)
    db.flush()

    unit = db.query(Unit).first()
    cat = db.query(FoodCategory).first()

    food = Food(
        slug=slug,
        name=name,
        category_id=cat.id,
        serving_size=100,
        serving_unit_id=unit.id,
        grams_per_serving=100,
        calories=100,
        protein_g=5,
        carbs_g=15,
        fat_g=3,
        is_active=True,
        verification_status=status,
    )
    db.add(food)
    db.commit()
    return food


class TestEligibleStatuses:
    def test_verified_is_eligible(self):
        assert VerificationStatus.VERIFIED in ELIGIBLE_STATUSES

    def test_verified_with_notes_is_eligible(self):
        assert VerificationStatus.VERIFIED_WITH_NOTES in ELIGIBLE_STATUSES

    def test_pending_review_is_excluded(self):
        assert VerificationStatus.PENDING_REVIEW in EXCLUDED_STATUSES

    def test_rejected_is_excluded(self):
        assert VerificationStatus.REJECTED in EXCLUDED_STATUSES

    def test_unverified_is_excluded(self):
        assert VerificationStatus.UNVERIFIED in EXCLUDED_STATUSES

    def test_conflict_is_excluded(self):
        assert VerificationStatus.CONFLICT in EXCLUDED_STATUSES

    def test_eligible_and_excluded_are_disjoint(self):
        assert ELIGIBLE_STATUSES.isdisjoint(EXCLUDED_STATUSES)


class TestFoodEligibility:
    def test_verified_food_is_eligible(self):
        reset_db()
        db = db_session.SessionLocal()
        food = seed_food(db, "test-verified", "Test Verified", VerificationStatus.VERIFIED)
        assert is_food_eligible(food)
        db.close()

    def test_verified_with_notes_is_eligible(self):
        reset_db()
        db = db_session.SessionLocal()
        food = seed_food(db, "test-notes", "Test Notes", VerificationStatus.VERIFIED_WITH_NOTES)
        assert is_food_eligible(food)
        db.close()

    def test_pending_review_food_not_eligible(self):
        reset_db()
        db = db_session.SessionLocal()
        food = seed_food(db, "test-pending", "Test Pending", VerificationStatus.PENDING_REVIEW)
        assert not is_food_eligible(food)
        db.close()

    def test_inactive_food_not_eligible(self):
        reset_db()
        db = db_session.SessionLocal()
        food = seed_food(db, "test-inactive", "Test Inactive", VerificationStatus.VERIFIED)
        food.is_active = False
        assert not is_food_eligible(food)
        db.close()

    def test_rejected_food_not_eligible(self):
        reset_db()
        db = db_session.SessionLocal()
        food = seed_food(db, "test-rejected", "Test Rejected", VerificationStatus.REJECTED)
        assert not is_food_eligible(food)
        db.close()


class TestGetVerifiedFoods:
    def test_only_returns_verified(self):
        reset_db()
        db = db_session.SessionLocal()
        seed_food(db, "v1", "Verified 1", VerificationStatus.VERIFIED)
        seed_food(db, "v2", "Verified 2", VerificationStatus.VERIFIED_WITH_NOTES)
        seed_food(db, "p1", "Pending 1", VerificationStatus.PENDING_REVIEW)
        seed_food(db, "r1", "Rejected 1", VerificationStatus.REJECTED)

        foods, total = get_verified_foods(db)
        assert total == 2
        slugs = {f.slug for f in foods}
        assert slugs == {"v1", "v2"}
        db.close()

    def test_count_matches(self):
        reset_db()
        db = db_session.SessionLocal()
        seed_food(db, "c1", "Food 1", VerificationStatus.VERIFIED)
        seed_food(db, "c2", "Food 2", VerificationStatus.VERIFIED)
        seed_food(db, "c3", "Food 3", VerificationStatus.PENDING_REVIEW)

        count = count_eligible_foods(db)
        assert count == 2
        db.close()

    def test_eligible_slugs(self):
        reset_db()
        db = db_session.SessionLocal()
        seed_food(db, "s1", "Slug 1", VerificationStatus.VERIFIED)
        seed_food(db, "s2", "Slug 2", VerificationStatus.PENDING_REVIEW)

        slugs = get_eligible_food_slugs(db)
        assert "s1" in slugs
        assert "s2" not in slugs
        db.close()


class TestProductionImportSafety:
    """Ensure the filter correctly separates verified from non-verified."""

    def test_mixed_statuses_correctly_filtered(self):
        reset_db()
        db = db_session.SessionLocal()
        statuses = [
            ("f1", "Verified A", VerificationStatus.VERIFIED),
            ("f2", "Verified B", VerificationStatus.VERIFIED_WITH_NOTES),
            ("f3", "Pending A", VerificationStatus.PENDING_REVIEW),
            ("f4", "Pending B", VerificationStatus.PENDING_REVIEW),
            ("f5", "Unverified", VerificationStatus.UNVERIFIED),
            ("f6", "Conflict", VerificationStatus.CONFLICT),
            ("f7", "Retracted", VerificationStatus.RETRACTED),
            ("f8", "Rejected", VerificationStatus.REJECTED),
        ]
        for slug, name, status in statuses:
            seed_food(db, slug, name, status)

        eligible, total = get_verified_foods(db)
        assert total == 2
        assert len(eligible) == 2
        assert count_eligible_foods(db) == 2
        db.close()
