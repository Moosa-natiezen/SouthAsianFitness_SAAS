"""Nutrition calculation service.

Calculates BMR, TDEE, calorie targets, and macronutrient distributions
based on a user's profile, activity level, and fitness goal.

Formulas:
- BMR: Mifflin-St Jeor equation (1990)
  Male:   BMR = 10 × weight_kg + 6.25 × height_cm - 5 × age - 5
  Female: BMR = 10 × weight_kg + 6.25 × height_cm - 5 × age - 161
- TDEE: BMR × activity_multiplier (Harris-Benedict revised)
- Target calories: TDEE + goal_adjustment

All assumptions are in nutrition_config.py.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.services.nutrition_config import (
    ACTIVITY_MULTIPLIERS,
    CARBS_KCAL_PER_G,
    FAT_KCAL_PER_G,
    GOAL_ADJUSTMENTS,
    MACRO_RATIOS,
    PROTEIN_KCAL_PER_G,
    SAFETY_BOUNDS,
)


@dataclass
class NutritionTarget:
    """Deterministic nutrition target result."""

    calorie_target: float
    protein_g: float
    carbs_g: float
    fat_g: float
    bmr: float
    tdee: float
    goal_adjustment: float
    is_bounded: bool
    warnings: list[str]
    # Metadata
    sex: str
    age: int
    height_cm: float
    weight_kg: float
    activity_level: str
    goal: str


def calculate_bmr(
    sex: str,
    age: int,
    height_cm: float,
    weight_kg: float,
) -> tuple[float, list[str]]:
    """Calculate Basal Metabolic Rate using Mifflin-St Jeor equation.

    Returns (bmr, warnings).
    """
    warnings = []

    if sex == "male":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 5
    elif sex == "female":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    else:
        # For other/prefer-not-to-say, use average of male and female
        bmr_male = 10 * weight_kg + 6.25 * height_cm - 5 * age - 5
        bmr_female = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
        bmr = (bmr_male + bmr_female) / 2
        warnings.append(
            f"Sex '{sex}' not directly supported by Mifflin-St Jeor; "
            "using average of male and female formulas."
        )

    return bmr, warnings


def calculate_tdee(bmr: float, activity_level: str) -> float:
    """Calculate Total Daily Energy Expenditure."""
    multiplier = ACTIVITY_MULTIPLIERS.for_level(activity_level)
    return bmr * multiplier


def calculate_calorie_target(
    tdee: float,
    goal: str,
    *,
    min_cal: float = SAFETY_BOUNDS.min_calories,
    max_cal: float = SAFETY_BOUNDS.max_calories,
) -> tuple[float, float, bool, list[str]]:
    """Calculate target calories with goal adjustment and safety bounds.

    Returns (target_calories, adjustment_applied, is_bounded, warnings).
    """
    warnings = []
    adjustment = GOAL_ADJUSTMENTS.for_goal(goal)

    # Clamp adjustment to safety bounds
    raw_adjustment = adjustment
    adjustment = max(
        SAFETY_BOUNDS.min_calorie_adjustment,
        min(SAFETY_BOUNDS.max_calorie_adjustment, adjustment),
    )
    if adjustment != raw_adjustment:
        warnings.append(
            f"Goal adjustment clamped from {raw_adjustment:.0f} to {adjustment:.0f} kcal."
        )

    target = tdee + adjustment
    is_bounded = False

    if target < min_cal:
        warnings.append(
            f"Calorie target {target:.0f} kcal is below minimum {min_cal:.0f} kcal. "
            f"Using {min_cal:.0f} kcal."
        )
        target = min_cal
        is_bounded = True
    elif target > max_cal:
        warnings.append(
            f"Calorie target {target:.0f} kcal exceeds maximum {max_cal:.0f} kcal. "
            f"Using {max_cal:.0f} kcal."
        )
        target = max_cal
        is_bounded = True

    return target, adjustment, is_bounded, warnings


def calculate_macros(
    calorie_target: float,
    weight_kg: float,
    goal: str,
) -> tuple[float, float, float, list[str]]:
    """Calculate macronutrient targets.

    Returns (protein_g, carbs_g, fat_g, warnings).
    """
    warnings = []

    # Protein
    pro_min, pro_max = MACRO_RATIOS.protein_per_kg.get(goal, (1.2, 1.6))
    protein_per_kg = (pro_min + pro_max) / 2
    protein_g = weight_kg * protein_per_kg
    protein_kcal = protein_g * PROTEIN_KCAL_PER_G

    # Fat
    fat_min_frac, fat_max_frac = MACRO_RATIOS.fat_fraction.get(goal, (0.20, 0.35))
    fat_fraction = (fat_min_frac + fat_max_frac) / 2
    fat_g = (calorie_target * fat_fraction) / FAT_KCAL_PER_G
    fat_kcal = fat_g * FAT_KCAL_PER_G

    # Carbs fill remainder
    remaining_kcal = calorie_target - protein_kcal - fat_kcal
    if remaining_kcal < 0:
        warnings.append(
            f"Protein + fat calories ({protein_kcal + fat_kcal:.0f}) exceed "
            f"total target ({calorie_target:.0f}). Reducing fat."
        )
        fat_g = max(0, (calorie_target - protein_kcal) / FAT_KCAL_PER_G)
        fat_kcal = fat_g * FAT_KCAL_PER_G
        remaining_kcal = calorie_target - protein_kcal - fat_kcal

    carbs_g = remaining_kcal / CARBS_KCAL_PER_G

    # Verify internal consistency
    total_kcal = (
        protein_g * PROTEIN_KCAL_PER_G
        + carbs_g * CARBS_KCAL_PER_G
        + fat_g * FAT_KCAL_PER_G
    )
    if abs(total_kcal - calorie_target) > 1.0:
        warnings.append(
            f"Macro calorie sum ({total_kcal:.0f}) differs from target "
            f"({calorie_target:.0f}) by {abs(total_kcal - calorie_target):.1f} kcal."
        )

    return protein_g, carbs_g, fat_g, warnings


def calculate_nutrition_targets(
    sex: str,
    age: int,
    height_cm: float,
    weight_kg: float,
    activity_level: str,
    goal: str,
) -> NutritionTarget:
    """Calculate complete nutrition targets from user profile.

    Validates inputs, calculates BMR → TDEE → calorie target → macros.
    Returns a NutritionTarget with all results and warnings.
    """
    all_warnings: list[str] = []

    # Input validation
    if age < SAFETY_BOUNDS.min_age or age > SAFETY_BOUNDS.max_age:
        all_warnings.append(
            f"Age {age} is outside typical range "
            f"({SAFETY_BOUNDS.min_age}-{SAFETY_BOUNDS.max_age}). "
            f"Clamping."
        )
        age = max(SAFETY_BOUNDS.min_age, min(SAFETY_BOUNDS.max_age, age))

    if height_cm < SAFETY_BOUNDS.min_height_cm or height_cm > SAFETY_BOUNDS.max_height_cm:
        all_warnings.append(
            f"Height {height_cm} cm is outside range "
            f"({SAFETY_BOUNDS.min_height_cm}-{SAFETY_BOUNDS.max_height_cm} cm). "
            f"Clamping."
        )
        height_cm = max(SAFETY_BOUNDS.min_height_cm, min(SAFETY_BOUNDS.max_height_cm, height_cm))

    if weight_kg < SAFETY_BOUNDS.min_weight_kg or weight_kg > SAFETY_BOUNDS.max_weight_kg:
        all_warnings.append(
            f"Weight {weight_kg} kg is outside range "
            f"({SAFETY_BOUNDS.min_weight_kg}-{SAFETY_BOUNDS.max_weight_kg} kg). "
            f"Clamping."
        )
        weight_kg = max(SAFETY_BOUNDS.min_weight_kg, min(SAFETY_BOUNDS.max_weight_kg, weight_kg))

    # BMR
    bmr, bmr_warnings = calculate_bmr(sex, age, height_cm, weight_kg)
    all_warnings.extend(bmr_warnings)

    # TDEE
    tdee = calculate_tdee(bmr, activity_level)

    # Calorie target
    calorie_target, adjustment, is_bounded, cal_warnings = calculate_calorie_target(tdee, goal)
    all_warnings.extend(cal_warnings)

    # Macros
    protein_g, carbs_g, fat_g, macro_warnings = calculate_macros(
        calorie_target, weight_kg, goal
    )
    all_warnings.extend(macro_warnings)

    # Round to reasonable precision
    calorie_target = round(calorie_target, 0)
    protein_g = round(protein_g, 1)
    carbs_g = round(carbs_g, 1)
    fat_g = round(fat_g, 1)
    bmr = round(bmr, 1)
    tdee = round(tdee, 1)

    return NutritionTarget(
        calorie_target=calorie_target,
        protein_g=protein_g,
        carbs_g=carbs_g,
        fat_g=fat_g,
        bmr=bmr,
        tdee=tdee,
        goal_adjustment=adjustment,
        is_bounded=is_bounded,
        warnings=all_warnings,
        sex=sex,
        age=age,
        height_cm=height_cm,
        weight_kg=weight_kg,
        activity_level=activity_level,
        goal=goal,
    )
