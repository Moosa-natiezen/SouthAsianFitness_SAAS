"""Tests for the budget calculation service.

Covers: budget normalization, daily/weekly/monthly conversions,
missing data handling, validation, and meal budget checks.
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-1234567890abcdefg")
os.environ.setdefault("CSRF_SECRET_KEY", "test-csrf-secret-key-1234567890abcdef")
os.environ.setdefault("ENVIRONMENT", "testing")

from decimal import Decimal

from app.services.budget_service import (
    calculate_budget_targets,
    check_meal_budget,
    normalize_budget_to_daily,
)

# ── Budget normalization ────────────────────────────────────────────────────


class TestBudgetNormalization:
    def test_daily_stays_same(self):
        result, warnings = normalize_budget_to_daily(Decimal(100), "daily")
        assert result == Decimal(100)
        assert len(warnings) == 0

    def test_weekly_to_daily(self):
        result, warnings = normalize_budget_to_daily(Decimal(700), "weekly")
        assert result == Decimal(100)
        assert len(warnings) == 0

    def test_monthly_to_daily(self):
        result, _warnings = normalize_budget_to_daily(Decimal(3000), "monthly")
        assert result == Decimal(100)

    def test_yearly_to_daily(self):
        result, _warnings = normalize_budget_to_daily(Decimal(36500), "yearly")
        assert result == Decimal(100)

    def test_unknown_period_warns(self):
        _result, warnings = normalize_budget_to_daily(Decimal(700), "fortnightly")
        assert len(warnings) == 1
        assert "fortnightly" in warnings[0].lower()

    def test_case_insensitive_period(self):
        result, _ = normalize_budget_to_daily(Decimal(700), "Weekly")
        assert result == Decimal(100)


# ── Budget target calculation ───────────────────────────────────────────────


class TestBudgetTargets:
    def test_weekly_budget(self):
        result = calculate_budget_targets(
            weekly_budget_amount=Decimal(700),
            currency_code="PKR",
            country_id=None,
            region_id=None,
        )
        assert result.daily_budget == Decimal("100.00")
        assert result.weekly_budget == Decimal("700.00")
        assert result.monthly_budget is not None
        assert result.monthly_budget > result.weekly_budget
        assert result.currency_code == "PKR"
        assert len(result.warnings) == 0

    def test_zero_budget_returns_none(self):
        result = calculate_budget_targets(
            weekly_budget_amount=Decimal(0),
            currency_code="PKR",
            country_id=None,
            region_id=None,
        )
        assert result.daily_budget is None
        assert result.weekly_budget is None

    def test_negative_budget_returns_none(self):
        result = calculate_budget_targets(
            weekly_budget_amount=Decimal(-100),
            currency_code="PKR",
            country_id=None,
            region_id=None,
        )
        assert result.daily_budget is None
        assert result.weekly_budget is None

    def test_none_budget_returns_none(self):
        result = calculate_budget_targets(
            weekly_budget_amount=None,
            currency_code="PKR",
            country_id=None,
            region_id=None,
        )
        assert result.daily_budget is None
        assert len(result.warnings) > 0

    def test_currency_preserved(self):
        result = calculate_budget_targets(
            weekly_budget_amount=Decimal(1000),
            currency_code="INR",
            country_id=None,
            region_id=None,
        )
        assert result.currency_code == "INR"

    def test_monthly_is_about_4_33x_weekly(self):
        result = calculate_budget_targets(
            weekly_budget_amount=Decimal(700),
            currency_code="USD",
            country_id=None,
            region_id=None,
        )
        # 700 * 4.33 = 3031.00
        assert result.monthly_budget == Decimal("3031.00")


# ── Meal budget check ───────────────────────────────────────────────────────


class TestMealBudget:
    def test_meal_within_daily_budget(self):
        within, warnings = check_meal_budget(
            estimated_cost=Decimal(500),
            currency_code="PKR",
            daily_budget=Decimal(1000),
            weekly_budget=Decimal(7000),
        )
        assert within
        assert len(warnings) == 0

    def test_meal_exceeds_daily_budget(self):
        within, warnings = check_meal_budget(
            estimated_cost=Decimal(1500),
            currency_code="PKR",
            daily_budget=Decimal(1000),
            weekly_budget=Decimal(7000),
        )
        assert not within
        assert any("daily" in w.lower() for w in warnings)

    def test_meal_exceeds_weekly_budget(self):
        within, warnings = check_meal_budget(
            estimated_cost=Decimal(1200),
            currency_code="PKR",
            daily_budget=Decimal(1500),
            weekly_budget=Decimal(5000),
        )
        assert not within
        assert any("weekly" in w.lower() for w in warnings)

    def test_no_budget_set(self):
        within, warnings = check_meal_budget(
            estimated_cost=Decimal(500),
            currency_code="PKR",
            daily_budget=None,
            weekly_budget=None,
        )
        assert within  # Can't check, so default to True
        assert any("no budget" in w.lower() for w in warnings)


# ── Budget target response shape ────────────────────────────────────────────


class TestBudgetTargetShape:
    def test_budget_target_has_all_fields(self):
        result = calculate_budget_targets(
            weekly_budget_amount=Decimal(700),
            currency_code="PKR",
            country_id=None,
            region_id=None,
        )
        assert hasattr(result, "daily_budget")
        assert hasattr(result, "weekly_budget")
        assert hasattr(result, "monthly_budget")
        assert hasattr(result, "currency_code")
        assert hasattr(result, "country_id")
        assert hasattr(result, "region_id")
        assert hasattr(result, "warnings")
