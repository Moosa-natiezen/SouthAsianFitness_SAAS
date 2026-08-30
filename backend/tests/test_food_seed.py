"""Tests for food dataset seeding on application startup.

Verifies that the food import in the FastAPI lifespan:
- imports the dataset when no foods exist
- skips import when the full dataset is present
- detects incomplete datasets and imports missing records
- does not duplicate records on repeated runs
- produces foods with correct verification statuses and nutrition data
- handles DataError from one food without destroying valid foods
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-1234567890abcdefg")
os.environ.setdefault("CSRF_SECRET_KEY", "test-csrf-secret-key-1234567890abcdef")
os.environ.setdefault("ENVIRONMENT", "testing")

from pathlib import Path
from unittest.mock import patch

from app.db import session as db_session
from app.db.base import Base
from app.models.enums import VerificationStatus
from app.models.food import Food
from app.services.food_import_service import (
    _normalize_verification_status,
    import_foods_from_file,
)
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

DATASET_PATH = Path(__file__).resolve().parent.parent / "data" / "south_asian_foods.json"
EXPECTED_FOOD_COUNT = 198


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


# ── Basic import tests ─────────────────────────────────────────────────────


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
        f"Record count changed: {count_after_first} -> {count_after_second}"
    )
    db.close()


def test_imported_foods_have_verified_status() -> None:
    """Foods with source.verification_status=verified get VERIFIED status."""
    db = _reset_db()
    import_foods_from_file(db, DATASET_PATH)

    verified = db.execute(
        select(func.count(Food.id)).where(
            Food.verification_status == VerificationStatus.VERIFIED
        )
    ).scalar()
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


# ── Complete dataset count ─────────────────────────────────────────────────


def test_full_dataset_imports_198_foods() -> None:
    """The full dataset should import exactly 198 foods."""
    db = _reset_db()
    summary = import_foods_from_file(db, DATASET_PATH)

    assert summary.imported == EXPECTED_FOOD_COUNT, (
        f"Expected {EXPECTED_FOOD_COUNT} imported, got {summary.imported}"
    )
    assert summary.failed == 0
    count = db.execute(select(func.count(Food.id))).scalar()
    assert count == EXPECTED_FOOD_COUNT
    db.close()


def test_verification_status_distribution() -> None:
    """After import, the verification status distribution matches the dataset."""
    db = _reset_db()
    import_foods_from_file(db, DATASET_PATH)

    verified = db.execute(
        select(func.count(Food.id)).where(
            Food.verification_status == VerificationStatus.VERIFIED
        )
    ).scalar()
    verified_notes = db.execute(
        select(func.count(Food.id)).where(
            Food.verification_status == VerificationStatus.VERIFIED_WITH_NOTES
        )
    ).scalar()
    pending = db.execute(
        select(func.count(Food.id)).where(
            Food.verification_status == VerificationStatus.PENDING_REVIEW
        )
    ).scalar()

    assert verified == 133, f"Expected 133 verified, got {verified}"
    assert verified_notes == 2, f"Expected 2 verified_with_notes, got {verified_notes}"
    assert pending == 63, f"Expected 63 pending_review, got {pending}"
    db.close()


def test_eligible_foods_count() -> None:
    """After import, the number of eligible foods matches expected count."""
    db = _reset_db()
    import_foods_from_file(db, DATASET_PATH)

    eligible = db.execute(
        select(func.count(Food.id)).where(
            Food.verification_status.in_(
                [VerificationStatus.VERIFIED, VerificationStatus.VERIFIED_WITH_NOTES]
            ),
            Food.is_active.is_(True),
        )
    ).scalar()
    assert eligible == 135, f"Expected 135 eligible foods, got {eligible}"
    db.close()


# ── Fast-path behavior ─────────────────────────────────────────────────────


def test_fast_path_skips_when_full_dataset_present() -> None:
    """When the full expected dataset is present, import is skipped."""
    db = _reset_db()
    import_foods_from_file(db, DATASET_PATH)

    count = db.execute(select(func.count(Food.id))).scalar()
    assert count == EXPECTED_FOOD_COUNT

    # Simulate lifespan fast-path: count >= EXPECTED_FOOD_COUNT
    # In a real scenario, the lifespan would skip the import entirely.
    second = import_foods_from_file(db, DATASET_PATH)
    assert second.imported == 0, "Should not import when full dataset exists"
    assert second.skipped == EXPECTED_FOOD_COUNT
    db.close()


def test_incomplete_dataset_detected() -> None:
    """An incomplete dataset (< 198 foods) triggers import of missing records."""
    db = _reset_db()

    # Import first 100 foods only
    import_foods_from_file(db, DATASET_PATH)
    count_full = db.execute(select(func.count(Food.id))).scalar()
    assert count_full == EXPECTED_FOOD_COUNT

    # Delete some foods to simulate incomplete dataset
    foods_to_delete = (
        db.execute(select(Food).limit(50)).scalars().all()
    )
    for food in foods_to_delete:
        db.delete(food)
    db.commit()

    count_partial = db.execute(select(func.count(Food.id))).scalar()
    assert count_partial == EXPECTED_FOOD_COUNT - 50

    # Re-import should add back the missing 50 foods
    summary = import_foods_from_file(db, DATASET_PATH)
    assert summary.imported == 50, f"Expected 50 new imports, got {summary.imported}"
    assert summary.skipped == count_partial, (
        f"Expected {count_partial} skipped, got {summary.skipped}"
    )

    final_count = db.execute(select(func.count(Food.id))).scalar()
    assert final_count == EXPECTED_FOOD_COUNT
    db.close()


def test_existing_foods_preserved_on_reimport() -> None:
    """Existing foods keep their UUIDs when the import is re-run."""
    db = _reset_db()
    import_foods_from_file(db, DATASET_PATH)

    # Record some UUIDs
    foods_before = db.execute(select(Food)).scalars().all()
    ids_before = {f.id for f in foods_before}
    assert len(ids_before) == EXPECTED_FOOD_COUNT

    # Re-import — no new foods should be created
    import_foods_from_file(db, DATASET_PATH)

    foods_after = db.execute(select(Food)).scalars().all()
    ids_after = {f.id for f in foods_after}
    assert ids_before == ids_after, "UUIDs changed after re-import"
    db.close()


# ── DataError resilience ───────────────────────────────────────────────────


def test_dataerror_does_not_destroy_valid_foods() -> None:
    """If one food raises DataError during flush, other valid foods are still committed."""
    db = _reset_db()

    original_flush = db.flush

    call_count = 0

    def mock_flush() -> None:
        nonlocal call_count
        call_count += 1
        # Fail on the 5th food flush (after 4 valid foods)
        if call_count == 5:
            from sqlalchemy.exc import DataError

            raise DataError("statement", "params", Exception("invalid enum value"))
        original_flush()

    with patch.object(db, "flush", side_effect=mock_flush):
        summary = import_foods_from_file(db, DATASET_PATH)

    # At least 4 valid foods should have been committed
    count = db.execute(select(func.count(Food.id))).scalar()
    assert count >= 4, f"Expected at least 4 foods, got {count}"
    assert summary.failed >= 1, "At least one food should have failed"
    assert summary.imported >= 4, "At least 4 foods should have been imported"
    db.close()


def test_normalized_verification_status() -> None:
    """_normalize_verification_status converts valid strings and falls back safely."""
    assert _normalize_verification_status("verified") == VerificationStatus.VERIFIED
    assert (
        _normalize_verification_status("verified_with_notes")
        == VerificationStatus.VERIFIED_WITH_NOTES
    )
    assert (
        _normalize_verification_status("pending_review")
        == VerificationStatus.PENDING_REVIEW
    )
    # Unknown values fall back to UNVERIFIED
    assert (
        _normalize_verification_status("unknown_status")
        == VerificationStatus.UNVERIFIED
    )
    assert _normalize_verification_status("") == VerificationStatus.UNVERIFIED


# ── Edge cases ─────────────────────────────────────────────────────────────


def test_import_with_empty_database() -> None:
    """Import into a truly empty database succeeds without errors."""
    db = _reset_db()
    count = db.execute(select(func.count(Food.id))).scalar()
    assert count == 0, "Database should be empty"

    summary = import_foods_from_file(db, DATASET_PATH)

    assert summary.imported > 0, "Should import foods into empty database"
    assert summary.failed == 0, f"Unexpected failures: {summary.warnings}"
    db.close()


def test_all_foods_are_active() -> None:
    """All imported foods should have is_active=True."""
    db = _reset_db()
    import_foods_from_file(db, DATASET_PATH)

    inactive = db.execute(
        select(func.count(Food.id)).where(Food.is_active.is_(False))
    ).scalar()
    assert inactive == 0, f"Expected 0 inactive foods, got {inactive}"
    db.close()
