from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    JSON,
    CheckConstraint,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import MealType
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.types import MEAL_TYPE_ENUM

if TYPE_CHECKING:
    from app.models.food import Food
    from app.models.meal_plan import MealPlanDayMeal
    from app.models.unit import Unit


class Meal(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "meals"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    translations: Mapped[dict | None] = mapped_column(JSON)
    meal_type: Mapped[MealType] = mapped_column(
        MEAL_TYPE_ENUM,
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)

    meal_foods: Mapped[list[MealFood]] = relationship(
        back_populates="meal",
        order_by="MealFood.sort_order",
        cascade="all, delete-orphan",
    )
    plan_day_meals: Mapped[list[MealPlanDayMeal]] = relationship(back_populates="meal")


class MealFood(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "meal_foods"
    __table_args__ = (
        UniqueConstraint("meal_id", "food_id", "sort_order", name="uq_meal_foods_meal_food_order"),
        CheckConstraint("servings > 0", name="positive_meal_servings"),
    )

    meal_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("meals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    food_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("foods.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    servings: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False, default=1)
    serving_unit_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("units.id", ondelete="RESTRICT"),
    )
    sort_order: Mapped[int] = mapped_column(nullable=False, default=0)

    meal: Mapped[Meal] = relationship(back_populates="meal_foods")
    food: Mapped[Food] = relationship(back_populates="meal_foods")
    serving_unit: Mapped[Unit | None] = relationship()
