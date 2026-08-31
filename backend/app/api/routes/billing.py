"""Billing API routes — Lemon Squeezy integration."""

from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_csrf
from app.core.logging import get_logger
from app.models.user import User
from app.services.billing_service import (
    create_checkout_url,
    create_portal_url,
    handle_webhook_event,
    verify_webhook_signature,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])


@router.post("/checkout")
def checkout(
    user: Annotated[User, Depends(require_csrf)],
) -> dict:
    """Create a Lemon Squeezy checkout session for the Pro plan.

    Returns the checkout URL the user should be redirected to.
    """
    try:
        url = create_checkout_url(user)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except Exception:
        logger.exception("Failed to create checkout for user %s", user.id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to create checkout session.",
        )
    return {"checkout_url": url}


@router.post("/portal")
def portal(
    user: Annotated[User, Depends(require_csrf)],
) -> dict:
    """Retrieve the Lemon Squeezy customer portal URL.

    Returns the portal URL where the user can manage their subscription.
    If no customer ID exists yet, returns null gracefully.
    """
    if not user.ls_customer_id:
        return {"portal_url": None}
    try:
        url = create_portal_url(user)
    except ValueError as exc:
        logger.warning(
            "Portal URL unavailable for user %s: %s", user.id, exc,
        )
        return {"portal_url": None}
    except Exception:
        logger.exception("Failed to get portal URL for user %s", user.id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to retrieve portal URL.",
        )
    return {"portal_url": url}


@router.post("/webhook")
async def webhook(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Receive Lemon Squeezy webhook events.

    This endpoint has NO auth and NO CSRF — Lemon Squeezy calls it directly.
    Signature verification is the only security gate.
    """
    raw_body = await request.body()
    signature = request.headers.get("X-Signature")

    if not verify_webhook_signature(raw_body, signature):
        logger.warning("Invalid webhook signature from %s", request.client.host if request.client else "unknown")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    try:
        payload = await request.json()
    except (json.JSONDecodeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    def user_lookup(
        session: Session,
        user_id: str | None = None,
        email: str | None = None,
    ) -> User | None:
        from uuid import UUID

        # Priority 1: look up by primary key
        if user_id:
            try:
                uid = UUID(user_id)
            except ValueError:
                pass
            else:
                user = session.query(User).filter(User.id == uid).first()
                if user is not None:
                    return user

        # Fallback: case-insensitive email lookup
        if email:
            return session.query(User).filter(
                func.lower(User.email) == email.lower()
            ).first()

        return None

    def session_factory():
        return db

    handle_webhook_event(payload, user_lookup, session_factory)

    return {"status": "ok"}
