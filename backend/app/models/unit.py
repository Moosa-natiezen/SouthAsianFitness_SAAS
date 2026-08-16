from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import UnitDimension
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.types import UNIT_DIMENSION_ENUM


class Unit(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "units"
    __table_args__ = (UniqueConstraint("code"),)

    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    dimension: Mapped[UnitDimension] = mapped_column(UNIT_DIMENSION_ENUM, nullable=False)
    to_base_factor: Mapped[Decimal | None] = mapped_column(Numeric(18, 8))
