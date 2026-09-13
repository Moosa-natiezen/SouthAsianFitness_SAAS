"""WhatsApp food logging models.

FoodLogEntry stores meals logged through the WhatsApp chat interface —
a lightweight intake record (what was eaten + estimated macros) linked to
the user resolved from their WhatsApp phone number.

WhatsAppLink binds a verified WhatsApp phone number to a user account so
inbound webhooks can be resolved to a profile without session auth.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class WhatsAppLink(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Binds a WhatsApp phone number to a user account.

    The phone number is stored in normalized E.164 digits-only form
    (e.g. ``923001234567``) — Meta sends ``wa_id`` in exactly this format.
    """

    __tablename__ = "whatsapp_links"
    __table_args__ = (
        UniqueConstraint("phone_e164", name="uq_whatsapp_links_phone"),
        UniqueConstraint("user_id", name="uq_whatsapp_links_user"),
    )

    phone_e164: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)


class FoodLogEntry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A meal logged via WhatsApp chat (or future intake surfaces).

    Persists the LLM-extracted food description plus estimated macros so the
    daily total ("updated daily calorie count") can be computed and echoed
    back to the user.
    """

    __tablename__ = "food_log_entries"
    __table_args__ = (
        CheckConstraint(
            "calories >= 0 AND protein_g >= 0 AND carbs_g >= 0 AND fat_g >= 0",
            name="positive_food_log_macros",
        ),
        Index("ix_food_log_entries_user_date", "user_id", "logged_on"),
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    logged_on: Mapped[date] = mapped_column(Date, nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="whatsapp")

    # Raw message + LLM extraction
    raw_text: Mapped[str] = mapped_column(String(1000), nullable=False)
    food_items_json: Mapped[str] = mapped_column(String(2000), nullable=False, default="[]")

    # Estimated totals for the whole message
    calories: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False, default=0)
    protein_g: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False, default=0)
    carbs_g: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False, default=0)
    fat_g: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False, default=0)
