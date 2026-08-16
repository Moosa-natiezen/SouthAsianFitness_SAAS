from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, ForeignKey, Numeric, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class ProgressEntry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "progress_entries"
    __table_args__ = (
        UniqueConstraint("user_id", "recorded_on", name="uq_progress_entries_user_recorded_on"),
        CheckConstraint("weight_kg > 0", name="positive_progress_weight"),
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    recorded_on: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    weight_kg: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    waist_cm: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    hip_cm: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    body_fat_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    notes: Mapped[str | None] = mapped_column(Text)

    user: Mapped[User] = relationship(back_populates="progress_entries")
