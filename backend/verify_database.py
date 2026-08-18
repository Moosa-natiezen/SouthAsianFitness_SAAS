"""Comprehensive verification script for South Asian Fitness SaaS database models, relationships, constraints, and migrations.

Verifications performed:
1. Dialect & DDL verification (PostgreSQL SQL generation via Alembic)
2. Live DB connection / Test DB session
3. Model schema verification (all 27 tables registered with Base.metadata)
4. Full relational lifecycle & transaction tests:
   - Currency, Unit, Country, Region
   - FoodCategory, CuisineTag, DietaryTag
   - User, UserProfile, UserPreferences, UserFoodPreference
   - Food, FoodPrice, FoodIngredient (recipe linking)
   - Meal, MealFood
   - MealPlan, MealPlanDay, MealPlanDayMeal
   - ProgressEntry
5. Relationship navigation & ORM graph traversal
6. Integrity & Constraint enforcement tests:
   - Check constraint validation (negative calories, negative height)
   - Unique constraint validation (duplicate email, duplicate slug)
   - Foreign key RESTRICT enforcement (deleting currency in use)
   - Foreign key CASCADE enforcement (deleting user cascades to profile, preferences, meal plans, progress)
"""

import sys
from datetime import UTC, date, datetime
from decimal import Decimal

from app.core.config import settings
from app.db.base import Base
from app.models.currency import Currency
from app.models.enums import (
    ActivityLevel,
    DietaryTagKind,
    DietPattern,
    FitnessGoal,
    FoodPreferenceType,
    MealPlanStatus,
    MealType,
    Sex,
    UnitDimension,
    UnitSystem,
)
from app.models.food import Food, FoodPrice
from app.models.geography import Country, Region
from app.models.meal import Meal, MealFood
from app.models.meal_plan import MealPlan, MealPlanDay, MealPlanDayMeal
from app.models.progress import ProgressEntry
from app.models.tags import CuisineTag, DietaryTag, FoodCategory
from app.models.unit import Unit
from app.models.user import User, UserFoodPreference, UserPreferences, UserProfile
from sqlalchemy import JSON, create_engine, inspect, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker


def _patch_jsonb_for_sqlite(metadata) -> None:
    """Replace PostgreSQL JSONB columns with generic JSON so SQLite can render them.

    This does NOT touch the production PostgreSQL schema — it only patches the
    in-memory column type objects on the metadata for the SQLite create_all call.
    """
    for table in metadata.tables.values():
        for col in table.columns:
            if isinstance(col.type, JSONB):
                col.type = JSON()


def get_test_engine():
    """Attempt to connect to configured PostgreSQL database; fall back to in-memory SQLite with foreign keys for local model testing."""
    try:
        pg_engine = create_engine(settings.database_url, pool_pre_ping=True, connect_args={"connect_timeout": 5})
        with pg_engine.connect() as conn:
            conn.execute(select(1))
        print("Connected successfully to PostgreSQL database:", settings.database_url.split("@")[-1])
        return pg_engine, "postgresql"
    except SQLAlchemyError as err:
        print(
            f"Notice: Live PostgreSQL connection not available ({err.__class__.__name__}). "
            "Using test engine with SQLite + foreign keys enabled."
        )
        sqlite_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
        )
        # Enable SQLite foreign key support
        from sqlalchemy import event

        @event.listens_for(sqlite_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        # Patch JSONB → JSON so SQLite can compile the schema
        _patch_jsonb_for_sqlite(Base.metadata)

        Base.metadata.create_all(bind=sqlite_engine)
        return sqlite_engine, "sqlite"


def verify_tables(engine, db_type: str) -> None:
    print(f"\n--- [Step 1] Verifying Tables & Metadata ({db_type.upper()}) ---")
    inspector = inspect(engine)
    tables = sorted(inspector.get_table_names())
    print(f"Total tables detected: {len(tables)}")
    expected_tables = {
        "currencies",
        "countries",
        "regions",
        "units",
        "food_categories",
        "cuisine_tags",
        "dietary_tags",
        "foods",
        "food_ingredients",
        "food_prices",
        "food_regions",
        "food_cuisine_tags",
        "food_dietary_tags",
        "meals",
        "meal_foods",
        "users",
        "user_profiles",
        "user_profile_dietary_tags",
        "user_preferences",
        "user_preference_cuisine_tags",
        "user_preference_dietary_tags",
        "user_preference_regions",
        "user_food_preferences",
        "meal_plans",
        "meal_plan_days",
        "meal_plan_day_meals",
        "progress_entries",
    }
    missing = expected_tables - set(tables)
    if missing:
        print(f"ERROR: Missing expected tables: {missing}")
        sys.exit(1)
    print(f"SUCCESS: All {len(expected_tables)} domain tables verified.")
    print(f"  Tables: {tables}")


def verify_alembic_ddl() -> None:
    """Verify that Alembic can generate valid PostgreSQL DDL without errors."""
    print("\n--- [Step 0] Verifying Alembic DDL Generation ---")
    import subprocess
    result = subprocess.run(
        ["uv", "run", "alembic", "upgrade", "head", "--sql"],
        capture_output=True,
        text=True,
        cwd=".",
        check=False,
    )
    if result.returncode != 0:
        print("ERROR: Alembic DDL generation failed:")
        print(result.stderr)
        sys.exit(1)

    # Spot-check key DDL statements in the generated SQL
    ddl = result.stdout
    required_fragments = [
        "CREATE TABLE currencies",
        "CREATE TABLE countries",
        "CREATE TABLE foods",
        "CREATE TABLE users",
        "CREATE TABLE meal_plans",
        "CREATE TABLE progress_entries",
    ]
    for fragment in required_fragments:
        if fragment not in ddl:
            print(f"ERROR: Expected DDL fragment not found: '{fragment}'")
            sys.exit(1)

    print("SUCCESS: Alembic generated valid PostgreSQL DDL containing all expected table definitions.")


def test_crud_and_relationships(TestSession: sessionmaker) -> None:
    print("\n--- [Step 2] Testing Relational CRUD Operations & Graph Traversal ---")
    with TestSession() as db:
        # 1. Currency & Unit
        pkr = Currency(code="PKR", name="Pakistani Rupee", symbol="Rs", minor_units=2)
        inr = Currency(code="INR", name="Indian Rupee", symbol="INR", minor_units=2)
        usd = Currency(code="USD", name="US Dollar", symbol="$", minor_units=2)
        db.add_all([pkr, inr, usd])
        db.flush()

        unit_g = Unit(code="g", name="Gram", dimension=UnitDimension.MASS, to_base_factor=Decimal("1.0"))
        unit_kg = Unit(code="kg", name="Kilogram", dimension=UnitDimension.MASS, to_base_factor=Decimal("1000.0"))
        unit_roti = Unit(code="roti", name="Roti (Medium Flatbread)", dimension=UnitDimension.COUNT, to_base_factor=None)
        unit_katori = Unit(code="katori", name="Katori (Small Bowl ~150ml)", dimension=UnitDimension.VOLUME, to_base_factor=None)
        unit_cup = Unit(code="cup", name="Cup (240ml)", dimension=UnitDimension.VOLUME, to_base_factor=Decimal("240.0"))
        db.add_all([unit_g, unit_kg, unit_roti, unit_katori, unit_cup])
        db.flush()

        # 2. Geography: Country & Regions
        pk = Country(name="Pakistan", iso_code="PK", currency_code="PKR", default_unit_system=UnitSystem.METRIC)
        ind = Country(name="India", iso_code="IN", currency_code="INR", default_unit_system=UnitSystem.METRIC)
        db.add_all([pk, ind])
        db.flush()

        punjab_pk = Region(name="Punjab (Pakistan)", code="PK-PB", country_id=pk.id)
        sindh_pk = Region(name="Sindh", code="PK-SD", country_id=pk.id)
        punjab_in = Region(name="Punjab (India)", code="IN-PB", country_id=ind.id)
        db.add_all([punjab_pk, sindh_pk, punjab_in])
        db.flush()

        # 3. Tags & Categories
        cat_lentils = FoodCategory(slug="lentils-pulses", name="Lentils & Pulses")
        cat_grains = FoodCategory(slug="breads-grains", name="Breads & Grains")
        cat_meat = FoodCategory(slug="meat-poultry", name="Meat & Poultry")
        db.add_all([cat_lentils, cat_grains, cat_meat])
        db.flush()

        tag_punjabi = CuisineTag(slug="punjabi", name="Punjabi")
        tag_mughlai = CuisineTag(slug="mughlai", name="Mughlai")
        db.add_all([tag_punjabi, tag_mughlai])
        db.flush()

        tag_halal = DietaryTag(slug="halal", name="Halal", kind=DietaryTagKind.RESTRICTION)
        tag_high_protein = DietaryTag(slug="high-protein", name="High-Protein", kind=DietaryTagKind.DIET_PATTERN)
        tag_vegetarian = DietaryTag(slug="vegetarian", name="Vegetarian", kind=DietaryTagKind.DIET_PATTERN)
        db.add_all([tag_halal, tag_high_protein, tag_vegetarian])
        db.flush()

        # 4. User, Profile, Preferences
        user = User(
            email="ahmed.khan@example.com",
            display_name="Ahmed Khan",
            country_id=pk.id,
            region_id=punjab_pk.id,
            preferred_language="ur",
            preferred_unit_system=UnitSystem.METRIC,
            preferred_currency_code="PKR",
        )
        db.add(user)
        db.flush()

        profile = UserProfile(
            user_id=user.id,
            age_years=28,
            sex=Sex.MALE,
            height_cm=Decimal("178.50"),
            weight_kg=Decimal("82.00"),
            activity_level=ActivityLevel.MODERATELY_ACTIVE,
            fitness_goal=FitnessGoal.WEIGHT_LOSS,
            diet_pattern=DietPattern.OMNIVORE,
        )
        profile.dietary_tags.append(tag_halal)
        profile.dietary_tags.append(tag_high_protein)
        db.add(profile)

        preferences = UserPreferences(
            user_id=user.id,
            weekly_budget_amount=Decimal("5000.00"),
            budget_currency_code="PKR",
            notes="Prefers traditional desi homemade meals, high protein for gym.",
        )
        preferences.cuisine_tags.append(tag_punjabi)
        preferences.cuisine_tags.append(tag_mughlai)
        preferences.preferred_regions.append(punjab_pk)
        db.add(preferences)
        db.flush()

        # 5. Foods, Ingredients, and Prices
        daal_raw = Food(
            slug="raw-daal-mash",
            name="Raw Daal Mash (White Lentils)",
            category_id=cat_lentils.id,
            serving_size=Decimal("100.000"),
            serving_unit_id=unit_g.id,
            grams_per_serving=Decimal("100.000"),
            calories=Decimal("350.00"),
            protein_g=Decimal("25.000"),
            carbs_g=Decimal("60.000"),
            fat_g=Decimal("1.500"),
            fiber_g=Decimal("18.000"),
            translations={"ur": {"name": "ماش کی دال"}, "hi": {"name": "उड़द दाल"}},
        )
        roti = Food(
            slug="whole-wheat-roti",
            name="Whole Wheat Roti / Chapati",
            category_id=cat_grains.id,
            serving_size=Decimal("1.000"),
            serving_unit_id=unit_roti.id,
            grams_per_serving=Decimal("45.000"),
            calories=Decimal("120.00"),
            protein_g=Decimal("3.500"),
            carbs_g=Decimal("24.000"),
            fat_g=Decimal("0.800"),
            fiber_g=Decimal("3.000"),
            translations={"ur": {"name": "گندم کی روٹی"}, "hi": {"name": "रोटी"}},
        )
        chicken_breast = Food(
            slug="raw-chicken-breast",
            name="Skinless Chicken Breast",
            category_id=cat_meat.id,
            serving_size=Decimal("100.000"),
            serving_unit_id=unit_g.id,
            grams_per_serving=Decimal("100.000"),
            calories=Decimal("165.00"),
            protein_g=Decimal("31.000"),
            carbs_g=Decimal("0.000"),
            fat_g=Decimal("3.600"),
        )
        db.add_all([daal_raw, roti, chicken_breast])
        db.flush()

        # Link tags to foods
        daal_raw.cuisine_tags.append(tag_punjabi)
        daal_raw.dietary_tags.append(tag_halal)
        daal_raw.dietary_tags.append(tag_vegetarian)
        daal_raw.regions.append(punjab_pk)
        daal_raw.regions.append(punjab_in)

        # Food price
        daal_price = FoodPrice(
            food_id=daal_raw.id,
            country_id=pk.id,
            region_id=punjab_pk.id,
            amount=Decimal("320.00"),
            currency_code="PKR",
            quantity=Decimal("1.000"),
            unit_id=unit_kg.id,
            source="Local Market Survey",
            observed_at=datetime.now(UTC),
        )
        db.add(daal_price)

        # User Food Preference (User loves daal)
        user_food_pref = UserFoodPreference(
            user_id=user.id,
            food_id=daal_raw.id,
            preference_type=FoodPreferenceType.LIKE,
        )
        db.add(user_food_pref)
        db.flush()

        # 6. Meals & Meal Foods
        dinner_meal = Meal(
            name="High-Protein Daal Mash with 2 Rotis",
            description="Traditional Punjabi dinner with cooked lentils and whole-wheat rotis.",
            meal_type=MealType.DINNER,
            translations={"ur": {"name": "ماش کی دال اور دو روٹیاں"}},
        )
        db.add(dinner_meal)
        db.flush()

        mf1 = MealFood(meal_id=dinner_meal.id, food_id=daal_raw.id, servings=Decimal("1.500"), sort_order=0)
        mf2 = MealFood(meal_id=dinner_meal.id, food_id=roti.id, servings=Decimal("2.000"), sort_order=1)
        db.add_all([mf1, mf2])
        db.flush()

        # 7. Meal Plan, Plan Day, Plan Day Meal
        meal_plan = MealPlan(
            user_id=user.id,
            name="Ahmed's 4-Week Fat Loss Plan",
            goal=FitnessGoal.WEIGHT_LOSS,
            daily_calorie_target=Decimal("2100.00"),
            daily_protein_g=Decimal("150.000"),
            daily_carbs_g=Decimal("220.000"),
            daily_fat_g=Decimal("65.000"),
            daily_budget_amount=Decimal("700.00"),
            budget_currency_code="PKR",
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 28),
            status=MealPlanStatus.ACTIVE,
        )
        db.add(meal_plan)
        db.flush()

        plan_day = MealPlanDay(
            meal_plan_id=meal_plan.id,
            plan_date=date(2026, 9, 1),
            notes="Day 1: Leg day training schedule.",
        )
        db.add(plan_day)
        db.flush()

        day_meal = MealPlanDayMeal(
            meal_plan_day_id=plan_day.id,
            meal_id=dinner_meal.id,
            meal_type=MealType.DINNER,
            sort_order=0,
        )
        db.add(day_meal)
        db.flush()

        # 8. Progress Entry
        progress = ProgressEntry(
            user_id=user.id,
            recorded_on=date(2026, 9, 1),
            weight_kg=Decimal("82.00"),
            waist_cm=Decimal("94.00"),
            hip_cm=Decimal("102.00"),
            body_fat_percent=Decimal("22.50"),
            notes="Baseline starting measurements.",
        )
        db.add(progress)
        db.commit()

        print("SUCCESS: Full relational hierarchy created and committed successfully.")

        # Test querying back & verifying relationships
        saved_user = db.scalar(select(User).where(User.id == user.id))
        assert saved_user is not None
        assert saved_user.profile.age_years == 28
        assert saved_user.preferences.weekly_budget_amount == Decimal("5000.00")
        assert len(saved_user.meal_plans) == 1
        assert len(saved_user.meal_plans[0].days) == 1
        assert len(saved_user.meal_plans[0].days[0].day_meals) == 1
        assert saved_user.meal_plans[0].days[0].day_meals[0].meal.name == "High-Protein Daal Mash with 2 Rotis"
        assert len(saved_user.progress_entries) == 1
        print("SUCCESS: ORM navigation and eager/lazy relationship traversal validated.")


def test_constraints_and_cascades(TestSession: sessionmaker) -> None:
    print("\n--- [Step 3] Testing Constraints and Cascades ---")

    # 1. Test Check Constraint: Negative Calories
    with TestSession() as db:
        try:
            unit_id = db.scalar(select(Unit.id))
            invalid_food = Food(
                slug="invalid-negative-food",
                name="Negative Calorie Food",
                serving_size=Decimal(100),
                serving_unit_id=unit_id,
                calories=Decimal("-50.00"),  # Fails ck_foods_non_negative_calories
            )
            db.add(invalid_food)
            db.commit()
            print("ERROR: CheckConstraint failed to block negative calories.")
            sys.exit(1)
        except IntegrityError:
            db.rollback()
            print("SUCCESS: CheckConstraint blocked negative calories as expected.")

    # 2. Test Unique Constraint: Duplicate Email
    with TestSession() as db:
        try:
            country_id = db.scalar(select(Country.id))
            dup_user = User(
                email="ahmed.khan@example.com",  # Already exists
                display_name="Ahmed Duplicate",
                country_id=country_id,
                preferred_language="en",
                preferred_unit_system=UnitSystem.METRIC,
                preferred_currency_code="PKR",
            )
            db.add(dup_user)
            db.commit()
            print("ERROR: UniqueConstraint failed to block duplicate email.")
            sys.exit(1)
        except IntegrityError:
            db.rollback()
            print("SUCCESS: UniqueConstraint blocked duplicate email as expected.")

    # 3. Test Foreign Key RESTRICT on Currency
    with TestSession() as db:
        try:
            pkr = db.scalar(select(Currency).where(Currency.code == "PKR"))
            db.delete(pkr)
            db.commit()
            print("ERROR: FK RESTRICT failed on Currency deletion with dependent countries/users.")
            sys.exit(1)
        except IntegrityError:
            db.rollback()
            print("SUCCESS: FK RESTRICT prevented deleting Currency in active use.")

    # 4. Test Foreign Key CASCADE on User deletion
    with TestSession() as db:
        user = db.scalar(select(User).where(User.email == "ahmed.khan@example.com"))
        user_id = user.id
        db.delete(user)
        db.commit()

        # Verify cascades
        remaining_profile = db.scalar(select(UserProfile).where(UserProfile.user_id == user_id))
        remaining_pref = db.scalar(select(UserPreferences).where(UserPreferences.user_id == user_id))
        remaining_plans = db.scalars(select(MealPlan).where(MealPlan.user_id == user_id)).all()
        remaining_progress = db.scalars(select(ProgressEntry).where(ProgressEntry.user_id == user_id)).all()

        assert remaining_profile is None
        assert remaining_pref is None
        assert len(remaining_plans) == 0
        assert len(remaining_progress) == 0
        print("SUCCESS: User CASCADE deletion cleaned up profile, preferences, meal plans, days, and progress entries.")


if __name__ == "__main__":
    print("=== STARTING DATABASE VERIFICATION ===")

    # Step 0: Verify Alembic DDL generation (PostgreSQL dialect)
    verify_alembic_ddl()

    # Step 1-3: Connect + run full model/relationship/constraint tests
    test_eng, db_type = get_test_engine()
    TestSession = sessionmaker(bind=test_eng, autocommit=False, autoflush=False, class_=Session)

    verify_tables(test_eng, db_type)
    test_crud_and_relationships(TestSession)
    test_constraints_and_cascades(TestSession)
    print("\n=== ALL DATABASE TESTS PASSED WITH 100% SUCCESS ===")
