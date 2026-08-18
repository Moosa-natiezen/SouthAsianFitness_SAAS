from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import FitnessGoal, MealPlanStatus, MealType
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.types import FITNESS_GOAL_ENUM, MEAL_PLAN_STATUS_ENUM, MEAL_TYPE_ENUM

if TYPE_CHECKING:
    from app.models.currency import Currency
    from app.models.meal import Meal
    from app.models.user import User


class MealPlan(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "meal_plans"
    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="valid_plan_dates"),
        CheckConstraint("daily_calorie_target > 0", name="positive_calorie_target"),
        CheckConstraint(
            "daily_budget_amount IS NULL OR daily_budget_amount >= 0",
            name="non_negative_daily_budget",
        ),
        Index("ix_meal_plans_user_status", "user_id", "status"),
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str | None] = mapped_column(String(255))
    goal: Mapped[FitnessGoal] = mapped_column(
        FITNESS_GOAL_ENUM,
        nullable=False,
    )
    daily_calorie_target: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    daily_protein_g: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
    daily_carbs_g: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
    daily_fat_g: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
    daily_budget_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    budget_currency_code: Mapped[str | None] = mapped_column(
        ForeignKey("currencies.code", ondelete="RESTRICT"),
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[MealPlanStatus] = mapped_column(
        MEAL_PLAN_STATUS_ENUM,
        nullable=False,
        default=MealPlanStatus.DRAFT,
        index=True,
    )

    user: Mapped[User] = relationship(back_populates="meal_plans")
    budget_currency: Mapped[Currency | None] = relationship()
    days: Mapped[list[MealPlanDay]] = relationship(
        back_populates="meal_plan",
        order_by="MealPlanDay.plan_date",
        cascade="all, delete-orphan",
    )


class MealPlanDay(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "meal_plan_days"
    __table_args__ = (
        UniqueConstraint("meal_plan_id", "plan_date", name="uq_meal_plan_days_plan_date"),
    )

    meal_plan_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("meal_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(String(500))

    meal_plan: Mapped[MealPlan] = relationship(back_populates="days")
    day_meals: Mapped[list[MealPlanDayMeal]] = relationship(
        back_populates="meal_plan_day",
        order_by="MealPlanDayMeal.sort_order",
        cascade="all, delete-orphan",
    )


class MealPlanDayMeal(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "meal_plan_day_meals"
    __table_args__ = (
        UniqueConstraint(
            "meal_plan_day_id",
            "meal_id",
            "sort_order",
            name="uq_meal_plan_day_meals_day_meal_order",
        ),
    )

    meal_plan_day_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("meal_plan_days.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    meal_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("meals.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    meal_type: Mapped[MealType | None] = mapped_column(MEAL_TYPE_ENUM, nullable=True)
    sort_order: Mapped[int] = mapped_column(nullable=False, default=0)

    meal_plan_day: Mapped[MealPlanDay] = relationship(back_populates="day_meals")
    meal: Mapped[Meal] = relationship(back_populates="plan_day_meals")
