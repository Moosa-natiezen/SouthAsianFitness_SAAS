"""Authenticated routes for linking a WhatsApp number to the current account.

The webhook resolves inbound messages to users via ``users.whatsapp_phone``;
this router lets the user set (or clear) that field themselves.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.api.deps import require_auth, require_csrf
from app.db.session import get_db
from app.models.user import User
from app.models.whatsapp import WhatsAppLink
from app.services.whatsapp_service import normalize_phone

router = APIRouter(prefix="/users", tags=["users"])


class WhatsAppLinkRequest(BaseModel):
    """Payload for PATCH /users/me/whatsapp."""

    # Accepts anything a human would paste: +92 300 1234567, 92300-1234567…
    # Empty/None clears the link (unlink).
    whatsapp_phone: str | None = Field(default=None, max_length=30)

    @field_validator("whatsapp_phone")
    @classmethod
    def _strip(cls, v: str | None) -> str | None:
        return v.strip() if v else v


def _digits_only(normalized: str) -> bool:
    return bool(normalized) and normalized.isdigit()


@router.patch("/me/whatsapp")
def update_whatsapp_phone(
    payload: WhatsAppLinkRequest,
    user: Annotated[User, Depends(require_csrf)],
    db: Annotated[Session, Depends(get_db)],
):
    """Link (or clear) the WhatsApp phone number on the current account.

    - The number is normalized to Meta's ``wa_id`` format (E.164 digits,
      no leading ``+``/zeros).
    - Links are exclusive: a phone already bound to a different account is
      rejected with 409; re-linking this account's existing number is a no-op.
    - ``{"whatsapp_phone": null}`` (or empty) unlinks the number.
    """
    raw = payload.whatsapp_phone

    if raw is None or raw == "":
        # Unlink: clear the fast-lookup column and deactivate the link row.
        user.whatsapp_phone = None
        link = (
            db.query(WhatsAppLink).filter(WhatsAppLink.user_id == user.id).first()
        )
        if link:
            link.is_active = False
        db.commit()
        return {"status": "ok", "linked": False, "whatsapp_phone": None}

    normalized = normalize_phone(raw)

    if not _digits_only(normalized):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "INVALID_PHONE",
                "message": "Phone number must contain only digits after removing "
                "'+', spaces, and dashes (E.164 format, e.g. 923001234567).",
            },
        )

    # E.164 sanity: country code + subscriber number, 8–15 digits total.
    if not (8 <= len(normalized) <= 15):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "INVALID_PHONE",
                "message": "Phone number must be 8–15 digits including country "
                "code (e.g. 923001234567 for +92 300 1234567).",
            },
        )

    # Exclusive linking: the number must not already belong to another user.
    clash = (
        db.query(WhatsAppLink)
        .filter(
            WhatsAppLink.phone_e164 == normalized,
            WhatsAppLink.user_id != user.id,
            WhatsAppLink.is_active.is_(True),
        )
        .first()
    )
    if clash:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "PHONE_ALREADY_LINKED",
                "message": "This WhatsApp number is already connected to another "
                "account. Unlink it there first, or contact support.",
            },
        )

    user.whatsapp_phone = normalized
    link = db.query(WhatsAppLink).filter(WhatsAppLink.user_id == user.id).first()
    if link:
        link.phone_e164 = normalized
        link.is_active = True
        link.verified_at = None  # re-verify on next inbound message
    else:
        db.add(WhatsAppLink(phone_e164=normalized, user_id=user.id))
    db.commit()

    return {"status": "ok", "linked": True, "whatsapp_phone": normalized}


@router.get("/me/whatsapp")
def get_whatsapp_phone(
    user: Annotated[User, Depends(require_auth)],
):
    """Return the current WhatsApp link status for the account."""
    return {
        "linked": bool(user.whatsapp_phone),
        "whatsapp_phone": user.whatsapp_phone,
    }
