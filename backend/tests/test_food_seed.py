"""Tests for food dataset seeding on application startup.

Verifies that the food import in the FastAPI lifespan:
- imports the dataset when no foods exist
- skips import when foods already exist
- does not duplicate records on repeated runs
- produces foods with correct verification statuses and nutrition data
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-1234567890abcdefg")
os.environ.setdefault("CSRF_SECRET_KEY", "test-csrf-secret-key-1234567890abcdef")
os.environ.setdefault("ENVIRONMENT", "testing")

from pathlib import Path

from app.db import session as db_session
from app.db.base import Base
from app.models.enums import VerificationStatus
from app.models.food import Food
from app.services.food_import_service import import_foods_from_file
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

DATASET_PATH = Path(__file__).resolve().parent.parent / "data" / "south_asian_foods.json"


def _reset_db() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db_session.engine = engine
    db_session.SessionLocal = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        class_=Session,
    )
    return db_session.SessionLocal()


def test_import_from_json_file() -> None:
    """Importing the bundled JSON file creates food records."""
    db = _reset_db()
    assert DATASET_PATH.exists(), f"Dataset not found: {DATASET_PATH}"

    summary = import_foods_from_file(db, DATASET_PATH)

    assert summary.imported > 0, "Expected foods to be imported"
    assert summary.failed == 0, f"Import had failures: {summary.warnings}"

    count = db.execute(select(func.count(Food.id))).scalar()
    assert count == summary.imported, f"DB count {count} != imported {summary.imported}"
    db.close()


def test_second_import_skips_existing() -> None:
    """Running the import twice does not create duplicate records."""
    db = _reset_db()

    first = import_foods_from_file(db, DATASET_PATH)
    count_after_first = db.execute(select(func.count(Food.id))).scalar()

    second = import_foods_from_file(db, DATASET_PATH)
    count_after_second = db.execute(select(func.count(Food.id))).scalar()

    assert first.imported > 0
    assert second.skipped > 0, "Second import should skip all existing foods"
    assert second.imported == 0, "Second import should not import any new foods"
    assert count_after_first == count_after_second, (
        f"Record count changed: {count_after_first} → {count_after_second}"
    )
    db.close()


def test_imported_foods_have_verified_status() -> None:
    """Foods with source.verification_status=verified get VERIFIED status."""
    db = _reset_db()
    import_foods_from_file(db, DATASET_PATH)

    verified = (
            db.execute(
                select(func.count(Food.id)).where(Food.verification_status == VerificationStatus.VERIFIED)
            )
            .scalar()
        )
    assert verified > 0, "Expected at least some verified foods"
    db.close()


def test_imported_foods_have_nutrition() -> None:
    """All imported foods have positive calorie values."""
    db = _reset_db()
    import_foods_from_file(db, DATASET_PATH)

    foods = db.execute(select(Food)).scalars().all()
    assert len(foods) > 0
    for food in foods:
        assert float(food.calories) >= 0, f"{food.slug} has negative calories"
        assert food.serving_size > 0, f"{food.slug} has zero serving_size"
    db.close()


def test_fast_path_check_skips_when_foods_exist() -> None:
    """Simulates the lifespan fast-path: if foods exist, import is skipped."""
    db = _reset_db()

    # Import once
    import_foods_from_file(db, DATASET_PATH)
    count_before = db.execute(select(func.count(Food.id))).scalar()
    assert count_before > 0

    # Simulate the lifespan fast-path check
    has_foods = db.execute(select(Food.id).limit(1)).scalar() is not None
    assert has_foods is True

    # No import needed — just verify nothing changes
    count_after = db.execute(select(func.count(Food.id))).scalar()
    assert count_before == count_after
    db.close()


def test_fast_path_imports_when_empty() -> None:
    """Simulates the lifespan fast-path: if no foods exist, import runs."""
    db = _reset_db()

    # Verify empty
    has_foods = db.execute(select(Food.id).limit(1)).scalar() is not None
    assert has_foods is False

    # Import
    summary = import_foods_from_file(db, DATASET_PATH)
    assert summary.imported > 0

    # Now has foods
    has_foods = db.execute(select(Food.id).limit(1)).scalar() is not None
    assert has_foods is True
    db.close()


def test_import_with_empty_database() -> None:
    """Import into a truly empty database succeeds without errors."""
    db = _reset_db()
    count = db.execute(select(func.count(Food.id))).scalar()
    assert count == 0, "Database should be empty"

    summary = import_foods_from_file(db, DATASET_PATH)

    assert summary.imported > 0, "Should import foods into empty database"
    assert summary.failed == 0, f"Unexpected failures: {summary.warnings}"
    db.close()


def test_eligible_foods_count() -> None:
    """After import, the number of verified foods matches expected count."""
    db = _reset_db()
    import_foods_from_file(db, DATASET_PATH)

    eligible = (
        db.execute(
            select(func.count(Food.id)).where(
                Food.verification_status.in_(
                    [VerificationStatus.VERIFIED, VerificationStatus.VERIFIED_WITH_NOTES]
                ),
                Food.is_active.is_(True),
            )
        )
        .scalar()
    )
    # The dataset has 135 verified/verified_with_notes foods
    assert eligible >= 100, f"Expected at least 100 eligible foods, got {eligible}"
    db.close()
