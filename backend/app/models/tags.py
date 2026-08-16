from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import DietaryTagKind
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.types import DIETARY_TAG_KIND_ENUM

if TYPE_CHECKING:
    from app.models.food import Food
    from app.models.user import UserPreferences, UserProfile


class FoodCategory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "food_categories"
    __table_args__ = (UniqueConstraint("slug"),)

    slug: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    foods: Mapped[list[Food]] = relationship(back_populates="category")


class CuisineTag(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "cuisine_tags"
    __table_args__ = (UniqueConstraint("slug"),)

    slug: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    foods: Mapped[list[Food]] = relationship(
        secondary="food_cuisine_tags",
        back_populates="cuisine_tags",
    )
    user_preferences: Mapped[list[UserPreferences]] = relationship(
        secondary="user_preference_cuisine_tags",
        back_populates="cuisine_tags",
    )


class DietaryTag(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "dietary_tags"
    __table_args__ = (UniqueConstraint("slug"),)

    slug: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    kind: Mapped[DietaryTagKind] = mapped_column(
        DIETARY_TAG_KIND_ENUM,
        nullable=False,
        index=True,
    )

    foods: Mapped[list[Food]] = relationship(
        secondary="food_dietary_tags",
        back_populates="dietary_tags",
    )
    user_profiles: Mapped[list[UserProfile]] = relationship(
        secondary="user_profile_dietary_tags",
        back_populates="dietary_tags",
    )
    user_preferences: Mapped[list[UserPreferences]] = relationship(
        secondary="user_preference_dietary_tags",
        back_populates="dietary_tags",
    )
