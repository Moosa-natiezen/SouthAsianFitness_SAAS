from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import UnitSystem
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.types import UNIT_SYSTEM_ENUM

if TYPE_CHECKING:
    from app.models.currency import Currency
    from app.models.food import Food
    from app.models.user import User


class Country(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "countries"
    __table_args__ = (UniqueConstraint("iso_code"),)

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    iso_code: Mapped[str] = mapped_column(String(2), nullable=False)
    currency_code: Mapped[str] = mapped_column(
        ForeignKey("currencies.code", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    default_unit_system: Mapped[UnitSystem] = mapped_column(
        UNIT_SYSTEM_ENUM,
        nullable=False,
    )

    currency: Mapped[Currency] = relationship(back_populates="countries")
    regions: Mapped[list[Region]] = relationship(
        back_populates="country",
        cascade="all, delete-orphan",
    )
    users: Mapped[list[User]] = relationship(back_populates="country")


class Region(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "regions"
    __table_args__ = (
        UniqueConstraint("country_id", "code", name="uq_regions_country_id_code"),
        UniqueConstraint("country_id", "name", name="uq_regions_country_id_name"),
    )

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    code: Mapped[str | None] = mapped_column(String(32))
    country_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("countries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    country: Mapped[Country] = relationship(back_populates="regions")
    users: Mapped[list[User]] = relationship(back_populates="region")
    foods: Mapped[list[Food]] = relationship(
        secondary="food_regions",
        back_populates="regions",
    )
