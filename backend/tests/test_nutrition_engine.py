"""Tests for the nutrition calculation engine.

Covers: BMR, TDEE, calorie targets, macronutrients, safety bounds,
goal adjustments, edge cases, and macro consistency.
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-1234567890abcdefg")
os.environ.setdefault("CSRF_SECRET_KEY", "test-csrf-secret-key-1234567890abcdef")
os.environ.setdefault("ENVIRONMENT", "testing")

from app.services.nutrition_config import (
    ACTIVITY_MULTIPLIERS,
    CARBS_KCAL_PER_G,
    FAT_KCAL_PER_G,
    GOAL_ADJUSTMENTS,
    PROTEIN_KCAL_PER_G,
    SAFETY_BOUNDS,
)
from app.services.nutrition_service import (
    calculate_bmr,
    calculate_calorie_target,
    calculate_macros,
    calculate_nutrition_targets,
    calculate_tdee,
)

# ── BMR calculations ────────────────────────────────────────────────────────


class TestBMR:
    def test_male_bmr(self):
        """Mifflin-St Jeor male: 10*w + 6.25*h - 5*age - 5"""
        bmr, warnings = calculate_bmr("male", 30, 175, 70)
        expected = 10 * 70 + 6.25 * 175 - 5 * 30 - 5  # 1646.25
        assert abs(bmr - expected) < 0.01
        assert len(warnings) == 0

    def test_female_bmr(self):
        """Mifflin-St Jeor female: 10*w + 6.25*h - 5*age - 161"""
        bmr, warnings = calculate_bmr("female", 25, 160, 55)
        expected = 10 * 55 + 6.25 * 160 - 5 * 25 - 161  # 1274.0
        assert abs(bmr - expected) < 0.01
        assert len(warnings) == 0

    def test_other_sex_averages_male_female(self):
        """Other/prefer-not-to-say should average male and female formulas."""
        bmr_male, _ = calculate_bmr("male", 30, 175, 70)
        bmr_female, _ = calculate_bmr("female", 30, 175, 70)
        bmr_other, warnings = calculate_bmr("other", 30, 175, 70)
        assert abs(bmr_other - (bmr_male + bmr_female) / 2) < 0.01
        assert len(warnings) == 1
        assert "average" in warnings[0].lower()

    def test_bmr_positive(self):
        """BMR should always be positive for valid inputs."""
        bmr, _ = calculate_bmr("male", 30, 175, 70)
        assert bmr > 0

    def test_bmr_increases_with_weight(self):
        """Heavier person should have higher BMR."""
        bmr_light, _ = calculate_bmr("male", 30, 175, 60)
        bmr_heavy, _ = calculate_bmr("male", 30, 175, 90)
        assert bmr_heavy > bmr_light


# ── TDEE calculations ───────────────────────────────────────────────────────


class TestTDEE:
    def test_sedentary_multiplier(self):
        tdee = calculate_tdee(1646.25, "sedentary")
        assert abs(tdee - 1646.25 * 1.2) < 0.01

    def test_very_active_multiplier(self):
        tdee = calculate_tdee(1646.25, "very_active")
        assert abs(tdee - 1646.25 * 1.725) < 0.01

    def test_all_activity_levels_produce_different_tdee(self):
        bmr = 1500.0
        tdees = {}
        for level in ["sedentary", "lightly_active", "moderately_active", "very_active", "extra_active"]:
            tdees[level] = calculate_tdee(bmr, level)
        # All should be different
        assert len(set(tdees.values())) == 5

    def test_tdee_increases_with_activity(self):
        bmr = 1500.0
        assert calculate_tdee(bmr, "sedentary") < calculate_tdee(bmr, "extra_active")

    def test_unknown_activity_defaults_to_sedentary(self):
        tdee = calculate_tdee(1500.0, "unknown_level")
        assert abs(tdee - 1500.0 * 1.2) < 0.01


# ── Calorie target calculations ─────────────────────────────────────────────


class TestCalorieTarget:
    def test_general_fitness_no_adjustment(self):
        target, adj, bounded, warnings = calculate_calorie_target(2000.0, "general_fitness")
        assert adj == 0
        assert target == 2000.0
        assert not bounded
        assert len(warnings) == 0

    def test_weight_loss_deficit(self):
        target, adj, _bounded, _warnings = calculate_calorie_target(2000.0, "weight_loss")
        assert adj == -500
        assert target == 1500.0

    def test_weight_gain_surplus(self):
        target, adj, _bounded, _warnings = calculate_calorie_target(2000.0, "weight_gain")
        assert adj == 400
        assert target == 2400.0

    def test_muscle_building_surplus(self):
        target, adj, _bounded, _warnings = calculate_calorie_target(2000.0, "muscle_building")
        assert adj == 300
        assert target == 2300.0

    def test_bounded_below_minimum(self):
        """Very low TDEE with weight loss should be bounded."""
        target, _adj, bounded, warnings = calculate_calorie_target(800.0, "weight_loss")
        assert bounded
        assert target == SAFETY_BOUNDS.min_calories
        assert any("minimum" in w.lower() or "below" in w.lower() for w in warnings)

    def test_bounded_above_maximum(self):
        """Very high TDEE with weight gain should be bounded."""
        # 5000 + 400 = 5400 which is under max_calories (6000), so use 6500
        target, _adj, bounded, warnings = calculate_calorie_target(6000.0, "weight_gain")
        assert bounded
        assert target == SAFETY_BOUNDS.max_calories
        assert any("maximum" in w.lower() or "exceeds" in w.lower() for w in warnings)


# ── Macronutrient calculations ──────────────────────────────────────────────


class TestMacros:
    def test_macros_sum_to_calories(self):
        """Protein + carbs + fat calories should sum to the target."""
        protein_g, carbs_g, fat_g, _warnings = calculate_macros(2000.0, 70, "general_fitness")
        total = (
            protein_g * PROTEIN_KCAL_PER_G
            + carbs_g * CARBS_KCAL_PER_G
            + fat_g * FAT_KCAL_PER_G
        )
        assert abs(total - 2000.0) < 1.0

    def test_macros_all_positive(self):
        protein_g, carbs_g, fat_g, _ = calculate_macros(2000.0, 70, "general_fitness")
        assert protein_g > 0
        assert carbs_g > 0
        assert fat_g > 0

    def test_protein_higher_for_muscle_building(self):
        """Muscle building should have more protein per kg than general fitness."""
        pro_muscle, _, _, _ = calculate_macros(2000.0, 70, "muscle_building")
        pro_general, _, _, _ = calculate_macros(2000.0, 70, "general_fitness")
        assert pro_muscle > pro_general

    def test_protein_higher_for_weight_loss(self):
        """Weight loss should have higher protein than general fitness."""
        pro_loss, _, _, _ = calculate_macros(2000.0, 70, "weight_loss")
        pro_general, _, _, _ = calculate_macros(2000.0, 70, "general_fitness")
        assert pro_loss > pro_general

    def test_heavier_person_gets_more_protein(self):
        """Heavier person should get more protein (per-kg basis)."""
        pro_light, _, _, _ = calculate_macros(2000.0, 55, "general_fitness")
        pro_heavy, _, _, _ = calculate_macros(2000.0, 90, "general_fitness")
        assert pro_heavy > pro_light


# ── Safety bounds ───────────────────────────────────────────────────────────


class TestSafetyBounds:
    def test_extreme_young_age_clamped(self):
        result = calculate_nutrition_targets("male", 5, 175, 70, "sedentary", "general_fitness")
        assert result.age == SAFETY_BOUNDS.min_age
        assert any("age" in w.lower() for w in result.warnings)

    def test_extreme_old_age_clamped(self):
        result = calculate_nutrition_targets("male", 120, 175, 70, "sedentary", "general_fitness")
        assert result.age == SAFETY_BOUNDS.max_age
        assert any("age" in w.lower() for w in result.warnings)

    def test_zero_height_clamped(self):
        result = calculate_nutrition_targets("male", 30, 0, 70, "sedentary", "general_fitness")
        assert result.height_cm == SAFETY_BOUNDS.min_height_cm
        assert any("height" in w.lower() for w in result.warnings)

    def test_extreme_height_clamped(self):
        result = calculate_nutrition_targets("male", 30, 300, 70, "sedentary", "general_fitness")
        assert result.height_cm == SAFETY_BOUNDS.max_height_cm

    def test_zero_weight_clamped(self):
        result = calculate_nutrition_targets("male", 30, 175, 0, "sedentary", "general_fitness")
        assert result.weight_kg == SAFETY_BOUNDS.min_weight_kg
        assert any("weight" in w.lower() for w in result.warnings)

    def test_extreme_weight_clamped(self):
        result = calculate_nutrition_targets("male", 30, 175, 400, "sedentary", "general_fitness")
        assert result.weight_kg == SAFETY_BOUNDS.max_weight_kg

    def test_valid_profile_no_warnings(self):
        """A valid profile should produce no input clamping warnings."""
        result = calculate_nutrition_targets("male", 30, 175, 70, "moderately_active", "general_fitness")
        clamping_warnings = [w for w in result.warnings if "outside" in w.lower() or "clamping" in w.lower()]
        assert len(clamping_warnings) == 0


# ── Full target calculation ─────────────────────────────────────────────────


class TestFullCalculation:
    def test_reasonable_male_profile(self):
        result = calculate_nutrition_targets("male", 30, 175, 70, "moderately_active", "general_fitness")
        assert 1500 <= result.calorie_target <= 3500
        assert 50 <= result.protein_g <= 300
        assert 100 <= result.carbs_g <= 600
        assert 30 <= result.fat_g <= 200
        assert result.bmr > 0
        assert result.tdee > result.bmr

    def test_reasonable_female_profile(self):
        result = calculate_nutrition_targets("female", 28, 163, 58, "lightly_active", "weight_loss")
        assert 1200 <= result.calorie_target <= 3000
        assert result.goal_adjustment == -500

    def test_weight_loss_fewer_calories_than_maintenance(self):
        result_loss = calculate_nutrition_targets("male", 30, 175, 70, "moderately_active", "weight_loss")
        result_maint = calculate_nutrition_targets("male", 30, 175, 70, "moderately_active", "general_fitness")
        assert result_loss.calorie_target < result_maint.calorie_target

    def test_weight_gain_more_calories_than_maintenance(self):
        result_gain = calculate_nutrition_targets("male", 30, 175, 70, "moderately_active", "weight_gain")
        result_maint = calculate_nutrition_targets("male", 30, 175, 70, "moderately_active", "general_fitness")
        assert result_gain.calorie_target > result_maint.calorie_target

    def test_deterministic(self):
        """Same inputs should always produce the same outputs."""
        args = ("female", 25, 160, 55, "very_active", "muscle_building")
        r1 = calculate_nutrition_targets(*args)
        r2 = calculate_nutrition_targets(*args)
        assert r1.calorie_target == r2.calorie_target
        assert r1.protein_g == r2.protein_g
        assert r1.carbs_g == r2.carbs_g
        assert r1.fat_g == r2.fat_g

    def test_metadata_preserved(self):
        """The result should echo back the inputs used."""
        result = calculate_nutrition_targets("male", 30, 175, 70, "sedentary", "general_fitness")
        assert result.sex == "male"
        assert result.age == 30
        assert result.height_cm == 175
        assert result.weight_kg == 70
        assert result.activity_level == "sedentary"
        assert result.goal == "general_fitness"

    def test_bounded_flag_set_when_clamped(self):
        result = calculate_nutrition_targets("male", 30, 175, 70, "sedentary", "weight_loss")
        # Low TDEE * 1.2 - 500 could be below minimum depending on profile
        if result.is_bounded:
            assert any("minimum" in w.lower() or "below" in w.lower() for w in result.warnings)


# ── Configuration consistency ───────────────────────────────────────────────


class TestConfiguration:
    def test_all_activity_levels_covered(self):
        for level in ["sedentary", "lightly_active", "moderately_active", "very_active", "extra_active"]:
            mult = ACTIVITY_MULTIPLIERS.for_level(level)
            assert mult > 1.0, f"Multiplier for {level} should be > 1.0"

    def test_all_goals_covered(self):
        for goal in ["weight_loss", "weight_gain", "muscle_building", "general_fitness"]:
            adj = GOAL_ADJUSTMENTS.for_goal(goal)
            assert isinstance(adj, (int, float))

    def test_weight_loss_deficit(self):
        assert GOAL_ADJUSTMENTS.for_goal("weight_loss") < 0

    def test_weight_gain_surplus(self):
        assert GOAL_ADJUSTMENTS.for_goal("weight_gain") > 0

    def test_caloric_values_correct(self):
        assert PROTEIN_KCAL_PER_G == 4.0
        assert CARBS_KCAL_PER_G == 4.0
        assert FAT_KCAL_PER_G == 9.0

    def test_safety_bounds_sensible(self):
        assert SAFETY_BOUNDS.min_age >= 14
        assert SAFETY_BOUNDS.max_age <= 120
        assert SAFETY_BOUNDS.min_height_cm > 50
        assert SAFETY_BOUNDS.max_height_cm < 300
        assert SAFETY_BOUNDS.min_weight_kg > 10
        assert SAFETY_BOUNDS.max_weight_kg < 500
        assert SAFETY_BOUNDS.min_calories >= 500
        assert SAFETY_BOUNDS.max_calories <= 10000
