"""Deterministic meal plan optimizer.

For each meal slot, selects foods and portion sizes that minimize
a weighted cost function composed of:
  - nutrition deviation (calorie, protein, carb, fat)
  - budget deviation
  - variety penalty (repeated foods)
  - preference penalty (disliked, not liked)

The optimizer is deterministic: same inputs → same output.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.services.meal_plan_config import (
    OPTIMIZER_PARAMS,
    PORTION_BOUNDS,
    SCORING_WEIGHTS,
    MealSlot,
)


@dataclass
class SelectedFood:
    """A food selected for a meal with a specific portion."""

    food_id: str
    name: str
    slug: str
    serving_quantity: float
    serving_unit_code: str
    portion_grams: float

    # Nutrition for this portion
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float

    # Estimated cost (None if unavailable)
    estimated_cost: Decimal | None
    cost_available: bool

    # Category for variety tracking
    category_slug: str | None


@dataclass
class MealResult:
    """Result of optimizing a single meal."""

    meal_type: str
    foods: list[SelectedFood]
    subtotal_calories: float
    subtotal_protein_g: float
    subtotal_carbs_g: float
    subtotal_fat_g: float
    subtotal_estimated_cost: Decimal | None
    cost_complete: bool  # True if all foods had price data
    warnings: list[str]


@dataclass
class DayResult:
    """Result of optimizing a full day."""

    meals: list[MealResult]
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    total_estimated_cost: Decimal | None
    cost_complete: bool
    warnings: list[str]


@dataclass
class OptimizationContext:
    """All data needed by the optimizer for one day."""

    # Targets
    calorie_target: float
    protein_target: float
    carb_target: float
    fat_target: float

    # Budget
    daily_budget: Decimal | None
    budget_currency: str | None
    price_per_gram: dict[str, Decimal]  # food_id → price per gram

    # Foods available (pre-filtered candidates)
    candidates: list  # list[CandidateFood]

    # Structure
    meal_slots: tuple[MealSlot, ...]


def optimize_day(ctx: OptimizationContext) -> DayResult:
    """Optimize a full day of meals.

    Uses a greedy approach: for each meal slot, select the best combination
    of foods and portions that moves toward the remaining daily targets
    while respecting variety and preference constraints.
    """
    all_warnings: list[str] = []
    all_meals: list[MealResult] = []
    foods_used_today: dict[str, int] = {}  # slug → count
    categories_used: list[str] = []

    # Track remaining targets as we fill meals
    remaining_cal = ctx.calorie_target
    remaining_protein = ctx.protein_target
    remaining_carbs = ctx.carb_target
    remaining_fat = ctx.fat_target

    for slot in ctx.meal_slots:
        slot_cal_target = ctx.calorie_target * slot.calorie_fraction
        slot_protein_target = ctx.protein_target * slot.calorie_fraction
        slot_carb_target = ctx.carb_target * slot.calorie_fraction
        slot_fat_target = ctx.fat_target * slot.calorie_fraction

        meal = _optimize_meal(
            slot=slot,
            cal_target=slot_cal_target,
            protein_target=slot_protein_target,
            carb_target=slot_carb_target,
            fat_target=slot_fat_target,
            candidates=ctx.candidates,
            price_per_gram=ctx.price_per_gram,
            foods_used_today=foods_used_today,
            categories_used=categories_used,
            daily_budget=ctx.daily_budget,
            budget_currency=ctx.budget_currency,
        )

        all_meals.append(meal)

        # Update remaining
        remaining_cal -= meal.subtotal_calories
        remaining_protein -= meal.subtotal_protein_g
        remaining_carbs -= meal.subtotal_carbs_g
        remaining_fat -= meal.subtotal_fat_g

        # Track foods used
        for sf in meal.foods:
            foods_used_today[sf.slug] = foods_used_today.get(sf.slug, 0) + 1
            if sf.category_slug:
                categories_used.append(sf.category_slug)

        all_warnings.extend(meal.warnings)

    # Day totals
    total_cal = sum(m.subtotal_calories for m in all_meals)
    total_protein = sum(m.subtotal_protein_g for m in all_meals)
    total_carbs = sum(m.subtotal_carbs_g for m in all_meals)
    total_fat = sum(m.subtotal_fat_g for m in all_meals)

    # Budget
    cost_complete = all(m.cost_complete for m in all_meals)
    total_cost = None
    if cost_complete:
        costs = [m.subtotal_estimated_cost for m in all_meals if m.subtotal_estimated_cost is not None]
        if costs:
            total_cost = sum(costs, Decimal(0))
    else:
        # Sum what we have
        costs = [m.subtotal_estimated_cost for m in all_meals if m.subtotal_estimated_cost is not None]
        if costs:
            total_cost = sum(costs, Decimal(0))

    # Day-level warnings
    cal_dev = abs(total_cal - ctx.calorie_target) / max(ctx.calorie_target, 1) * 100
    if cal_dev > OPTIMIZER_PARAMS.calorie_tolerance_pct * 100:
        all_warnings.append(
            f"Daily calories ({total_cal:.0f}) deviate {cal_dev:.0f}% "
            f"from target ({ctx.calorie_target:.0f})"
        )

    if not cost_complete and ctx.daily_budget is not None:
        all_warnings.append("Some foods lack price data; budget estimate is incomplete")

    return DayResult(
        meals=all_meals,
        total_calories=total_cal,
        total_protein_g=total_protein,
        total_carbs_g=total_carbs,
        total_fat_g=total_fat,
        total_estimated_cost=total_cost,
        cost_complete=cost_complete,
        warnings=all_warnings,
    )


def _optimize_meal(
    *,
    slot: MealSlot,
    cal_target: float,
    protein_target: float,
    carb_target: float,
    fat_target: float,
    candidates: list,
    price_per_gram: dict[str, Decimal],
    foods_used_today: dict[str, int],
    categories_used: list[str],
    daily_budget: Decimal | None,
    budget_currency: str | None,
) -> MealResult:
    """Optimize a single meal slot using greedy scoring."""
    warnings: list[str] = []
    selected: list[SelectedFood] = []
    meal_cal = 0.0
    meal_protein = 0.0
    meal_carbs = 0.0
    meal_fat = 0.0

    # Score all candidates for this slot
    scored = _score_candidates(
        candidates=candidates,
        cal_target=cal_target,
        protein_target=protein_target,
        carb_target=carb_target,
        fat_target=fat_target,
        foods_used_today=foods_used_today,
        categories_used=categories_used,
        price_per_gram=price_per_gram,
    )

    # Greedy selection: pick top foods until we fill the slot
    budget_remaining = daily_budget  # simplified — full budget for one meal
    max_attempts = slot.max_foods + 5  # some slack for retry

    for _ in range(max_attempts):
        if len(selected) >= slot.max_foods:
            break

        remaining_cal = cal_target - meal_cal
        if remaining_cal < cal_target * 0.15:
            break  # We've filled >85% of the slot

        best_food = None
        best_score = float("inf")

        for base_score, candidate in scored:
            # Skip already-selected foods
            if any(s.food_id == candidate.food_id for s in selected):
                continue

            # Skip foods used too many times today
            if foods_used_today.get(candidate.slug, 0) >= OPTIMIZER_PARAMS.max_same_food_per_day:
                continue

            # Calculate portion
            portion = _calculate_optimal_portion(
                candidate=candidate,
                remaining_cal=remaining_cal,
                remaining_protein=protein_target - meal_protein,
                remaining_carbs=carb_target - meal_carbs,
                remaining_fat=fat_target - meal_fat,
            )

            if portion is None:
                continue

            # Check budget
            if daily_budget is not None:
                ppg = price_per_gram.get(candidate.food_id)
                if ppg is not None:
                    cost = ppg * Decimal(str(portion.portion_grams))
                    if budget_remaining is not None and cost > budget_remaining:
                        continue

            # Score this selection
            score = _score_selection(
                candidate=candidate,
                portion=portion,
                base_score=base_score,
                remaining_cal=remaining_cal,
                remaining_protein=protein_target - meal_protein,
                remaining_carbs=carb_target - meal_carbs,
                remaining_fat=fat_target - meal_fat,
            )

            if score < best_score:
                best_score = score
                best_food = (candidate, portion)

        if best_food is None:
            break

        candidate, portion = best_food

        # Build the selected food
        ppg = price_per_gram.get(candidate.food_id)
        cost = ppg * Decimal(str(portion.portion_grams)) if ppg else None

        sf = SelectedFood(
            food_id=candidate.food_id,
            name=candidate.name,
            slug=candidate.slug,
            serving_quantity=portion.serving_quantity,
            serving_unit_code=candidate.serving_unit_code,
            portion_grams=portion.portion_grams,
            calories=portion.calories,
            protein_g=portion.protein_g,
            carbs_g=portion.carbs_g,
            fat_g=portion.fat_g,
            estimated_cost=cost,
            cost_available=ppg is not None,
            category_slug=candidate.category_slug,
        )

        selected.append(sf)
        meal_cal += sf.calories
        meal_protein += sf.protein_g
        meal_carbs += sf.carbs_g
        meal_fat += sf.fat_g

        if daily_budget is not None and cost is not None:
            budget_remaining = budget_remaining - cost if budget_remaining else None

    cost_complete = all(s.cost_available for s in selected) if selected else True

    return MealResult(
        meal_type=slot.meal_type,
        foods=selected,
        subtotal_calories=meal_cal,
        subtotal_protein_g=meal_protein,
        subtotal_carbs_g=meal_carbs,
        subtotal_fat_g=meal_fat,
        subtotal_estimated_cost=(
            sum((s.estimated_cost for s in selected if s.estimated_cost is not None), Decimal(0))
            if selected
            else None
        ),
        cost_complete=cost_complete,
        warnings=warnings,
    )


@dataclass
class _Portion:
    """A calculated portion for a food."""

    serving_quantity: float
    portion_grams: float
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float


def _calculate_optimal_portion(
    candidate,
    remaining_cal: float,
    remaining_protein: float,
    remaining_carbs: float,
    remaining_fat: float,
) -> _Portion | None:
    """Calculate the optimal portion size for a candidate food.

    Uses binary search to find the portion that best matches remaining targets.
    """
    # Determine gram bounds
    cat_slug = candidate.category_slug or ""
    max_grams = PORTION_BOUNDS.default_max_grams
    for prefix, bound in PORTION_BOUNDS.category_max_grams.items():
        if cat_slug.startswith(prefix) or candidate.slug.startswith(prefix):
            max_grams = bound
            break

    min_grams = PORTION_BOUNDS.min_inclusion_grams
    if max_grams < min_grams:
        return None

    # Nutrition per gram
    gps = candidate.grams_per_serving if candidate.grams_per_serving > 0 else 100.0
    cal_per_g = candidate.calories_per_serving / gps
    pro_per_g = candidate.protein_per_serving / gps
    carb_per_g = candidate.carbs_per_serving / gps
    fat_per_g = candidate.fat_per_serving / gps

    # Find best portion: prefer matching calories, with macro secondary
    best_grams = min_grams
    best_cost = float("inf")

    # Step through portions (coarse grid for efficiency)
    step = max(10.0, (max_grams - min_grams) / 15)
    grams = min_grams
    while grams <= max_grams:
        cal = cal_per_g * grams
        pro = pro_per_g * grams
        carb = carb_per_g * grams
        fat = fat_per_g * grams

        # Score: how well does this portion serve remaining targets?
        cal_err = abs(cal - remaining_cal) / max(remaining_cal, 1)
        pro_err = abs(pro - remaining_protein) / max(remaining_protein, 1)
        carb_err = abs(carb - remaining_carbs) / max(remaining_carbs, 1)
        fat_err = abs(fat - remaining_fat) / max(remaining_fat, 1)

        cost = cal_err * 0.4 + pro_err * 0.3 + carb_err * 0.15 + fat_err * 0.15

        if cost < best_cost:
            best_cost = cost
            best_grams = grams

        grams += step

    # Refine with finer grid around best
    fine_min = max(min_grams, best_grams - step)
    fine_max = min(max_grams, best_grams + step)
    fine_step = max(1.0, step / 10)
    grams = fine_min
    while grams <= fine_max:
        cal = cal_per_g * grams
        pro = pro_per_g * grams
        carb = carb_per_g * grams
        fat = fat_per_g * grams

        cal_err = abs(cal - remaining_cal) / max(remaining_cal, 1)
        pro_err = abs(pro - remaining_protein) / max(remaining_protein, 1)
        carb_err = abs(carb - remaining_carbs) / max(remaining_carbs, 1)
        fat_err = abs(fat - remaining_fat) / max(remaining_fat, 1)

        cost = cal_err * 0.4 + pro_err * 0.3 + carb_err * 0.15 + fat_err * 0.15

        if cost < best_cost:
            best_cost = cost
            best_grams = grams

        grams += fine_step

    serving_qty = best_grams / gps if gps > 0 else 1.0

    return _Portion(
        serving_quantity=round(serving_qty, 2),
        portion_grams=round(best_grams, 1),
        calories=round(cal_per_g * best_grams, 1),
        protein_g=round(pro_per_g * best_grams, 2),
        carbs_g=round(carb_per_g * best_grams, 2),
        fat_g=round(fat_per_g * best_grams, 2),
    )


def _score_candidates(
    *,
    candidates: list,
    cal_target: float,
    protein_target: float,
    carb_target: float,
    fat_target: float,
    foods_used_today: dict[str, int],
    categories_used: list[str],
    price_per_gram: dict[str, Decimal],
) -> list[tuple[float, object]]:
    """Score all candidates and return sorted (score, candidate) pairs.

    Lower score = better candidate.
    """
    scored = []
    w = SCORING_WEIGHTS

    for c in candidates:
        # Base nutrition alignment score (0–1, lower is better)
        cal_score = _normalize_deviation(c.calories_per_serving, cal_target * 0.3)
        pro_score = _normalize_deviation(c.protein_per_serving, protein_target * 0.3)

        nutrition_score = (
            cal_score * w.calorie_deviation
            + pro_score * w.protein_deviation
        )

        # Preference bonus
        pref_penalty = 0.0
        if c.is_disliked:
            pref_penalty = 1.0
        elif c.is_liked:
            pref_penalty = -0.3  # Bonus (negative cost)

        # Variety penalty
        variety = 0.0
        count = foods_used_today.get(c.slug, 0)
        if count > 0:
            variety = w.variety_penalty * count * 0.5

        # Category variety
        if c.category_slug and c.category_slug in categories_used:
            variety += 0.02

        total = (
            nutrition_score
            + w.preference_penalty * pref_penalty
            + variety
        )

        scored.append((total, c))

    scored.sort(key=lambda x: x[0])
    return scored


def _normalize_deviation(value: float, target: float) -> float:
    """Normalize how well a value matches a target to [0, 1]."""
    if target <= 0:
        return 0.0
    deviation = abs(value - target) / target
    return min(deviation, 1.0)



def _score_selection(
    *,
    candidate,
    portion: _Portion,
    base_score: float,
    remaining_cal: float,
    remaining_protein: float,
    remaining_carbs: float,
    remaining_fat: float,
) -> float:
    """Score a specific food+portion combination against remaining targets."""
    w = SCORING_WEIGHTS

    # How well does this portion fill remaining targets?
    cal_fill = portion.calories / max(remaining_cal, 1)
    pro_fill = portion.protein_g / max(remaining_protein, 1)

    # Penalize over-filling (going over target is worse than under)
    cal_penalty = max(0, cal_fill - 1.0) * 2.0
    pro_penalty = max(0, pro_fill - 1.0) * 1.5

    # Reward filling a good fraction (not too small)
    fill_score = 0.0
    if cal_fill < 0.1:
        fill_score = 0.3  # Too small, waste of a food slot
    elif cal_fill > 1.5:
        fill_score = 0.2  # Too large, unrealistic

    score = (
        base_score * 0.4
        + w.calorie_deviation * cal_penalty
        + w.protein_deviation * pro_penalty
        + fill_score
    )

    return score
