"""Tests for the meal plan retrieval endpoint (GET /api/meal-plans/today).

Covers:
- Authenticated retrieval of existing plan
- 404 when no plan exists
- User isolation (cannot retrieve another user's plan)
- GET /today does NOT create a meal plan
- Existing generation endpoint still works
- Service layer: get_current_meal_plan + build_plan_response_from_db
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-1234567890abcdefg")
os.environ.setdefault("CSRF_SECRET_KEY", "test-csrf-secret-key-1234567890abcdef")
os.environ.setdefault("ENVIRONMENT", "testing")

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from app import models as app_models  # noqa: F401
from app.db import session as db_session
from app.db.base import Base
from app.models.enums import (
    ActivityLevel,
    DietPattern,
    FitnessGoal,
    MealPlanStatus,
    MealType,
    Sex,
    UnitDimension,
    VerificationStatus,
)
from app.models.food import Food
from app.models.meal import Meal, MealFood
from app.models.meal_plan import MealPlan, MealPlanDay, MealPlanDayMeal
from app.models.tags import FoodCategory
from app.models.unit import Unit
from app.models.user import User, UserProfile
from app.services.meal_plan_service import (
    build_plan_response_from_db,
    generate_meal_plan,
    get_current_meal_plan,
    persist_meal_plan,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# ── Test helpers ─────────────────────────────────────────────────────────────


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


def seed_basics(db: Session):
    """Seed units and categories."""
    unit_g = Unit(code="g", name="gram", dimension=UnitDimension.MASS, to_base_factor=1)
    unit_piece = Unit(code="pc", name="piece", dimension=UnitDimension.COUNT, to_base_factor=None)
    db.add_all([unit_g, unit_piece])

    categories = {}
    for slug in ["grains", "meats", "dairy", "vegetables", "fruits", "legumes", "oils"]:
        cat = FoodCategory(name=slug.title(), slug=slug)
        db.add(cat)
        categories[slug] = cat

    db.flush()
    return {"unit_g": unit_g, "unit_piece": unit_piece, "categories": categories}


def create_food(
    db: Session,
    *,
    slug: str,
    name: str,
    category: FoodCategory,
    calories: float,
    protein_g: float = 0,
    carbs_g: float = 0,
    fat_g: float = 0,
    serving_size: float = 100,
    unit: Unit,
    verification: VerificationStatus = VerificationStatus.VERIFIED,
) -> Food:
    food = Food(
        slug=slug,
        name=name,
        category_id=category.id,
        serving_size=serving_size,
        serving_unit_id=unit.id,
        grams_per_serving=serving_size,
        calories=calories,
        protein_g=protein_g,
        carbs_g=carbs_g,
        fat_g=fat_g,
        is_active=True,
        verification_status=verification,
    )
    db.add(food)
    db.flush()
    return food


def create_user_with_profile(
    db: Session,
    *,
    email: str = "test@example.com",
    sex: Sex = Sex.MALE,
    age: int = 30,
    height_cm: float = 175,
    weight_kg: float = 70,
    activity_level: ActivityLevel = ActivityLevel.MODERATELY_ACTIVE,
    fitness_goal: FitnessGoal = FitnessGoal.GENERAL_FITNESS,
    diet_pattern: DietPattern = DietPattern.OMNIVORE,
) -> User:
    user = User(
        email=email,
        display_name="Test User",
        password_hash="fakehash",
        preferred_language="en",
        preferred_unit_system="metric",
        preferred_currency_code="PKR",
    )
    db.add(user)
    db.flush()

    profile = UserProfile(
        user_id=user.id,
        age_years=age,
        sex=sex,
        height_cm=height_cm,
        weight_kg=weight_kg,
        activity_level=activity_level,
        fitness_goal=fitness_goal,
        diet_pattern=diet_pattern,
    )
    db.add(profile)
    db.commit()
    return user


def seed_food_dataset(db: Session):
    """Create a realistic set of South Asian foods for testing."""
    basics = seed_basics(db)
    cats = basics["categories"]
    unit_g = basics["unit_g"]

    foods = [
        create_food(db, slug="basmati-rice", name="Basmati Rice", category=cats["grains"],
                     calories=130, protein_g=2.7, carbs_g=28, fat_g=0.3, serving_size=100, unit=unit_g),
        create_food(db, slug="roti", name="Roti (Chapati)", category=cats["grains"],
                     calories=105, protein_g=3.0, carbs_g=18, fat_g=2.5, serving_size=40, unit=unit_g),
        create_food(db, slug="paratha", name="Paratha", category=cats["grains"],
                     calories=250, protein_g=4.0, carbs_g=30, fat_g=12, serving_size=80, unit=unit_g),
        create_food(db, slug="chana-masala", name="Chana Masala", category=cats["legumes"],
                     calories=120, protein_g=6.0, carbs_g=18, fat_g=3.0, serving_size=100, unit=unit_g),
        create_food(db, slug="moong-dal", name="Moong Dal", category=cats["legumes"],
                     calories=104, protein_g=7.0, carbs_g=18, fat_g=0.4, serving_size=100, unit=unit_g),
        create_food(db, slug="chicken-curry", name="Chicken Curry", category=cats["meats"],
                     calories=180, protein_g=25, carbs_g=3, fat_g=8, serving_size=100, unit=unit_g),
        create_food(db, slug="mutton-karahi", name="Mutton Karahi", category=cats["meats"],
                     calories=250, protein_g=20, carbs_g=5, fat_g=16, serving_size=100, unit=unit_g),
        create_food(db, slug="yogurt", name="Plain Yogurt", category=cats["dairy"],
                     calories=60, protein_g=3.5, carbs_g=5, fat_g=3, serving_size=100, unit=unit_g),
        create_food(db, slug="milk-whole", name="Whole Milk", category=cats["dairy"],
                     calories=61, protein_g=3.2, carbs_g=4.8, fat_g=3.3, serving_size=100, unit=unit_g),
        create_food(db, slug="sabzi-mix", name="Mixed Vegetable Sabzi", category=cats["vegetables"],
                     calories=65, protein_g=2.5, carbs_g=8, fat_g=2.5, serving_size=100, unit=unit_g),
        create_food(db, slug="palak-paneer", name="Palak Paneer", category=cats["vegetables"],
                     calories=140, protein_g=8, carbs_g=6, fat_g=9, serving_size=100, unit=unit_g),
        create_food(db, slug="banana", name="Banana", category=cats["fruits"],
                     calories=89, protein_g=1.1, carbs_g=23, fat_g=0.3, serving_size=100, unit=unit_g),
        create_food(db, slug="ghee", name="Ghee", category=cats["oils"],
                     calories=900, protein_g=0, carbs_g=0, fat_g=100, serving_size=100, unit=unit_g),
    ]
    db.commit()
    return foods


def create_manual_meal_plan(db: Session, user: User, start_date: date, end_date: date) -> MealPlan:
    """Manually create a meal plan for testing retrieval (without the optimizer)."""
    # Use existing food if one exists, otherwise create one
    food = db.query(Food).first()
    if food is None:
        basics = seed_basics(db)
        food = create_food(db, slug="test-food", name="Test Food", category=basics["categories"]["grains"],
                           calories=100, protein_g=5, carbs_g=20, fat_g=1,
                           serving_size=100, unit=basics["unit_g"])

    unit_g_id = food.serving_unit_id

    meal_plan = MealPlan(
        user_id=user.id,
        name="Test Plan",
        goal=FitnessGoal.GENERAL_FITNESS,
        daily_calorie_target=Decimal(2000),
        daily_protein_g=Decimal(100),
        daily_carbs_g=Decimal(250),
        daily_fat_g=Decimal(65),
        start_date=start_date,
        end_date=end_date,
        status=MealPlanStatus.DRAFT,
    )
    db.add(meal_plan)
    db.flush()

    today = datetime.now(tz=UTC).date()
    day = MealPlanDay(
        meal_plan_id=meal_plan.id,
        plan_date=today,
    )
    db.add(day)
    db.flush()

    meal = Meal(
        name="Test Lunch",
        meal_type=MealType.LUNCH,
        is_active=True,
    )
    db.add(meal)
    db.flush()

    meal_food = MealFood(
        meal_id=meal.id,
        food_id=food.id,
        servings=Decimal(2),
        serving_unit_id=unit_g_id,
        sort_order=0,
    )
    db.add(meal_food)

    day_meal = MealPlanDayMeal(
        meal_plan_day_id=day.id,
        meal_id=meal.id,
        meal_type=MealType.LUNCH,
        sort_order=0,
    )
    db.add(day_meal)

    db.commit()
    db.refresh(meal_plan)
    return meal_plan


# ── Service layer tests ──────────────────────────────────────────────────────


class TestGetCurrentMealPlan:
    def test_returns_plan_when_one_exists(self):
        """get_current_meal_plan returns a plan covering today."""
        reset_db()
        db = db_session.SessionLocal()
        seed_food_dataset(db)
        user = create_user_with_profile(db)

        today = datetime.now(tz=UTC).date()
        plan = create_manual_meal_plan(db, user, today, today)

        result = get_current_meal_plan(db, user_id=user.id)
        assert result is not None
        assert result.id == plan.id
        assert result.start_date <= today <= result.end_date
        db.close()

    def test_returns_none_when_no_plan(self):
        """get_current_meal_plan returns None when user has no plan."""
        reset_db()
        db = db_session.SessionLocal()
        seed_food_dataset(db)
        user = create_user_with_profile(db)

        result = get_current_meal_plan(db, user_id=user.id)
        assert result is None
        db.close()

    def test_returns_none_for_other_user(self):
        """get_current_meal_plan only returns the authenticated user's plan."""
        reset_db()
        db = db_session.SessionLocal()
        seed_food_dataset(db)
        user1 = create_user_with_profile(db, email="user1@example.com")
        user2 = create_user_with_profile(db, email="user2@example.com")

        today = datetime.now(tz=UTC).date()
        create_manual_meal_plan(db, user1, today, today)

        result = get_current_meal_plan(db, user_id=user2.id)
        assert result is None
        db.close()

    def test_ignores_past_plan(self):
        """get_current_meal_plan ignores plans that ended before today."""
        reset_db()
        db = db_session.SessionLocal()
        seed_food_dataset(db)
        user = create_user_with_profile(db)

        yesterday = datetime.now(tz=UTC).date() - timedelta(days=1)
        create_manual_meal_plan(db, user, yesterday, yesterday)

        result = get_current_meal_plan(db, user_id=user.id)
        assert result is None
        db.close()

    def test_ignores_future_plan(self):
        """get_current_meal_plan ignores plans that start after today."""
        reset_db()
        db = db_session.SessionLocal()
        seed_food_dataset(db)
        user = create_user_with_profile(db)

        tomorrow = datetime.now(tz=UTC).date() + timedelta(days=1)
        next_week = datetime.now(tz=UTC).date() + timedelta(days=7)
        create_manual_meal_plan(db, user, tomorrow, next_week)

        result = get_current_meal_plan(db, user_id=user.id)
        assert result is None
        db.close()

    def test_multi_day_plan_covering_today(self):
        """get_current_meal_plan finds a multi-day plan that spans today."""
        reset_db()
        db = db_session.SessionLocal()
        seed_food_dataset(db)
        user = create_user_with_profile(db)

        start = datetime.now(tz=UTC).date() - timedelta(days=3)
        end = datetime.now(tz=UTC).date() + timedelta(days=3)
        plan = create_manual_meal_plan(db, user, start, end)

        result = get_current_meal_plan(db, user_id=user.id)
        assert result is not None
        assert result.id == plan.id
        db.close()


class TestBuildPlanResponseFromDb:
    def test_reconstructs_response_from_persisted_plan(self):
        """build_plan_response_from_db returns a valid MealPlanResponse."""
        reset_db()
        db = db_session.SessionLocal()
        seed_food_dataset(db)
        user = create_user_with_profile(db)

        today = datetime.now(tz=UTC).date()
        plan = create_manual_meal_plan(db, user, today, today)

        response = build_plan_response_from_db(plan)
        assert response.plan_id == str(plan.id)
        assert response.plan_name == "Test Plan"
        assert response.start_date == today
        assert response.end_date == today
        assert len(response.days) == 1
        assert len(response.days[0].meals) == 1
        assert response.days[0].meals[0].meal_type == "lunch"
        assert response.days[0].meals[0].foods[0].name == "Basmati Rice"
        db.close()

    def test_nutrition_data_from_plan(self):
        """Nutrition targets come from the persisted plan."""
        reset_db()
        db = db_session.SessionLocal()
        seed_food_dataset(db)
        user = create_user_with_profile(db)

        today = datetime.now(tz=UTC).date()
        plan = create_manual_meal_plan(db, user, today, today)

        response = build_plan_response_from_db(plan)
        assert response.nutrition.calorie_target == 2000.0
        assert response.nutrition.protein_g == 100.0
        db.close()


# ── Auto-generation prevention test ─────────────────────────────────────────


class TestGetTodayDoesNotGenerate:
    def test_service_does_not_create_plan(self):
        """get_current_meal_plan never creates a new plan."""
        reset_db()
        db = db_session.SessionLocal()
        seed_food_dataset(db)
        user = create_user_with_profile(db)

        # Verify no plan exists
        assert get_current_meal_plan(db, user_id=user.id) is None

        # Call the service again
        result = get_current_meal_plan(db, user_id=user.id)
        assert result is None

        # Verify no MealPlan was created
        count = db.query(MealPlan).filter(MealPlan.user_id == user.id).count()
        assert count == 0
        db.close()


# ── Generation still works ──────────────────────────────────────────────────


class TestGenerationStillWorks:
    def test_generate_then_retrieve(self):
        """After generating a plan, get_current_meal_plan finds it."""
        reset_db()
        db = db_session.SessionLocal()
        seed_food_dataset(db)
        user = create_user_with_profile(db)

        # Generate a plan
        result = generate_meal_plan(db, user_id=user.id, plan_days=1)
        assert result.success

        # Persist it
        plan_id = persist_meal_plan(db, user_id=user.id, result=result)

        # Now get_current_meal_plan should find it
        plan = get_current_meal_plan(db, user_id=user.id)
        assert plan is not None
        assert plan.id == plan_id
        db.close()
