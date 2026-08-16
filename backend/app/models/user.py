from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
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
from app.models.associations import (
    user_preference_cuisine_tags,
    user_preference_dietary_tags,
    user_preference_regions,
    user_profile_dietary_tags,
)
from app.models.enums import (
    ActivityLevel,
    DietPattern,
    FitnessGoal,
    FoodPreferenceType,
    Sex,
    UnitSystem,
)
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.types import (
    ACTIVITY_LEVEL_ENUM,
    DIET_PATTERN_ENUM,
    FITNESS_GOAL_ENUM,
    FOOD_PREFERENCE_TYPE_ENUM,
    SEX_ENUM,
    UNIT_SYSTEM_ENUM,
)

if TYPE_CHECKING:
    from app.models.currency import Currency
    from app.models.food import Food
    from app.models.geography import Country, Region
    from app.models.meal_plan import MealPlan
    from app.models.progress import ProgressEntry
    from app.models.tags import CuisineTag, DietaryTag


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email"),)

    email: Mapped[str] = mapped_column(String(320), nullable=False)
    display_name: Mapped[str] = mapped_column(String(150), nullable=False)
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
    preferred_language: Mapped[str] = mapped_column(String(16), nullable=False, default="en")
    preferred_unit_system: Mapped[UnitSystem] = mapped_column(
        UNIT_SYSTEM_ENUM,
        nullable=False,
    )
    preferred_currency_code: Mapped[str] = mapped_column(
        ForeignKey("currencies.code", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)

    country: Mapped[Country] = relationship(back_populates="users")
    region: Mapped[Region | None] = relationship(back_populates="users")
    preferred_currency: Mapped[Currency] = relationship()
    profile: Mapped[UserProfile | None] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    preferences: Mapped[UserPreferences | None] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    food_preferences: Mapped[list[UserFoodPreference]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    meal_plans: Mapped[list[MealPlan]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    progress_entries: Mapped[list[ProgressEntry]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class UserProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_profiles"
    __table_args__ = (
        UniqueConstraint("user_id"),
        CheckConstraint("age_years > 0", name="positive_age"),
        CheckConstraint("height_cm > 0", name="positive_height"),
        CheckConstraint("weight_kg > 0", name="positive_weight"),
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    age_years: Mapped[int] = mapped_column(nullable=False)
    sex: Mapped[Sex] = mapped_column(SEX_ENUM, nullable=False)
    height_cm: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    weight_kg: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    activity_level: Mapped[ActivityLevel] = mapped_column(
        ACTIVITY_LEVEL_ENUM,
        nullable=False,
    )
    fitness_goal: Mapped[FitnessGoal] = mapped_column(
        FITNESS_GOAL_ENUM,
        nullable=False,
    )
    diet_pattern: Mapped[DietPattern] = mapped_column(
        DIET_PATTERN_ENUM,
        nullable=False,
        default=DietPattern.OMNIVORE,
    )

    user: Mapped[User] = relationship(back_populates="profile")
    dietary_tags: Mapped[list[DietaryTag]] = relationship(
        secondary=user_profile_dietary_tags,
        back_populates="user_profiles",
    )


class UserPreferences(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_preferences"
    __table_args__ = (
        UniqueConstraint("user_id"),
        CheckConstraint(
            "weekly_budget_amount IS NULL OR weekly_budget_amount >= 0",
            name="non_negative_weekly_budget",
        ),
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    weekly_budget_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    budget_currency_code: Mapped[str | None] = mapped_column(
        ForeignKey("currencies.code", ondelete="RESTRICT"),
    )
    notes: Mapped[str | None] = mapped_column(Text)

    user: Mapped[User] = relationship(back_populates="preferences")
    budget_currency: Mapped[Currency | None] = relationship()
    dietary_tags: Mapped[list[DietaryTag]] = relationship(
        secondary=user_preference_dietary_tags,
        back_populates="user_preferences",
    )
    cuisine_tags: Mapped[list[CuisineTag]] = relationship(
        secondary=user_preference_cuisine_tags,
        back_populates="user_preferences",
    )
    preferred_regions: Mapped[list[Region]] = relationship(
        secondary=user_preference_regions,
    )


class UserFoodPreference(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_food_preferences"
    __table_args__ = (UniqueConstraint("user_id", "food_id", name="uq_user_food_preferences_user_food"),)

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    food_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("foods.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    preference_type: Mapped[FoodPreferenceType] = mapped_column(
        FOOD_PREFERENCE_TYPE_ENUM,
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="food_preferences")
    food: Mapped[Food] = relationship(back_populates="user_food_preferences")
