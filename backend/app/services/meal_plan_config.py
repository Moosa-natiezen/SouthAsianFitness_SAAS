"""Meal plan generation configuration.

All magic numbers, scoring weights, portion bounds, meal structure,
and optimization parameters are defined here in one place.

The optimizer minimizes a weighted cost function. Lower cost = better plan.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ── Scoring weights (lower is better) ───────────────────────────────────────
# Each term is normalized to [0, 1] before weighting, except preference
# and variety penalties which are already in [0, 1] range.


@dataclass(frozen=True)
class ScoringWeights:
    """Weights for the meal plan optimization scoring function.

    All terms are designed so the optimizer minimizes total cost.
    A value of 0 disables a scoring term.
    """

    # Nutrition deviation (normalized 0–1 per macro, then averaged)
    calorie_deviation: float = 0.35
    protein_deviation: float = 0.20
    carb_deviation: float = 0.15
    fat_deviation: float = 0.10

    # Budget
    budget_deviation: float = 0.10

    # Penalties (0–1 range each)
    variety_penalty: float = 0.05
    preference_penalty: float = 0.05


# ── Portion boundaries ──────────────────────────────────────────────────────


@dataclass(frozen=True)
class PortionBounds:
    """Configurable portion boundaries per food category.

    Values are in grams. These prevent unrealistic quantities.
    If a target cannot be reached within these bounds, a warning is emitted.
    """

    # Default bounds for any food
    default_min_grams: float = 20.0
    default_max_grams: float = 500.0

    # Category-specific overrides (by slug prefix or category name)
    # These are applied as max values
    category_max_grams: dict[str, float] = field(default_factory=lambda: {
        "rice": 400.0,
        "roti": 200.0,  # ~3 rotis
        "chapati": 200.0,
        "paratha": 200.0,
        "naan": 200.0,
        "chicken": 300.0,
        "beef": 250.0,
        "mutton": 250.0,
        "fish": 250.0,
        "egg": 150.0,   # ~3 eggs
        "lentil": 300.0,
        "daal": 300.0,
        "dal": 300.0,
        "yogurt": 300.0,
        "curd": 300.0,
        "milk": 500.0,
        "oil": 30.0,
        "ghee": 30.0,
        "butter": 30.0,
        "sugar": 30.0,
        "salt": 5.0,
        "fruit": 300.0,
        "vegetable": 400.0,
        "bread": 200.0,
        "snack": 100.0,
    })

    # Minimum grams for a food to be included (skip trivial amounts)
    min_inclusion_grams: float = 10.0


# ── Meal structure ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class MealSlot:
    """Definition of a meal slot in the daily structure."""

    meal_type: str  # breakfast, lunch, snack, dinner
    calorie_fraction: float  # fraction of daily calories (must sum to ~1.0)
    min_foods: int = 1
    max_foods: int = 3


@dataclass(frozen=True)
class MealStructure:
    """Configurable daily meal structure.

    calorie_fractions should sum to 1.0.
    """

    slots: tuple[MealSlot, ...] = (
        MealSlot(meal_type="breakfast", calorie_fraction=0.25, min_foods=1, max_foods=2),
        MealSlot(meal_type="lunch", calorie_fraction=0.35, min_foods=2, max_foods=3),
        MealSlot(meal_type="snack", calorie_fraction=0.10, min_foods=1, max_foods=2),
        MealSlot(meal_type="dinner", calorie_fraction=0.30, min_foods=2, max_foods=3),
    )

    def validate(self) -> list[str]:
        """Validate that fractions sum to ~1.0."""
        warnings = []
        total = sum(s.calorie_fraction for s in self.slots)
        if abs(total - 1.0) > 0.05:
            warnings.append(
                f"Meal calorie fractions sum to {total:.2f}, expected ~1.0"
            )
        return warnings


# ── Optimization parameters ─────────────────────────────────────────────────


@dataclass(frozen=True)
class OptimizerParams:
    """Parameters controlling the optimization algorithm."""

    # Maximum foods to consider per meal slot (top-N candidates)
    max_candidates_per_slot: int = 50

    # Maximum portion iterations (to avoid brute force)
    max_portion_iterations: int = 200

    # Calorie tolerance: plans within this % of target are acceptable
    calorie_tolerance_pct: float = 0.10  # ±10%

    # Macro tolerance: plans within this % of target are acceptable
    macro_tolerance_pct: float = 0.15  # ±15%

    # Maximum days supported
    max_plan_days: int = 30

    # Default plan days
    default_plan_days: int = 1

    # Minimum unique foods across the full day
    min_unique_foods_per_day: int = 4

    # Maximum repetition of the same food across meals in a day
    max_same_food_per_day: int = 2


# ── Diet pattern food exclusions ────────────────────────────────────────────
# Foods that violate a diet pattern are always excluded.
# This maps diet patterns to excluded food category slugs or keywords.


@dataclass(frozen=True)
class DietExclusions:
    """Food exclusions based on dietary pattern."""

    vegetarian_exclude_categories: frozenset[str] = frozenset({
        "meats", "poultry", "fish",
    })

    vegan_exclude_categories: frozenset[str] = frozenset({
        "meats", "poultry", "fish", "dairy", "eggs",
    })

    eggetarian_exclude_categories: frozenset[str] = frozenset({
        "meats", "poultry", "fish",
    })

    pescetarian_exclude_categories: frozenset[str] = frozenset({
        "meats", "poultry",
    })


# ── Global configuration instances ──────────────────────────────────────────

SCORING_WEIGHTS = ScoringWeights()
PORTION_BOUNDS = PortionBounds()
DEFAULT_MEAL_STRUCTURE = MealStructure()
OPTIMIZER_PARAMS = OptimizerParams()
DIET_EXCLUSIONS = DietExclusions()
