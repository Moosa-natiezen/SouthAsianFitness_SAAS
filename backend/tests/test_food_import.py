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
