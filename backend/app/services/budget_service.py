"""Budget calculation service.

Converts user budget preferences into normalized daily/weekly/monthly budgets
and queries food pricing data for the user's location.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.food import FoodPrice


@dataclass
class BudgetTarget:
    """Normalized budget targets."""

    daily_budget: Decimal | None
    weekly_budget: Decimal | None
    monthly_budget: Decimal | None
    currency_code: str | None
    country_id: str | None
    region_id: str | None
    warnings: list[str]


@dataclass
class FoodPriceInfo:
    """Price information for a specific food."""

    food_id: str
    food_name: str
    food_slug: str
    price_amount: Decimal
    price_currency: str
    price_quantity: Decimal
    price_unit: str
    price_per_gram: Decimal | None
    country_id: str
    region_id: str | None


def normalize_budget_to_daily(
    amount: Decimal,
    period: str,
) -> tuple[Decimal, list[str]]:
    """Convert a budget amount and period to a daily amount.

    Supported periods: daily, weekly, monthly, yearly.
    """
    warnings = []
    period_lower = period.strip().lower()

    if period_lower == "daily":
        return amount, warnings
    elif period_lower == "weekly":
        return amount / Decimal(7), warnings
    elif period_lower == "monthly":
        return amount / Decimal(30), warnings
    elif period_lower == "yearly":
        return amount / Decimal(365), warnings
    else:
        warnings.append(f"Unknown budget period '{period}'. Assuming weekly.")
        return amount / Decimal(7), warnings


def calculate_budget_targets(
    weekly_budget_amount: Decimal | None,
    currency_code: str | None,
    country_id: UUID | None,
    region_id: UUID | None,
) -> BudgetTarget:
    """Calculate daily/weekly/monthly budget from user preferences."""
    warnings: list[str] = []

    if weekly_budget_amount is None or weekly_budget_amount <= 0:
        return BudgetTarget(
            daily_budget=None,
            weekly_budget=None,
            monthly_budget=None,
            currency_code=currency_code,
            country_id=str(country_id) if country_id else None,
            region_id=str(region_id) if region_id else None,
            warnings=["No budget set. Set a weekly food budget to see budget targets."],
        )

    daily = weekly_budget_amount / Decimal(7)
    monthly = weekly_budget_amount * Decimal("4.33")

    return BudgetTarget(
        daily_budget=daily.quantize(Decimal("0.01")),
        weekly_budget=weekly_budget_amount.quantize(Decimal("0.01")),
        monthly_budget=monthly.quantize(Decimal("0.01")),
        currency_code=currency_code,
        country_id=str(country_id) if country_id else None,
        region_id=str(region_id) if region_id else None,
        warnings=warnings,
    )


def get_food_prices_for_location(
    db: Session,
    country_id: UUID,
    region_id: UUID | None = None,
    limit: int = 50,
) -> list[FoodPriceInfo]:
    """Query food prices for a location, preferring region-level data.

    Falls back to country-level prices when region-specific data is unavailable.
    """
    # First try region-level prices
    if region_id is not None:
        region_prices = _query_prices(db, country_id=country_id, region_id=region_id, limit=limit)
        if region_prices:
            return region_prices

    # Fall back to country-level prices
    return _query_prices(db, country_id=country_id, region_id=None, limit=limit)


def _query_prices(
    db: Session,
    country_id: UUID,
    region_id: UUID | None,
    limit: int,
) -> list[FoodPriceInfo]:
    """Query food prices with optional region filter."""
    q = (
        select(FoodPrice)
        .where(FoodPrice.country_id == country_id)
        .order_by(desc(FoodPrice.observed_at))
        .limit(limit)
    )
    if region_id is not None:
        q = q.where(FoodPrice.region_id == region_id)
    else:
        q = q.where(FoodPrice.region_id.is_(None))

    prices = db.execute(q).scalars().all()
    results = []
    for p in prices:
        price_per_gram = None
        if p.unit and p.unit.to_base_factor and p.unit.to_base_factor > 0 and p.quantity > 0:
            total_grams = p.quantity * p.unit.to_base_factor
            if total_grams > 0:
                price_per_gram = p.amount / total_grams

        results.append(
            FoodPriceInfo(
                food_id=str(p.food_id),
                food_name=p.food.name if p.food else "",
                food_slug=p.food.slug if p.food else "",
                price_amount=p.amount,
                price_currency=p.currency_code,
                price_quantity=p.quantity,
                price_unit=p.unit.code if p.unit else "",
                price_per_gram=price_per_gram,
                country_id=str(p.country_id),
                region_id=str(p.region_id) if p.region_id else None,
            )
        )
    return results


def check_meal_budget(
    estimated_cost: Decimal,
    currency_code: str,
    daily_budget: Decimal | None,
    weekly_budget: Decimal | None,
) -> tuple[bool, list[str]]:
    """Check if a meal's estimated cost is within budget.

    Returns (is_within_budget, warnings).
    """
    warnings: list[str] = []

    if daily_budget is None and weekly_budget is None:
        warnings.append("No budget set. Cannot check if meal is within budget.")
        return True, warnings

    if daily_budget is not None and estimated_cost > daily_budget:
        warnings.append(
            f"Meal cost {estimated_cost} {currency_code} exceeds "
            f"daily budget {daily_budget} {currency_code}."
        )
        return False, warnings

    if weekly_budget is not None:
        weekly_cost = estimated_cost * 7
        if weekly_cost > weekly_budget:
            warnings.append(
                f"Estimated weekly cost {weekly_cost:.2f} {currency_code} "
                f"exceeds weekly budget {weekly_budget} {currency_code}."
            )
            return False, warnings

    return True, warnings
