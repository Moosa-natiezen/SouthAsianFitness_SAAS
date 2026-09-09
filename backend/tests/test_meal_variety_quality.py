"""Regression tests for meal generator food-selection quality.

Pins two product requirements:
1. Raw pantry/seasoning items (garlic, black pepper, turmeric, pure oils,
   sugar) must NEVER be selected as standalone meal foods.
2. Multi-day plans must actually vary from day to day (not repeat the exact
   same menu), while remaining fully deterministic across runs.
"""

from __future__ import annotations

import os
from typing import ClassVar

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-1234567890abcdefg")
os.environ.setdefault("CSRF_SECRET_KEY", "test-csrf-secret-key-1234567890abcdef")
os.environ.setdefault("ENVIRONMENT", "testing")

from app import models as app_models  # noqa: F401
from app.db import session as db_session
from app.db.base import Base
from app.models.enums import (
    ActivityLevel,
    DietPattern,
    FitnessGoal,
    Sex,
    UnitDimension,
    VerificationStatus,
)
from app.models.food import Food
from app.models.tags import FoodCategory
from app.models.unit import Unit
from app.models.user import User, UserProfile
from app.services.food_candidate_service import FilterContext, get_candidate_foods
from app.services.meal_plan_service import generate_meal_plan
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
    unit_g = Unit(code="g", name="gram", dimension=UnitDimension.MASS, to_base_factor=1)
    unit_piece = Unit(code="pc", name="piece", dimension=UnitDimension.COUNT, to_base_factor=None)
    db.add_all([unit_g, unit_piece])

    categories = {}
    for slug in [
        "grains", "meats", "poultry", "fish", "dairy", "eggs",
        "vegetables", "fruits", "legumes", "nuts-seeds", "breads", "snacks",
        "spices", "sweeteners", "oils-fats",
    ]:
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


def seed_varied_dataset(db: Session) -> dict:
    """A realistic, varied South Asian food set + a batch of pantry items.

    Includes the whole-food categories needed for quality meal plans AND the
    pantry categories (spices/sweeteners/oils-fats) that must never be picked
    standalone.
    """
    basics = seed_basics(db)
    cats = basics["categories"]
    g = basics["unit_g"]
    pc = basics["unit_piece"]

    foods = {}
    foods["basmati-rice"] = create_food(db, slug="basmati-rice", name="Basmati Rice",
        category=cats["grains"], calories=130, protein_g=2.7, carbs_g=28, fat_g=0.3, unit=g)
    foods["roti"] = create_food(db, slug="roti", name="Roti", category=cats["breads"],
        calories=105, protein_g=3.0, carbs_g=18, fat_g=2.5, serving_size=40, unit=g)
    foods["paratha"] = create_food(db, slug="paratha", name="Paratha", category=cats["breads"],
        calories=250, protein_g=4.0, carbs_g=30, fat_g=12, serving_size=80, unit=g)
    foods["naan"] = create_food(db, slug="naan", name="Naan", category=cats["breads"],
        calories=262, protein_g=8.7, carbs_g=45, fat_g=5.7, serving_size=90, unit=g)
    foods["oats"] = create_food(db, slug="oats", name="Oats", category=cats["grains"],
        calories=389, protein_g=16.9, carbs_g=66, fat_g=6.9, unit=g)
    foods["chana-masala"] = create_food(db, slug="chana-masala", name="Chana Masala",
        category=cats["legumes"], calories=120, protein_g=6.0, carbs_g=18, fat_g=3.0, unit=g)
    foods["moong-dal"] = create_food(db, slug="moong-dal", name="Moong Dal",
        category=cats["legumes"], calories=104, protein_g=7.0, carbs_g=18, fat_g=0.4, unit=g)
    foods["masoor-dal"] = create_food(db, slug="masoor-dal", name="Masoor Dal",
        category=cats["legumes"], calories=116, protein_g=9.0, carbs_g=20, fat_g=0.4, unit=g)
    foods["rajma"] = create_food(db, slug="rajma", name="Rajma", category=cats["legumes"],
        calories=127, protein_g=8.7, carbs_g=21, fat_g=0.5, unit=g)
    foods["chickpeas"] = create_food(db, slug="chickpeas", name="Chickpeas",
        category=cats["legumes"], calories=164, protein_g=8.9, carbs_g=27, fat_g=2.6, unit=g)
    foods["chicken-curry"] = create_food(db, slug="chicken-curry", name="Chicken Curry",
        category=cats["meats"], calories=180, protein_g=25, carbs_g=3, fat_g=8, unit=g)
    foods["mutton-karahi"] = create_food(db, slug="mutton-karahi", name="Mutton Karahi",
        category=cats["meats"], calories=250, protein_g=20, carbs_g=5, fat_g=16, unit=g)
    foods["beef-nihari"] = create_food(db, slug="beef-nihari", name="Beef Nihari",
        category=cats["meats"], calories=280, protein_g=18, carbs_g=8, fat_g=20, unit=g)
    foods["seekh-kebab"] = create_food(db, slug="seekh-kebab", name="Seekh Kebab",
        category=cats["meats"], calories=230, protein_g=22, carbs_g=3, fat_g=15, unit=g)
    foods["chicken-tikka"] = create_food(db, slug="chicken-tikka", name="Chicken Tikka",
        category=cats["poultry"], calories=190, protein_g=26, carbs_g=2, fat_g=9, unit=g)
    foods["chicken-biryani"] = create_food(db, slug="chicken-biryani", name="Chicken Biryani",
        category=cats["poultry"], calories=210, protein_g=12, carbs_g=28, fat_g=6, unit=g)
    foods["fish-curry"] = create_food(db, slug="fish-curry", name="Fish Curry",
        category=cats["fish"], calories=150, protein_g=20, carbs_g=3, fat_g=7, unit=g)
    foods["boiled-egg"] = create_food(db, slug="boiled-egg", name="Boiled Egg",
        category=cats["eggs"], calories=155, protein_g=13, carbs_g=1.1, fat_g=11,
        serving_size=50, unit=pc)
    foods["egg-curry"] = create_food(db, slug="egg-curry", name="Egg Curry",
        category=cats["eggs"], calories=130, protein_g=10, carbs_g=3, fat_g=9, unit=g)
    foods["omelette"] = create_food(db, slug="omelette", name="Masala Omelette",
        category=cats["eggs"], calories=154, protein_g=11, carbs_g=1.2, fat_g=12, unit=g)
    foods["yogurt"] = create_food(db, slug="yogurt", name="Plain Yogurt",
        category=cats["dairy"], calories=60, protein_g=3.5, carbs_g=5, fat_g=3, unit=g)
    foods["paneer"] = create_food(db, slug="paneer", name="Paneer",
        category=cats["dairy"], calories=265, protein_g=18, carbs_g=4, fat_g=21, unit=g)
    foods["milk-whole"] = create_food(db, slug="milk-whole", name="Whole Milk",
        category=cats["dairy"], calories=61, protein_g=3.2, carbs_g=4.8, fat_g=3.3, unit=g)
    foods["sabzi-mix"] = create_food(db, slug="sabzi-mix", name="Mixed Vegetable Sabzi",
        category=cats["vegetables"], calories=65, protein_g=2.5, carbs_g=8, fat_g=2.5, unit=g)
    foods["palak-paneer"] = create_food(db, slug="palak-paneer", name="Palak Paneer",
        category=cats["vegetables"], calories=140, protein_g=8, carbs_g=6, fat_g=9, unit=g)
    foods["aloo-gobi"] = create_food(db, slug="aloo-gobi", name="Aloo Gobi",
        category=cats["vegetables"], calories=110, protein_g=3.0, carbs_g=15, fat_g=4.5, unit=g)
    foods["saag"] = create_food(db, slug="saag", name="Saag", category=cats["vegetables"],
        calories=50, protein_g=3.5, carbs_g=5, fat_g=2.0, unit=g)
    foods["banana"] = create_food(db, slug="banana", name="Banana",
        category=cats["fruits"], calories=89, protein_g=1.1, carbs_g=23, fat_g=0.3, unit=g)
    foods["mango"] = create_food(db, slug="mango", name="Mango",
        category=cats["fruits"], calories=60, protein_g=0.8, carbs_g=15, fat_g=0.4, unit=g)
    foods["papaya"] = create_food(db, slug="papaya", name="Papaya",
        category=cats["fruits"], calories=43, protein_g=0.5, carbs_g=11, fat_g=0.3, unit=g)
    foods["almonds"] = create_food(db, slug="almonds", name="Almonds",
        category=cats["nuts-seeds"], calories=579, protein_g=21, carbs_g=22, fat_g=50,
        serving_size=28, unit=g)
    foods["samosa"] = create_food(db, slug="samosa", name="Samosa",
        category=cats["snacks"], calories=310, protein_g=6, carbs_g=30, fat_g=18, unit=g)

    # ── Pantry items (must NEVER be picked standalone) ────────────────
    foods["garlic"] = create_food(db, slug="garlic", name="Garlic (raw)",
        category=cats["spices"], calories=149, protein_g=6.4, carbs_g=33, fat_g=0.5, unit=g)
    foods["black-pepper"] = create_food(db, slug="black-pepper", name="Black Pepper",
        category=cats["spices"], calories=251, protein_g=10.4, carbs_g=64, fat_g=3.3, unit=g)
    foods["turmeric"] = create_food(db, slug="turmeric", name="Turmeric (ground)",
        category=cats["spices"], calories=312, protein_g=9.7, carbs_g=68, fat_g=3.3, unit=g)
    foods["cumin-seeds"] = create_food(db, slug="cumin-seeds", name="Cumin Seeds",
        category=cats["spices"], calories=375, protein_g=17.8, carbs_g=44, fat_g=22.3, unit=g)
    foods["sugar"] = create_food(db, slug="sugar", name="Sugar",
        category=cats["sweeteners"], calories=387, protein_g=0, carbs_g=100, fat_g=0, unit=g)
    foods["jaggery"] = create_food(db, slug="jaggery", name="Jaggery (Gur)",
        category=cats["sweeteners"], calories=383, protein_g=0.4, carbs_g=98, fat_g=0.1, unit=g)
    foods["mustard-oil"] = create_food(db, slug="mustard-oil", name="Mustard Oil",
        category=cats["oils-fats"], calories=884, protein_g=0, carbs_g=0, fat_g=100, unit=g)
    foods["ghee"] = create_food(db, slug="ghee", name="Ghee",
        category=cats["oils-fats"], calories=900, protein_g=0, carbs_g=0, fat_g=100, unit=g)

    db.commit()
    return {"foods": foods, "basics": basics}


def create_user_with_profile(db: Session) -> User:
    user = User(
        email="variety@test.com",
        display_name="Variety Tester",
        password_hash="fakehash",
        preferred_language="en",
    )
    db.add(user)
    db.flush()

    profile = UserProfile(
        user_id=user.id,
        age_years=30,
        sex=Sex.MALE,
        height_cm=175,
        weight_kg=70,
        activity_level=ActivityLevel.MODERATELY_ACTIVE,
        fitness_goal=FitnessGoal.GENERAL_FITNESS,
        diet_pattern=DietPattern.OMNIVORE,
    )
    db.add(profile)
    db.commit()
    return user


def plan_slugs(plan) -> list[set[str]]:
    """Return each day's food slug set, in day order."""
    day_sets = []
    for day in plan.days:
        slugs = set()
        for meal in day.meals:
            for f in meal.foods:
                slugs.add(f.slug)
        day_sets.append(slugs)
    return day_sets


# ── Pantry / raw-ingredient exclusion ───────────────────────────────────────


class TestPantryExclusion:
    def test_pantry_foods_never_selected_across_days(self):
        """Garlic, black pepper, turmeric, sugar, and pure oils must never
        appear as standalone meal items — not on day 1 or any later day."""
        reset_db()
        db = db_session.SessionLocal()
        seed_varied_dataset(db)
        user = create_user_with_profile(db)

        result = generate_meal_plan(db, user_id=user.id, plan_days=7)
        assert result.success
        assert len(result.plan.days) == 7

        pantry_slugs = {
            "garlic", "black-pepper", "turmeric", "cumin-seeds",
            "sugar", "jaggery", "mustard-oil", "ghee",
        }
        for day_index, day_slugs in enumerate(plan_slugs(result.plan)):
            assert not (day_slugs & pantry_slugs), (
                f"Day {day_index} contains pantry item(s) "
                f"{day_slugs & pantry_slugs} selected standalone"
            )
        db.close()

    def test_pantry_exclusion_still_yields_food(self):
        """Excluding pantry items must not starve the plan of calories."""
        reset_db()
        db = db_session.SessionLocal()
        seed_varied_dataset(db)
        user = create_user_with_profile(db)

        result = generate_meal_plan(db, user_id=user.id, plan_days=7)
        assert result.success
        for day in result.plan.days:
            assert day.total_calories > 0
            assert len(day.meals) == 4
        db.close()


# ── Cross-day variety ───────────────────────────────────────────────────────


class TestCrossDayVariety:
    def test_multi_day_plan_rotates_foods(self):
        """A 7-day plan from a varied library should produce multiple
        distinct daily menus instead of repeating the identical day."""
        reset_db()
        db = db_session.SessionLocal()
        seed_varied_dataset(db)
        user = create_user_with_profile(db)

        result = generate_meal_plan(db, user_id=user.id, plan_days=7)
        assert result.success

        day_sets = plan_slugs(result.plan)
        unique_days = len({frozenset(d) for d in day_sets})
        print(f"\n  7-day variety: {unique_days}/7 unique daily menus")
        assert unique_days >= 4, (
            f"Expected day-to-day rotation but only {unique_days}/7 days "
            f"differ — optimizer is repeating the same menu"
        )

        # Consecutive days should not be exact copies when plenty of foods exist
        identical_pairs = sum(
            1 for i in range(len(day_sets) - 1) if day_sets[i] == day_sets[i + 1]
        )
        assert identical_pairs <= 2, (
            f"{identical_pairs} consecutive identical day pairs — rotation failed"
        )
        db.close()

    def test_day_two_differs_from_day_one(self):
        """Day 2 should not simply clone day 1 (food-level, not totals)."""
        reset_db()
        db = db_session.SessionLocal()
        seed_varied_dataset(db)
        user = create_user_with_profile(db)

        result = generate_meal_plan(db, user_id=user.id, plan_days=2)
        assert result.success
        day_sets = plan_slugs(result.plan)
        assert day_sets[0] != day_sets[1], (
            "Day 2 repeats day 1's exact food set"
        )
        db.close()

    def test_multi_day_plan_stays_deterministic(self):
        """Rotation must remain fully deterministic across identical runs."""
        reset_db()
        db = db_session.SessionLocal()
        seed_varied_dataset(db)
        user = create_user_with_profile(db)

        r1 = generate_meal_plan(db, user_id=user.id, plan_days=7)
        r2 = generate_meal_plan(db, user_id=user.id, plan_days=7)
        assert r1.success and r2.success

        for d1, d2 in zip(r1.plan.days, r2.plan.days):
            for m1, m2 in zip(d1.meals, d2.meals):
                assert len(m1.foods) == len(m2.foods)
                for f1, f2 in zip(m1.foods, m2.foods):
                    assert f1.slug == f2.slug
                    assert f1.portion_grams == f2.portion_grams
                    assert f1.calories == f2.calories
        db.close()


# ── Meal-suitability exclusion (organ meats / plain white bread) ───────────


def seed_suitability_dataset(db: Session) -> dict:
    """A realistic whole-food set plus the offenders that must never be
    generated as standalone meals: beef/chicken liver and plain white bread.

    Liver is deliberately the most protein-dense food in the pool (135 kcal,
    20 g protein per 100 g) so a macro-driven optimizer would otherwise reach
    for it in every protein-heavy meal slot.
    """
    basics = seed_basics(db)
    cats = basics["categories"]
    g = basics["unit_g"]
    pc = basics["unit_piece"]

    foods = {}
    foods["basmati-rice"] = create_food(db, slug="basmati-rice", name="Basmati Rice",
        category=cats["grains"], calories=130, protein_g=2.7, carbs_g=28, fat_g=0.3, unit=g)
    foods["roti"] = create_food(db, slug="roti", name="Roti", category=cats["breads"],
        calories=105, protein_g=3.0, carbs_g=18, fat_g=2.5, serving_size=40, unit=g)
    foods["chicken-curry"] = create_food(db, slug="chicken-curry", name="Chicken Curry",
        category=cats["meats"], calories=180, protein_g=25, carbs_g=3, fat_g=8, unit=g)
    foods["mutton-karahi"] = create_food(db, slug="mutton-karahi", name="Mutton Karahi",
        category=cats["meats"], calories=250, protein_g=20, carbs_g=5, fat_g=16, unit=g)
    foods["moong-dal"] = create_food(db, slug="moong-dal", name="Moong Dal",
        category=cats["legumes"], calories=104, protein_g=7.0, carbs_g=18, fat_g=0.4, unit=g)
    foods["masoor-dal"] = create_food(db, slug="masoor-dal", name="Masoor Dal",
        category=cats["legumes"], calories=116, protein_g=9.0, carbs_g=20, fat_g=0.4, unit=g)
    foods["yogurt"] = create_food(db, slug="yogurt", name="Plain Yogurt",
        category=cats["dairy"], calories=60, protein_g=3.5, carbs_g=5, fat_g=3, unit=g)
    foods["paneer"] = create_food(db, slug="paneer", name="Paneer",
        category=cats["dairy"], calories=265, protein_g=18, carbs_g=4, fat_g=21, unit=g)
    foods["palak-paneer"] = create_food(db, slug="palak-paneer", name="Palak Paneer",
        category=cats["vegetables"], calories=140, protein_g=8, carbs_g=6, fat_g=9, unit=g)
    foods["aloo-gobi"] = create_food(db, slug="aloo-gobi", name="Aloo Gobi",
        category=cats["vegetables"], calories=110, protein_g=3.0, carbs_g=15, fat_g=4.5, unit=g)
    foods["banana"] = create_food(db, slug="banana", name="Banana",
        category=cats["fruits"], calories=89, protein_g=1.1, carbs_g=23, fat_g=0.3, unit=g)
    foods["almonds"] = create_food(db, slug="almonds", name="Almonds",
        category=cats["nuts-seeds"], calories=579, protein_g=21, carbs_g=22, fat_g=50,
        serving_size=28, unit=g)
    foods["boiled-egg"] = create_food(db, slug="boiled-egg", name="Boiled Egg",
        category=cats["eggs"], calories=155, protein_g=13, carbs_g=1.1, fat_g=11,
        serving_size=50, unit=pc)

    # ── Offenders (verified + active, but must never be standalone meals) ──
    foods["beef-liver"] = create_food(db, slug="beef-liver", name="Beef liver (cooked)",
        category=cats["meats"], calories=135, protein_g=20.4, carbs_g=4, fat_g=3.6, unit=g)
    foods["chicken-liver"] = create_food(db, slug="chicken-liver", name="Chicken liver (cooked)",
        category=cats["meats"], calories=116, protein_g=16.9, carbs_g=0.9, fat_g=4.8, unit=g)
    foods["white-bread"] = create_food(db, slug="white-bread", name="Bread (white)",
        category=cats["grains"], calories=265, protein_g=9, carbs_g=49, fat_g=3.2, unit=g)

    db.commit()
    return {"foods": foods, "basics": basics}


class TestMealSuitabilityExclusions:
    """Organ meats and plain white bread must never appear in generated meals."""

    OFFENDER_SLUGS: ClassVar[set[str]] = {"beef-liver", "chicken-liver", "white-bread"}

    def test_offenders_excluded_from_candidate_pool(self):
        """Even for an omnivore, liver and white bread never reach the
        optimizer's candidate pool (they stay in the Food Library only)."""
        reset_db()
        db = db_session.SessionLocal()
        seed_suitability_dataset(db)

        ctx = FilterContext(diet_pattern=DietPattern.OMNIVORE)
        candidates = get_candidate_foods(db, ctx)
        slugs = {c.slug for c in candidates}

        assert not (slugs & self.OFFENDER_SLUGS), (
            f"Offenders leaked into the candidate pool: {slugs & self.OFFENDER_SLUGS}"
        )
        # The whole foods remain available.
        assert {"chicken-curry", "basmati-rice", "moong-dal"} <= slugs
        db.close()

    def test_offenders_never_selected_across_plan_days(self):
        """A generated plan must never contain liver or white bread on any day."""
        reset_db()
        db = db_session.SessionLocal()
        seed_suitability_dataset(db)
        user = create_user_with_profile(db)

        result = generate_meal_plan(db, user_id=user.id, plan_days=7)
        assert result.success
        assert len(result.plan.days) == 7

        for day_index, day_slugs in enumerate(plan_slugs(result.plan)):
            assert not (day_slugs & self.OFFENDER_SLUGS), (
                f"Day {day_index} contains unsuitable meal food(s) "
                f"{day_slugs & self.OFFENDER_SLUGS}"
            )
        db.close()

    def test_exclusion_still_yields_full_plan(self):
        """Excluding offenders must not starve the generated plan."""
        reset_db()
        db = db_session.SessionLocal()
        seed_suitability_dataset(db)
        user = create_user_with_profile(db)

        result = generate_meal_plan(db, user_id=user.id, plan_days=7)
        assert result.success
        for day in result.plan.days:
            assert day.total_calories > 0
            assert len(day.meals) == 4
        db.close()


# ── Raw commodity exclusion (condensed milk, sorghum, ragi, flours, etc.) ──


def seed_raw_commodity_dataset(db: Session) -> dict:
    """A realistic whole-food set plus raw commodities that must never be
    selected as standalone meals: condensed milk, sorghum, finger millet,
    raw flours, ghee, butter, sugar, etc.

    Raw commodities are deliberately high in a single macro (protein or carbs)
    so a macro-driven optimizer would otherwise reach for them.
    """
    basics = seed_basics(db)
    cats = basics["categories"]
    g = basics["unit_g"]
    pc = basics["unit_piece"]

    # Add a raw-grains category for the raw items
    raw_cat = FoodCategory(name="Raw Grains", slug="raw-grains")
    db.add(raw_cat)
    db.flush()

    foods = {}
    # Whole foods (must remain available)
    foods["basmati-rice"] = create_food(db, slug="basmati-rice", name="Basmati Rice",
        category=cats["grains"], calories=130, protein_g=2.7, carbs_g=28, fat_g=0.3, unit=g)
    foods["roti"] = create_food(db, slug="roti", name="Roti", category=cats["breads"],
        calories=105, protein_g=3.0, carbs_g=18, fat_g=2.5, serving_size=40, unit=g)
    foods["chicken-curry"] = create_food(db, slug="chicken-curry", name="Chicken Curry",
        category=cats["meats"], calories=180, protein_g=25, carbs_g=3, fat_g=8, unit=g)
    foods["moong-dal"] = create_food(db, slug="moong-dal", name="Moong Dal",
        category=cats["legumes"], calories=104, protein_g=7.0, carbs_g=18, fat_g=0.4, unit=g)
    foods["yogurt"] = create_food(db, slug="yogurt", name="Plain Yogurt",
        category=cats["dairy"], calories=60, protein_g=3.5, carbs_g=5, fat_g=3, unit=g)
    foods["paneer"] = create_food(db, slug="paneer", name="Paneer",
        category=cats["dairy"], calories=265, protein_g=18, carbs_g=4, fat_g=21, unit=g)
    foods["palak-paneer"] = create_food(db, slug="palak-paneer", name="Palak Paneer",
        category=cats["vegetables"], calories=140, protein_g=8, carbs_g=6, fat_g=9, unit=g)
    foods["aloo-gobi"] = create_food(db, slug="aloo-gobi", name="Aloo Gobi",
        category=cats["vegetables"], calories=110, protein_g=3.0, carbs_g=15, fat_g=4.5, unit=g)
    foods["banana"] = create_food(db, slug="banana", name="Banana",
        category=cats["fruits"], calories=89, protein_g=1.1, carbs_g=23, fat_g=0.3, unit=g)
    foods["almonds"] = create_food(db, slug="almonds", name="Almonds",
        category=cats["nuts-seeds"], calories=579, protein_g=21, carbs_g=22, fat_g=50,
        serving_size=28, unit=g)
    foods["boiled-egg"] = create_food(db, slug="boiled-egg", name="Boiled Egg",
        category=cats["eggs"], calories=155, protein_g=13, carbs_g=1.1, fat_g=11,
        serving_size=50, unit=pc)

    # ── Raw commodities (verified + active, but must never be standalone meals) ──
    foods["condensed-milk"] = create_food(db, slug="condensed-milk",
        name="Condensed milk (sweetened)", category=cats["dairy"],
        calories=321, protein_g=7.9, carbs_g=54, fat_g=8.7, unit=g)
    foods["sorghum"] = create_food(db, slug="sorghum", name="Sorghum (jowar)",
        category=raw_cat, calories=329, protein_g=10.4, carbs_g=72, fat_g=3.1, unit=g)
    foods["finger-millet"] = create_food(db, slug="finger-millet",
        name="Finger millet (ragi)", category=raw_cat,
        calories=336, protein_g=11, carbs_g=72, fat_g=1.3, unit=g)
    foods["whole-wheat-flour"] = create_food(db, slug="whole-wheat-flour",
        name="Whole wheat flour (atta)", category=raw_cat,
        calories=340, protein_g=13.2, carbs_g=72, fat_g=2.5, unit=g)
    foods["all-purpose-flour"] = create_food(db, slug="all-purpose-flour",
        name="All-purpose flour (maida)", category=raw_cat,
        calories=364, protein_g=10.3, carbs_g=76, fat_g=1.0, unit=g)
    foods["ghee"] = create_food(db, slug="ghee", name="Ghee (clarified butter)",
        category=cats["dairy"], calories=900, protein_g=0, carbs_g=0, fat_g=100, unit=g)
    foods["butter"] = create_food(db, slug="butter", name="Butter (salted)",
        category=cats["dairy"], calories=717, protein_g=0.9, carbs_g=0.1, fat_g=81, unit=g)
    foods["sugar"] = create_food(db, slug="sugar", name="Sugar (granulated)",
        category=cats["sweeteners"], calories=387, protein_g=0, carbs_g=100, fat_g=0, unit=g)
    foods["white-rice"] = create_food(db, slug="white-rice",
        name="White rice (long-grain, raw)", category=raw_cat,
        calories=130, protein_g=2.7, carbs_g=28, fat_g=0.3, unit=g)

    db.commit()
    return {"foods": foods, "basics": basics}


RAW_COMMODITY_SLUGS: ClassVar[set[str]] = {
    "condensed-milk", "sorghum", "finger-millet",
    "whole-wheat-flour", "all-purpose-flour",
    "ghee", "butter", "sugar", "white-rice",
}


class TestRawCommodityExclusions:
    """Raw commodities, baking items, and non-meal ingredients must never
    appear as standalone generated meals."""

    def test_raw_commodities_excluded_from_candidate_pool(self):
        """Raw commodities never reach the optimizer's candidate pool."""
        reset_db()
        db = db_session.SessionLocal()
        seed_raw_commodity_dataset(db)

        ctx = FilterContext(diet_pattern=DietPattern.OMNIVORE)
        candidates = get_candidate_foods(db, ctx)
        slugs = {c.slug for c in candidates}

        leaked = slugs & RAW_COMMODITY_SLUGS
        assert not leaked, f"Raw commodities leaked into candidate pool: {leaked}"
        # Whole foods remain available
        assert {"chicken-curry", "basmati-rice", "moong-dal"} <= slugs
        db.close()

    def test_raw_commodities_never_selected_across_plan_days(self):
        """A generated plan must never contain raw commodities on any day."""
        reset_db()
        db = db_session.SessionLocal()
        seed_raw_commodity_dataset(db)
        user = create_user_with_profile(db)

        result = generate_meal_plan(db, user_id=user.id, plan_days=7)
        assert result.success
        assert len(result.plan.days) == 7

        for day_index, day_slugs in enumerate(plan_slugs(result.plan)):
            leaked = day_slugs & RAW_COMMODITY_SLUGS
            assert not leaked, (
                f"Day {day_index} contains raw commodity(s) {leaked} selected standalone"
            )
        db.close()

    def test_exclusion_still_yields_full_plan(self):
        """Excluding raw commodities must not starve the generated plan."""
        reset_db()
        db = db_session.SessionLocal()
        seed_raw_commodity_dataset(db)
        user = create_user_with_profile(db)

        result = generate_meal_plan(db, user_id=user.id, plan_days=7)
        assert result.success
        for day in result.plan.days:
            assert day.total_calories > 0
            assert len(day.meals) == 4
        db.close()
