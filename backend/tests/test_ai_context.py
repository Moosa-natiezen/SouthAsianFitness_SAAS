"""Tests for AI context management (UserAIContext + get_user_ai_context).

Covers:
- UserAIContext.format_for_prompt() output rendering
- get_user_ai_context() population from the database
- Dietary preference / allergy separation by tag kind
- Goal vocabulary mapping (cutting / maintenance / bulking)
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-1234567890abcdefg")
os.environ.setdefault("CSRF_SECRET_KEY", "test-csrf-secret-key-1234567890abcdef")
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("DEBUG", "false")

import importlib

from app.core.config import get_settings

get_settings.cache_clear()
import app.core.config

importlib.reload(app.core.config)

from app import models as app_models  # noqa: F401
from app.db import session as db_session
from app.db.base import Base
from app.models.enums import (
    ActivityLevel,
    DietaryTagKind,
    DietPattern,
    FitnessGoal,
    Sex,
)
from app.models.tags import DietaryTag
from app.models.user import User, UserPreferences, UserProfile
from app.schemas.ai_context import UserAIContext
from app.services.ai_context_service import get_user_ai_context
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


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


def _make_user(
    *,
    email: str = "ctx_test@example.com",
    fitness_goal: FitnessGoal = FitnessGoal.WEIGHT_LOSS,
    diet_pattern: DietPattern = DietPattern.OMNIVORE,
    target_calories: int = 2000,
    target_protein_g: float = 120.0,
) -> User:
    """Create a user with a fully-populated profile and preferences."""
    db = db_session.SessionLocal()
    try:
        user = User(
            email=email,
            display_name="Context Test",
            password_hash="x",
        )
        db.add(user)
        db.flush()

        profile = UserProfile(
            user_id=user.id,
            age_years=28,
            sex=Sex.MALE,
            height_cm=175,
            weight_kg=72,
            activity_level=ActivityLevel.MODERATELY_ACTIVE,
            fitness_goal=fitness_goal,
            diet_pattern=diet_pattern,
            target_calories=target_calories,
            target_protein_g=target_protein_g,
        )
        db.add(profile)

        prefs = UserPreferences(user_id=user.id)
        db.add(prefs)
        db.flush()

        # Dietary preference tag (e.g. "halal") + allergen tag (e.g. "peanuts")
        # Idempotent: reuse existing tags when re-creating users in one DB.
        halal = db.query(DietaryTag).filter(DietaryTag.slug == "halal").first()
        if halal is None:
            halal = DietaryTag(
                slug="halal",
                name="Halal",
                kind=DietaryTagKind.RESTRICTION,
            )
            db.add(halal)
            db.flush()
        peanuts = db.query(DietaryTag).filter(DietaryTag.slug == "peanuts").first()
        if peanuts is None:
            peanuts = DietaryTag(
                slug="peanuts",
                name="Peanuts",
                kind=DietaryTagKind.ALLERGEN,
            )
            db.add(peanuts)
            db.flush()

        prefs.dietary_tags.append(halal)
        prefs.dietary_tags.append(peanuts)

        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def _fetch_context(user_id) -> UserAIContext | None:
    db = db_session.SessionLocal()
    try:
        return get_user_ai_context(user_id, db)
    finally:
        db.close()


# ── Model rendering tests ────────────────────────────────────────────────


def test_format_for_prompt_full_context():
    """Verify a fully-populated context renders a clean prompt block."""
    ctx = UserAIContext(
        user_id="11111111-1111-1111-1111-111111111111",
        target_calories=2000,
        target_protein=120,
        dietary_preferences=["halal", "vegetarian"],
        allergies=["peanuts"],
        current_goal="cutting",
        activity_level="moderately_active",
        sex="male",
        age_years=28,
        height_cm=175,
        weight_kg=72,
    )

    block = ctx.format_for_prompt()

    assert "whose current goal is cutting" in block
    assert "targeting 2000 calories/day" in block
    assert "120g protein/day" in block
    assert "halal, vegetarian" in block
    assert "NEVER suggest" in block
    assert "peanuts" in block
    assert "28 years old" in block
    assert "moderately_active activity level" in block


def test_format_for_prompt_minimal_context():
    """Verify an empty context degrades gracefully without crashing."""
    ctx = UserAIContext(user_id="11111111-1111-1111-1111-111111111111")

    block = ctx.format_for_prompt()

    # No headline (no goal/targets), no errors
    assert "You are helping a user" not in block
    assert block == ""


# ── Database injector tests ──────────────────────────────────────────────


def test_get_user_ai_context_populates_profile():
    """Verify the injector reads profile, tags, and targets from the DB."""
    reset_db()
    user = _make_user()
    ctx = _fetch_context(user.id)

    assert ctx is not None
    assert ctx.user_id == user.id
    assert ctx.target_calories == 2000
    assert ctx.target_protein == 120.0
    assert ctx.current_goal == "cutting"  # WEIGHT_LOSS → cutting
    assert "halal" in ctx.dietary_preferences
    assert "peanuts" in ctx.allergies
    assert "peanuts" not in ctx.dietary_preferences
    assert ctx.activity_level == "moderately_active"
    assert ctx.age_years == 28
    assert ctx.height_cm == 175
    assert ctx.weight_kg == 72


def test_get_user_ai_context_diet_pattern_included():
    """Verify the diet pattern (e.g. vegetarian) is added to preferences."""
    reset_db()
    user = _make_user(diet_pattern=DietPattern.VEGETARIAN)
    ctx = _fetch_context(user.id)

    assert ctx is not None
    assert "vegetarian" in ctx.dietary_preferences


def test_get_user_ai_context_goal_mapping():
    """Verify fitness goals map to the friendly vocabulary."""
    reset_db()
    maintain_user = _make_user(
        email="maintain@example.com",
        fitness_goal=FitnessGoal.GENERAL_FITNESS,
    )
    bulk_user = _make_user(
        email="bulk@example.com",
        fitness_goal=FitnessGoal.MUSCLE_BUILDING,
    )

    maintain_ctx = _fetch_context(maintain_user.id)
    bulk_ctx = _fetch_context(bulk_user.id)

    assert maintain_ctx is not None
    assert maintain_ctx.current_goal == "maintenance"
    assert bulk_ctx is not None
    assert bulk_ctx.current_goal == "bulking"


def test_get_user_ai_context_missing_user():
    """Verify a missing user returns None instead of raising."""
    reset_db()
    ctx = _fetch_context("99999999-9999-9999-9999-999999999999")
    assert ctx is None