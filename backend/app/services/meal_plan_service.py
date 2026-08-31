"""Meal plan generation service.

Orchestrates the full meal plan generation pipeline:
1. Resolve user profile → nutrition targets (via nutrition_service)
2. Resolve budget targets (via budget_service)
3. Filter food candidates (via food_candidate_service)
4. Optimize each day (via meal_optimizer)
5. Persist the plan to the database
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.enums import MealPlanStatus, MealType
from app.models.food import FoodPrice
from app.models.meal import Meal, MealFood
from app.models.meal_plan import MealPlan, MealPlanDay, MealPlanDayMeal
from app.models.user import User, UserPreferences
from app.schemas.meal_plan import MealPlanResponse

# ── Free-tier usage limits ──────────────────────────────────────────────────

FREE_MONTHLY_MEAL_PLAN_LIMIT = 3


def check_meal_plan_limit(db: Session, user: User) -> None:
    """Check whether the user has exceeded their monthly meal plan limit.

    Pro users have unlimited generations.
    Free users are limited to FREE_MONTHLY_MEAL_PLAN_LIMIT plans per calendar month.

    Raises HTTPException 403 if the limit is exceeded.
    """
    if user.subscription_tier == "pro":
        return

    # First day of the current calendar month
    now = datetime.now(tz=UTC)
    first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    count = (
        db.query(func.count(MealPlan.id))
        .filter(
            MealPlan.user_id == user.id,
            MealPlan.created_at >= first_of_month,
        )
        .scalar()
        or 0
    )

    if count >= FREE_MONTHLY_MEAL_PLAN_LIMIT:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Free tier limit reached. Please upgrade to Pro to generate more meal plans.",
        )
from app.services.budget_service import BudgetTarget, calculate_budget_targets
from app.services.food_candidate_service import (
    build_filter_context,
    get_candidate_foods,
)
from app.services.meal_optimizer import (
    DayResult,
    OptimizationContext,
    optimize_day,
)
from app.services.meal_plan_config import DEFAULT_MEAL_STRUCTURE, OPTIMIZER_PARAMS
from app.services.nutrition_service import (
    NutritionTarget,
    calculate_nutrition_targets,
)


@dataclass
class GeneratedMealPlan:
    """The full output of meal plan generation."""

    plan_id: UUID
    days: list[GeneratedDay]
    nutrition: NutritionTarget
    budget: BudgetTarget
    warnings: list[str]
    plan_name: str
    start_date: date
    end_date: date


@dataclass
class GeneratedDay:
    """A single day in the generated plan."""

    plan_date: date
    meals: list[GeneratedMeal]
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    total_estimated_cost: Decimal | None
    cost_complete: bool
    warnings: list[str]


@dataclass
class GeneratedMeal:
    """A single meal in the generated plan."""

    meal_type: str
    foods: list[GeneratedFood]
    subtotal_calories: float
    subtotal_protein_g: float
    subtotal_carbs_g: float
    subtotal_fat_g: float
    subtotal_estimated_cost: Decimal | None
    cost_complete: bool


@dataclass
class GeneratedFood:
    """A single food in a generated meal."""

    food_id: str
    name: str
    slug: str
    serving_quantity: float
    serving_unit_code: str
    portion_grams: float
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    estimated_cost: Decimal | None
    cost_available: bool


@dataclass
class GenerationFailure:
    """Structured failure when no valid plan can be generated."""

    reason: str
    conflict_details: list[str]
    suggestions: list[str]


@dataclass
class GenerationResult:
    """Either a successful plan or a structured failure."""

    success: bool
    plan: GeneratedMealPlan | None = None
    failure: GenerationFailure | None = None


def generate_meal_plan(
    db: Session,
    *,
    user_id: UUID,
    plan_days: int | None = None,
    meal_count: int | None = None,
) -> GenerationResult:
    """Generate a meal plan for a user.

    This is the main entry point for meal plan generation.
    """
    all_warnings: list[str] = []

    # Validate plan_days
    if plan_days is not None:
        days = plan_days
    else:
        days = OPTIMIZER_PARAMS.default_plan_days
    if days > OPTIMIZER_PARAMS.max_plan_days:
        return GenerationResult(
            success=False,
            failure=GenerationFailure(
                reason=f"Plan length {days} exceeds maximum {OPTIMIZER_PARAMS.max_plan_days} days",
                conflict_details=[],
                suggestions=["Reduce plan length to 30 days or fewer"],
            ),
        )
    if days < 1:
        return GenerationResult(
            success=False,
            failure=GenerationFailure(
                reason="Plan must be at least 1 day",
                conflict_details=[],
                suggestions=[],
            ),
        )

    # ── Resolve user profile ────────────────────────────────────────────
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        return GenerationResult(
            success=False,
            failure=GenerationFailure(
                reason="User not found",
                conflict_details=[],
                suggestions=[],
            ),
        )

    profile = user.profile
    if profile is None:
        return GenerationResult(
            success=False,
            failure=GenerationFailure(
                reason="User profile not found. Please complete onboarding.",
                conflict_details=[],
                suggestions=["Complete the onboarding process to set your profile"],
            ),
        )

    # ── Calculate nutrition targets ─────────────────────────────────────
    nutrition = calculate_nutrition_targets(
        sex=profile.sex.value if profile.sex else "other",
        age=profile.age_years,
        height_cm=float(profile.height_cm),
        weight_kg=float(profile.weight_kg),
        activity_level=profile.activity_level.value if profile.activity_level else "sedentary",
        goal=profile.fitness_goal.value if profile.fitness_goal else "general_fitness",
    )

    all_warnings.extend(nutrition.warnings)

    # ── Calculate budget targets ────────────────────────────────────────
    prefs: UserPreferences | None = user.preferences
    budget = calculate_budget_targets(
        weekly_budget_amount=prefs.weekly_budget_amount if prefs else None,
        currency_code=prefs.budget_currency_code if prefs else None,
        country_id=user.country_id,
        region_id=user.region_id,
    )

    all_warnings.extend(budget.warnings)

    # ── Build filter context ────────────────────────────────────────────
    filter_ctx = build_filter_context(
        db=db,
        user_id=user_id,
        diet_pattern=profile.diet_pattern,
    )

    # ── Get candidate foods ─────────────────────────────────────────────
    candidates = get_candidate_foods(db, filter_ctx)

    if not candidates:
        return GenerationResult(
            success=False,
            failure=GenerationFailure(
                reason="No eligible foods found after applying filters",
                conflict_details=[
                    "All foods were excluded by verification, diet pattern, allergies, restrictions, or preferences."
                ],
                suggestions=[
                    "Check dietary preferences",
                    "Verify food dataset has relevant foods",
                ],
            ),
        )

    # ── Build price lookup ──────────────────────────────────────────────
    price_per_gram = _build_price_lookup(
        db=db,
        candidates=candidates,
        country_id=user.country_id,
        region_id=user.region_id,
    )

    # ── Determine meal structure ────────────────────────────────────────
    structure = DEFAULT_MEAL_STRUCTURE
    if meal_count is not None:
        structure = _adjust_meal_structure(meal_count)

    # ── Generate each day ──────────────────────────────────────────────
    from datetime import datetime

    start = datetime.now(tz=UTC).date()
    generated_days: list[GeneratedDay] = []

    for day_offset in range(days):
        current_date = start + timedelta(days=day_offset)

        opt_ctx = OptimizationContext(
            calorie_target=nutrition.calorie_target,
            protein_target=nutrition.protein_g,
            carb_target=nutrition.carbs_g,
            fat_target=nutrition.fat_g,
            daily_budget=budget.daily_budget,
            budget_currency=budget.currency_code,
            price_per_gram=price_per_gram,
            candidates=candidates,
            meal_slots=structure.slots,
            day_index=day_offset,
        )

        day_result = optimize_day(opt_ctx)

        generated_days.append(_convert_day_result(day_result, current_date))

    # ── Build plan ─────────────────────────────────────────────────────
    plan_name = _generate_plan_name(nutrition)

    plan = GeneratedMealPlan(
        plan_id=UUID(int=0),  # Will be set on persist
        days=generated_days,
        nutrition=nutrition,
        budget=budget,
        warnings=all_warnings,
        plan_name=plan_name,
        start_date=start,
        end_date=start + timedelta(days=days - 1),
    )

    return GenerationResult(success=True, plan=plan)


def persist_meal_plan(
    db: Session,
    *,
    user_id: UUID,
    result: GenerationResult,
) -> UUID:
    """Persist a generated meal plan to the database.

    Creates MealPlan → MealPlanDay → Meal (per day) → MealFood entries.
    Returns the MealPlan UUID.
    """
    if not result.success or result.plan is None:
        raise ValueError("Cannot persist a failed generation result")

    plan = result.plan

    # Create MealPlan
    from app.models.enums import FitnessGoal

    goal_str = plan.nutrition.goal
    try:
        goal = FitnessGoal(goal_str)
    except ValueError:
        goal = FitnessGoal.GENERAL_FITNESS

    meal_plan = MealPlan(
        user_id=user_id,
        name=plan.plan_name,
        goal=goal,
        daily_calorie_target=Decimal(str(plan.nutrition.calorie_target)),
        daily_protein_g=Decimal(str(plan.nutrition.protein_g)),
        daily_carbs_g=Decimal(str(plan.nutrition.carbs_g)),
        daily_fat_g=Decimal(str(plan.nutrition.fat_g)),
        daily_budget_amount=plan.budget.daily_budget,
        budget_currency_code=plan.budget.currency_code,
        start_date=plan.start_date,
        end_date=plan.end_date,
        status=MealPlanStatus.DRAFT,
    )

    db.add(meal_plan)
    db.flush()

    # Create days
    for gen_day in plan.days:
        day = MealPlanDay(
            meal_plan_id=meal_plan.id,
            plan_date=gen_day.plan_date,
        )
        db.add(day)
        db.flush()

        # Create meals for each slot
        for sort_order, gen_meal in enumerate(gen_day.meals):
            # Create a Meal record
            meal = Meal(
                name=f"{gen_meal.meal_type.title()} - {gen_day.plan_date}",
                meal_type=MealType(gen_meal.meal_type),
                is_active=True,
            )
            db.add(meal)
            db.flush()

            # Add foods to the meal
            for food_sort, gen_food in enumerate(gen_meal.foods):
                meal_food = MealFood(
                    meal_id=meal.id,
                    food_id=gen_food.food_id if isinstance(gen_food.food_id, UUID) else UUID(gen_food.food_id),
                    servings=Decimal(str(gen_food.serving_quantity)),
                    serving_unit_id=None,  # Will be resolved by serving_unit_code
                    sort_order=food_sort,
                )
                db.add(meal_food)

            # Link meal to the day
            day_meal = MealPlanDayMeal(
                meal_plan_day_id=day.id,
                meal_id=meal.id,
                meal_type=MealType(gen_meal.meal_type),
                sort_order=sort_order,
            )
            db.add(day_meal)

    db.commit()
    return meal_plan.id


def get_current_meal_plan(
    db: Session,
    *,
    user_id: UUID,
) -> MealPlan | None:
    """Retrieve the user's currently active meal plan covering today.

    Returns the most recent MealPlan where start_date <= today <= end_date
    and status is DRAFT or ACTIVE. Returns None if no plan exists.
    Eagerly loads days → day_meals → meal → meal_foods → food relationships.
    """
    from sqlalchemy.orm import joinedload

    today = datetime.now(tz=UTC).date()

    plan = (
        db.query(MealPlan)
        .options(
            joinedload(MealPlan.days)
            .joinedload(MealPlanDay.day_meals)
            .joinedload(MealPlanDayMeal.meal)
            .joinedload(Meal.meal_foods)
            .selectinload(MealFood.food),
            joinedload(MealPlan.days)
            .joinedload(MealPlanDay.day_meals)
            .joinedload(MealPlanDayMeal.meal)
            .joinedload(Meal.meal_foods)
            .selectinload(MealFood.serving_unit),
        )
        .filter(
            MealPlan.user_id == user_id,
            MealPlan.start_date <= today,
            MealPlan.end_date >= today,
            MealPlan.status.in_([MealPlanStatus.DRAFT, MealPlanStatus.ACTIVE]),
        )
        .order_by(MealPlan.created_at.desc())
        .first()
    )

    return plan


def build_plan_response_from_db(plan: MealPlan) -> MealPlanResponse:
    """Reconstruct a MealPlanResponse from a persisted MealPlan database object.

    Walks the relationship tree: MealPlan → Days → DayMeals → Meal → MealFoods.
    """
    from app.models.food import Food
    from app.schemas.meal_plan import (
        BudgetTargetOut,
        GeneratedDayOut,
        GeneratedFoodOut,
        GeneratedMealOut,
        NutritionTargetOut,
    )

    days = []
    for db_day in sorted(plan.days, key=lambda d: d.plan_date):
        meals = []
        for dm in sorted(db_day.day_meals, key=lambda m: m.sort_order):
            meal = dm.meal
            if meal is None:
                continue

            foods = []
            for mf in sorted(meal.meal_foods, key=lambda f: f.sort_order):
                food: Food = mf.food
                if food is None:
                    continue

                servings = float(mf.servings) if mf.servings else 1.0
                calories = float(food.calories) * servings
                protein = float(food.protein_g) * servings
                carbs = float(food.carbs_g) * servings
                fat = float(food.fat_g) * servings
                portion = float(food.grams_per_serving) * servings if food.grams_per_serving else 0.0

                foods.append(
                    GeneratedFoodOut(
                        food_id=str(food.id),
                        name=food.name,
                        slug=food.slug,
                        serving_quantity=servings,
                        serving_unit_code=getattr(mf.serving_unit, "code", "serving") if mf.serving_unit else "serving",
                        portion_grams=portion,
                        calories=calories,
                        protein_g=protein,
                        carbs_g=carbs,
                        fat_g=fat,
                        estimated_cost=None,
                        cost_available=False,
                    )
                )

            # Compute meal subtotals from foods
            subtotal_calories = sum(f.calories for f in foods)
            subtotal_protein = sum(f.protein_g for f in foods)
            subtotal_carbs = sum(f.carbs_g for f in foods)
            subtotal_fat = sum(f.fat_g for f in foods)

            meals.append(
                GeneratedMealOut(
                    meal_type=dm.meal_type.value if dm.meal_type else meal.meal_type.value,
                    foods=foods,
                    subtotal_calories=subtotal_calories,
                    subtotal_protein_g=subtotal_protein,
                    subtotal_carbs_g=subtotal_carbs,
                    subtotal_fat_g=subtotal_fat,
                    subtotal_estimated_cost=None,
                    cost_complete=False,
                )
            )

        total_calories = sum(m.subtotal_calories for m in meals)
        total_protein = sum(m.subtotal_protein_g for m in meals)
        total_carbs = sum(m.subtotal_carbs_g for m in meals)
        total_fat = sum(m.subtotal_fat_g for m in meals)

        days.append(
            GeneratedDayOut(
                plan_date=db_day.plan_date,
                meals=meals,
                total_calories=total_calories,
                total_protein_g=total_protein,
                total_carbs_g=total_carbs,
                total_fat_g=total_fat,
                total_estimated_cost=None,
                cost_complete=False,
                warnings=[],
            )
        )

    # Build nutrition/budget from persisted plan targets
    nutrition = NutritionTargetOut(
        calorie_target=float(plan.daily_calorie_target) if plan.daily_calorie_target else 0,
        protein_g=float(plan.daily_protein_g) if plan.daily_protein_g else 0,
        carbs_g=float(plan.daily_carbs_g) if plan.daily_carbs_g else 0,
        fat_g=float(plan.daily_fat_g) if plan.daily_fat_g else 0,
        goal=plan.goal.value if plan.goal else "general_fitness",
        is_bounded=True,
        warnings=[],
    )
    budget = BudgetTargetOut(
        daily_budget=plan.daily_budget_amount,
        weekly_budget=None,
        monthly_budget=None,
        currency_code=plan.budget_currency_code,
    )

    return MealPlanResponse(
        plan_id=str(plan.id),
        plan_name=plan.name or "Current Plan",
        start_date=plan.start_date,
        end_date=plan.end_date,
        days=days,
        nutrition=nutrition,
        budget=budget,
        warnings=[],
    )


def _build_price_lookup(
    db: Session,
    candidates: list,
    country_id: UUID | None,
    region_id: UUID | None,
) -> dict[str, Decimal]:
    """Build a food_id → price_per_gram lookup from FoodPrice data.

    Prefers region-level pricing, falls back to country-level.
    """
    if country_id is None:
        return {}

    food_ids = [c.food_id for c in candidates]
    if not food_ids:
        return {}

    # Get region-level prices first
    prices = _fetch_prices(db, food_ids, country_id, region_id)
    if not prices and region_id is not None:
        # Fall back to country-level (region_id=None)
        prices = _fetch_prices(db, food_ids, country_id, None)

    # Build lookup: take most recent price per food
    lookup: dict[str, Decimal] = {}
    for fp in prices:
        fid = str(fp.food_id)
        if fid in lookup:
            continue  # Already have a price (first is most recent due to ORDER BY)

        if fp.unit and fp.unit.to_base_factor and fp.unit.to_base_factor > 0 and fp.quantity > 0:
            total_grams = fp.quantity * fp.unit.to_base_factor
            if total_grams > 0:
                lookup[fid] = fp.amount / total_grams

    return lookup


def _fetch_prices(
    db: Session,
    food_ids: list[UUID],
    country_id: UUID,
    region_id: UUID | None,
):
    """Fetch food prices with optional region filter."""
    from sqlalchemy import desc, select

    q = (
        select(FoodPrice)
        .where(
            FoodPrice.country_id == country_id,
            FoodPrice.food_id.in_(food_ids),
        )
        .order_by(desc(FoodPrice.observed_at))
    )
    if region_id is not None:
        q = q.where(FoodPrice.region_id == region_id)
    else:
        q = q.where(FoodPrice.region_id.is_(None))

    q = q.limit(500)
    return db.execute(q).scalars().all()


def _convert_day_result(day_result: DayResult, plan_date: date) -> GeneratedDay:
    """Convert an optimizer DayResult to the API-facing GeneratedDay."""
    gen_meals = []
    for meal_result in day_result.meals:
        gen_foods = []
        for sf in meal_result.foods:
            gen_foods.append(
                GeneratedFood(
                    food_id=sf.food_id,
                    name=sf.name,
                    slug=sf.slug,
                    serving_quantity=sf.serving_quantity,
                    serving_unit_code=sf.serving_unit_code,
                    portion_grams=sf.portion_grams,
                    calories=sf.calories,
                    protein_g=sf.protein_g,
                    carbs_g=sf.carbs_g,
                    fat_g=sf.fat_g,
                    estimated_cost=sf.estimated_cost,
                    cost_available=sf.cost_available,
                )
            )
        gen_meals.append(
            GeneratedMeal(
                meal_type=meal_result.meal_type,
                foods=gen_foods,
                subtotal_calories=meal_result.subtotal_calories,
                subtotal_protein_g=meal_result.subtotal_protein_g,
                subtotal_carbs_g=meal_result.subtotal_carbs_g,
                subtotal_fat_g=meal_result.subtotal_fat_g,
                subtotal_estimated_cost=meal_result.subtotal_estimated_cost,
                cost_complete=meal_result.cost_complete,
            )
        )

    return GeneratedDay(
        plan_date=plan_date,
        meals=gen_meals,
        total_calories=day_result.total_calories,
        total_protein_g=day_result.total_protein_g,
        total_carbs_g=day_result.total_carbs_g,
        total_fat_g=day_result.total_fat_g,
        total_estimated_cost=day_result.total_estimated_cost,
        cost_complete=day_result.cost_complete,
        warnings=day_result.warnings,
    )


def _adjust_meal_structure(meal_count: int):
    """Adjust meal structure based on requested meal count."""
    from app.services.meal_plan_config import MealSlot, MealStructure

    if meal_count <= 2:
        return MealStructure(slots=(
            MealSlot(meal_type="lunch", calorie_fraction=0.55, min_foods=2, max_foods=3),
            MealSlot(meal_type="dinner", calorie_fraction=0.45, min_foods=2, max_foods=3),
        ))
    elif meal_count == 3:
        return MealStructure(slots=(
            MealSlot(meal_type="breakfast", calorie_fraction=0.30, min_foods=1, max_foods=2),
            MealSlot(meal_type="lunch", calorie_fraction=0.40, min_foods=2, max_foods=3),
            MealSlot(meal_type="dinner", calorie_fraction=0.30, min_foods=2, max_foods=3),
        ))
    else:
        return DEFAULT_MEAL_STRUCTURE


def _generate_plan_name(nutrition: NutritionTarget) -> str:
    """Generate a descriptive plan name."""
    return (
        f"{nutrition.goal.replace('_', ' ').title()} Plan - "
        f"{nutrition.calorie_target:.0f} kcal/day"
    )


def list_user_meal_plans(
    db: Session,
    *,
    user_id: UUID,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[MealPlan], int]:
    """Return a paginated list of the user's meal plans, newest first."""
    q = db.query(MealPlan).filter(MealPlan.user_id == user_id)
    total = q.count()
    items = (
        q.order_by(MealPlan.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    return items, total


def delete_meal_plan(
    db: Session,
    *,
    user_id: UUID,
    plan_id: UUID,
) -> None:
    """Delete a meal plan owned by the user.

    Raises HTTPException 404 if the plan does not exist or does not belong to the user.
    """
    from fastapi import HTTPException, status

    plan = (
        db.query(MealPlan)
        .filter(MealPlan.id == plan_id, MealPlan.user_id == user_id)
        .first()
    )
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal plan not found",
        )
    db.delete(plan)
    db.commit()
