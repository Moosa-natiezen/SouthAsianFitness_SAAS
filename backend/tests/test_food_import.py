from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-1234567890abcdefg")
os.environ.setdefault("CSRF_SECRET_KEY", "test-csrf-secret-key-1234567890abcdef")
os.environ.setdefault("ENVIRONMENT", "testing")

from app.db import session as db_session
from app.db.base import Base
from app.models.food import Food, FoodIngredient, FoodPrice
from app.services.food_import_service import ImportValidationError, import_food_dataset
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


def reset_db() -> Session:
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


def test_import_food_dataset_creates_food_and_prices() -> None:
    db = reset_db()
    payload = {
        "foods": [
            {
                "name": "Chicken salan",
                "slug": "chicken-salan",
                "category": "prepared-meals",
                "food_type": "composite",
                "country": "PK",
                "regions": ["Punjab"],
                "nutrition": {
                    "calories": 420,
                    "protein_g": 32,
                    "carbs_g": 18,
                    "fat_g": 23,
                    "fiber_g": 3,
                },
                "serving": {"amount": 1, "unit": "serving", "grams_equivalent": 350},
                "ingredients": [
                    {"name": "chicken", "quantity": 180, "unit": "g"},
                    {"name": "onion", "quantity": 40, "unit": "g"},
                ],
                "prices": [
                    {
                        "country": "PK",
                        "region": "Punjab",
                        "currency": "PKR",
                        "amount": 540,
                        "quantity": 1,
                        "unit": "serving",
                        "observed_at": "2026-08-01T00:00:00+00:00",
                    }
                ],
            }
        ]
    }

    summary = import_food_dataset(db, payload)
    assert summary.imported == 1
    assert summary.failed == 0

    food = db.query(Food).filter(Food.slug == "chicken-salan").one()
    assert food.category is not None
    assert food.category.name == "prepared-meals"
    assert len(food.ingredients) == 2
    assert len(food.prices) == 1
    assert db.query(FoodPrice).count() == 1
    assert db.query(FoodIngredient).count() == 2
    db.close()


def test_invalid_record_is_rejected() -> None:
    db = reset_db()
    payload = {
        "foods": [
            {
                "name": "Bad food",
                "slug": "bad-food",
                "category": "grains",
                "food_type": "ingredient",
                "country": "PK",
                "nutrition": {
                    "calories": -1,
                    "protein_g": 0,
                    "carbs_g": 0,
                    "fat_g": 0,
                },
                "serving": {"amount": 100, "unit": "g", "grams_equivalent": 100},
                "ingredients": [],
                "prices": [],
            }
        ]
    }

    try:
        import_food_dataset(db, payload)
        raise AssertionError("expected validation error")
    except ImportValidationError:
        assert db.query(Food).count() == 0
    finally:
        db.close()


def test_dry_run_does_not_commit_changes() -> None:
    db = reset_db()
    payload = {
        "foods": [
            {
                "name": "Basmati rice",
                "slug": "basmati-rice",
                "category": "grains",
                "food_type": "ingredient",
                "country": "PK",
                "nutrition": {
                    "calories": 130,
                    "protein_g": 2.5,
                    "carbs_g": 28,
                    "fat_g": 0.4,
                },
                "serving": {"amount": 100, "unit": "g", "grams_equivalent": 100},
                "ingredients": [],
                "prices": [],
            }
        ]
    }

    summary = import_food_dataset(db, payload, dry_run=True)
    assert summary.imported == 1
    assert db.query(Food).count() == 0
    db.close()


def test_reimport_is_idempotent_for_duplicate_slug() -> None:
    db = reset_db()
    payload = {
        "foods": [
            {
                "name": "Daal",
                "slug": "daal",
                "category": "prepared-meals",
                "food_type": "composite",
                "country": "PK",
                "nutrition": {
                    "calories": 210,
                    "protein_g": 15,
                    "carbs_g": 25,
                    "fat_g": 4,
                },
                "serving": {"amount": 1, "unit": "serving", "grams_equivalent": 250},
                "ingredients": [
                    {"name": "lentils", "quantity": 100, "unit": "g"},
                ],
                "prices": [],
            }
        ]
    }

    first = import_food_dataset(db, payload)
    second = import_food_dataset(db, payload)
    assert first.imported == 1
    assert second.skipped == 1
    assert db.query(Food).count() == 2
    assert db.query(Food).filter(Food.slug == "lentils").count() == 1
    db.close()


def test_import_with_per_record_source() -> None:
    """Verify per-record source provenance fields are persisted."""
    db = reset_db()
    payload = {
        "foods": [
            {
                "name": "Basmati Rice",
                "slug": "basmati-rice-provenance",
                "category": "grains",
                "food_type": "ingredient",
                "country": "IN",
                "nutrition": {
                    "calories": 130,
                    "protein_g": 2.7,
                    "carbs_g": 28.2,
                    "fat_g": 0.3,
                },
                "serving": {"amount": 100, "unit": "g", "grams_equivalent": 100},
                "ingredients": [],
                "prices": [],
                "source": {
                    "source_name": "USDA FoodData Central",
                    "source_identifier": "FDC-169705",
                    "source_version": "SR Legacy",
                    "source_date": "2024-06-01T00:00:00+00:00",
                    "verification_status": "pending_review",
                    "notes": "Imported from USDA",
                },
            }
        ]
    }

    summary = import_food_dataset(db, payload)
    assert summary.imported == 1
    assert summary.failed == 0

    food = db.query(Food).filter(Food.slug == "basmati-rice-provenance").one()
    assert food.source_identifier == "FDC-169705"
    assert food.source_version == "SR Legacy"
    assert food.verification_status.value == "pending_review"
    assert food.imported_at is not None
    assert food.source is not None
    assert food.source.name == "USDA FoodData Central"
    assert food.source.version == "SR Legacy"
    db.close()


def test_import_with_dataset_level_source() -> None:
    """Verify dataset-level source metadata applies to all foods."""
    db = reset_db()
    payload = {
        "dataset_source": {
            "name": "ICMR-NIN IFCT",
            "version": "2017",
            "license_category": "open_data",
            "can_store_raw_data": False,
            "can_store_derived_values": True,
            "source_date": "2017-01-01T00:00:00+00:00",
        },
        "foods": [
            {
                "name": "Chickpeas",
                "slug": "chickpeas-ifct",
                "category": "legumes",
                "food_type": "ingredient",
                "country": "IN",
                "nutrition": {
                    "calories": 164,
                    "protein_g": 8.9,
                    "carbs_g": 27.4,
                    "fat_g": 2.6,
                },
                "serving": {"amount": 100, "unit": "g", "grams_equivalent": 100},
                "ingredients": [],
                "prices": [],
            }
        ],
    }

    summary = import_food_dataset(db, payload)
    assert summary.imported == 1

    food = db.query(Food).filter(Food.slug == "chickpeas-ifct").one()
    assert food.source is not None
    assert food.source.name == "ICMR-NIN IFCT"
    assert food.source.version == "2017"
    assert food.source.license_category.value == "open_data"
    assert food.source.can_store_raw_data is False
    assert food.source.can_store_derived_values is True
    assert food.verification_status.value == "unverified"
    db.close()


def test_per_record_source_overrides_dataset_source() -> None:
    """Per-record source should take precedence over dataset-level source."""
    db = reset_db()
    payload = {
        "dataset_source": {
            "name": "USDA FoodData Central",
            "version": "2024",
            "license_category": "public_domain",
        },
        "foods": [
            {
                "name": "Special Rice",
                "slug": "special-rice-overrides",
                "category": "grains",
                "food_type": "ingredient",
                "country": "IN",
                "nutrition": {
                    "calories": 130,
                    "protein_g": 2.7,
                    "carbs_g": 28.2,
                    "fat_g": 0.3,
                },
                "serving": {"amount": 100, "unit": "g", "grams_equivalent": 100},
                "ingredients": [],
                "prices": [],
                "source": {
                    "source_name": "ICMR-NIN IFCT",
                    "source_identifier": "IFCT-CUSTOM-001",
                    "source_version": "2017",
                    "verification_status": "verified",
                },
            }
        ],
    }

    summary = import_food_dataset(db, payload)
    assert summary.imported == 1

    food = db.query(Food).filter(Food.slug == "special-rice-overrides").one()
    assert food.source.name == "ICMR-NIN IFCT"
    assert food.source_identifier == "IFCT-CUSTOM-001"
    assert food.verification_status.value == "verified"
    db.close()


def test_food_source_created_once_per_name_version() -> None:
    """Multiple foods from the same source should share one FoodSource record."""
    from app.models.food_source import FoodSource

    db = reset_db()
    payload = {
        "dataset_source": {
            "name": "Shared Source",
            "version": "1.0",
        },
        "foods": [
            {
                "name": "Food A",
                "slug": "food-a-shared",
                "category": "grains",
                "food_type": "ingredient",
                "country": "PK",
                "nutrition": {"calories": 100, "protein_g": 5, "carbs_g": 20, "fat_g": 1},
                "serving": {"amount": 100, "unit": "g", "grams_equivalent": 100},
                "ingredients": [],
                "prices": [],
            },
            {
                "name": "Food B",
                "slug": "food-b-shared",
                "category": "legumes",
                "food_type": "ingredient",
                "country": "PK",
                "nutrition": {"calories": 120, "protein_g": 8, "carbs_g": 18, "fat_g": 2},
                "serving": {"amount": 100, "unit": "g", "grams_equivalent": 100},
                "ingredients": [],
                "prices": [],
            },
        ],
    }

    summary = import_food_dataset(db, payload)
    assert summary.imported == 2

    # Both foods should share the same FoodSource
    sources = db.query(FoodSource).all()
    assert len(sources) == 1
    assert sources[0].name == "Shared Source"
    assert sources[0].version == "1.0"

    food_a = db.query(Food).filter(Food.slug == "food-a-shared").one()
    food_b = db.query(Food).filter(Food.slug == "food-b-shared").one()
    assert food_a.food_source_id == food_b.food_source_id
    db.close()
