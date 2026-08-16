from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.associations import food_cuisine_tags, food_dietary_tags, food_regions
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.currency import Currency
    from app.models.geography import Country, Region
    from app.models.meal import MealFood
    from app.models.tags import CuisineTag, DietaryTag, FoodCategory
    from app.models.unit import Unit
    from app.models.user import UserFoodPreference


class Food(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "foods"
    __table_args__ = (
        UniqueConstraint("slug"),
        CheckConstraint("serving_size > 0", name="positive_serving_size"),
        CheckConstraint("calories >= 0", name="non_negative_calories"),
        Index("ix_foods_name", "name"),
    )

    slug: Mapped[str] = mapped_column(String(150), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    translations: Mapped[dict | None] = mapped_column(JSONB)
    category_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("food_categories.id", ondelete="SET NULL"),
        index=True,
    )
    serving_size: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    serving_unit_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("units.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    grams_per_serving: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
    calories: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    protein_g: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False, default=0)
    carbs_g: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False, default=0)
    fat_g: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False, default=0)
    fiber_g: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
    sugar_g: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
    sodium_mg: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)

    category: Mapped[FoodCategory | None] = relationship(back_populates="foods")
    serving_unit: Mapped[Unit] = relationship()
    regions: Mapped[list[Region]] = relationship(
        secondary=food_regions,
        back_populates="foods",
    )
    cuisine_tags: Mapped[list[CuisineTag]] = relationship(
        secondary=food_cuisine_tags,
        back_populates="foods",
    )
    dietary_tags: Mapped[list[DietaryTag]] = relationship(
        secondary=food_dietary_tags,
        back_populates="foods",
    )
    prices: Mapped[list[FoodPrice]] = relationship(
        back_populates="food",
        cascade="all, delete-orphan",
    )
    ingredients: Mapped[list[FoodIngredient]] = relationship(
        back_populates="parent_food",
        foreign_keys="FoodIngredient.parent_food_id",
        cascade="all, delete-orphan",
    )
    meal_foods: Mapped[list[MealFood]] = relationship(back_populates="food")
    user_food_preferences: Mapped[list[UserFoodPreference]] = relationship(
        back_populates="food",
    )


class FoodIngredient(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "food_ingredients"
    __table_args__ = (
        UniqueConstraint("parent_food_id", "ingredient_food_id", name="uq_food_ingredients_parent_ingredient"),
        CheckConstraint("quantity > 0", name="positive_ingredient_quantity"),
    )

    parent_food_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("foods.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ingredient_food_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("foods.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    unit_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("units.id", ondelete="RESTRICT"),
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(String(255))

    parent_food: Mapped[Food] = relationship(
        back_populates="ingredients",
        foreign_keys=[parent_food_id],
    )
    ingredient_food: Mapped[Food] = relationship(foreign_keys=[ingredient_food_id])
    unit: Mapped[Unit] = relationship()


class FoodPrice(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "food_prices"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="non_negative_price"),
        CheckConstraint("quantity > 0", name="positive_price_quantity"),
        Index(
            "ix_food_prices_lookup",
            "food_id",
            "country_id",
            "region_id",
            "observed_at",
        ),
    )

    food_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("foods.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    country_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("countries.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    region_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("regions.id", ondelete="SET NULL"),
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    currency_code: Mapped[str] = mapped_column(
        ForeignKey("currencies.code", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False, default=1)
    unit_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("units.id", ondelete="RESTRICT"),
        nullable=False,
    )
    source: Mapped[str | None] = mapped_column(String(255))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    food: Mapped[Food] = relationship(back_populates="prices")
    country: Mapped[Country] = relationship()
    region: Mapped[Region | None] = relationship()
    currency: Mapped[Currency] = relationship()
    unit: Mapped[Unit] = relationship()
