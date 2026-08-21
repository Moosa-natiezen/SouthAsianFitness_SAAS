from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import FoodSourceLicense
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.types import FOOD_SOURCE_LICENSE_ENUM

if TYPE_CHECKING:
    from app.models.food import Food


class FoodSource(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Tracks the provenance of nutrition data for foods.

    Each food record can be linked to a FoodSource that records where
    its nutrition data originated, enabling traceability and compliance.
    """

    __tablename__ = "food_sources"
    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_food_sources_name_version"),
    )

    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    reference_url: Mapped[str | None] = mapped_column(Text)
    license_category: Mapped[FoodSourceLicense] = mapped_column(
        FOOD_SOURCE_LICENSE_ENUM, nullable=False, default=FoodSourceLicense.UNKNOWN
    )
    attribution_text: Mapped[str | None] = mapped_column(Text)
    can_store_raw_data: Mapped[bool] = mapped_column(nullable=False, default=False)
    can_store_derived_values: Mapped[bool] = mapped_column(nullable=False, default=True)
    description: Mapped[str | None] = mapped_column(Text)
    source_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    imported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    foods: Mapped[list[Food]] = relationship(back_populates="source")
