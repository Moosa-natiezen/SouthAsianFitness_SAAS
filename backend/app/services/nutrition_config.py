"""Nutrition calculation configuration.

All magic numbers, formulas, and assumptions are defined here in one place.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ActivityMultipliers:
    """Harris-Benedict revised activity multipliers for TDEE calculation."""

    sedentary: float = 1.2
    lightly_active: float = 1.375
    moderately_active: float = 1.55
    very_active: float = 1.725
    extra_active: float = 1.9

    def for_level(self, level: str) -> float:
        mapping = {
            "sedentary": self.sedentary,
            "lightly_active": self.lightly_active,
            "moderately_active": self.moderately_active,
            "very_active": self.very_active,
            "extra_active": self.extra_active,
        }
        return mapping.get(level, self.sedentary)


@dataclass(frozen=True)
class GoalAdjustments:
    """Daily calorie adjustments by fitness goal (kcal)."""

    weight_loss: float = -500
    weight_gain: float = 400
    muscle_building: float = 300
    general_fitness: float = 0

    def for_goal(self, goal: str) -> float:
        mapping = {
            "weight_loss": self.weight_loss,
            "weight_gain": self.weight_gain,
            "muscle_building": self.muscle_building,
            "general_fitness": self.general_fitness,
        }
        return mapping.get(goal, 0.0)


@dataclass(frozen=True)
class MacroRatios:
    """Protein and fat targets as fraction of total calories, per goal.

    Carbs fill the remainder.
    """

    # protein_g per kg of body weight (min, max)
    protein_per_kg: dict[str, tuple[float, float]] = field(default_factory=lambda: {
        "weight_loss": (1.6, 2.2),
        "weight_gain": (1.4, 1.8),
        "muscle_building": (1.8, 2.4),
        "general_fitness": (1.2, 1.6),
    })
    # fat as fraction of total calories (min, max)
    fat_fraction: dict[str, tuple[float, float]] = field(default_factory=lambda: {
        "weight_loss": (0.20, 0.35),
        "weight_gain": (0.20, 0.35),
        "muscle_building": (0.20, 0.30),
        "general_fitness": (0.20, 0.35),
    })


@dataclass(frozen=True)
class SafetyBounds:
    """Safety boundaries for inputs and outputs."""

    min_age: int = 14
    max_age: int = 100
    min_height_cm: float = 100.0
    max_height_cm: float = 250.0
    min_weight_kg: float = 30.0
    max_weight_kg: float = 300.0
    min_calories: float = 1000.0
    max_calories: float = 6000.0
    min_calorie_adjustment: float = -1500.0
    max_calorie_adjustment: float = 1500.0


# Global configuration instances
ACTIVITY_MULTIPLIERS = ActivityMultipliers()
GOAL_ADJUSTMENTS = GoalAdjustments()
MACRO_RATIOS = MacroRatios()
SAFETY_BOUNDS = SafetyBounds()

# Caloric values per gram
PROTEIN_KCAL_PER_G = 4.0
CARBS_KCAL_PER_G = 4.0
FAT_KCAL_PER_G = 9.0
