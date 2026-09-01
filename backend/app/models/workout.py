from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class SavedWorkoutPlan(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A saved AI-generated workout plan."""

    __tablename__ = "saved_workout_plans"
    __table_args__ = (
        Index("ix_saved_workout_plans_user_created", "user_id", "created_at"),
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    goal: Mapped[str | None] = mapped_column(String(50))
    split: Mapped[str | None] = mapped_column(String(50))
    equipment: Mapped[str | None] = mapped_column(String(50))

    user: Mapped[User] = relationship(back_populates="saved_workout_plans")
