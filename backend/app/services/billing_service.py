"""Lemon Squeezy billing service.

Handles checkout sessions, customer portal, webhook verification,
and subscription state synchronization.
"""

from __future__ import annotations

import hashlib
import hmac
from datetime import datetime
from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.models.user import User

logger = get_logger(__name__)

LS_API_BASE = "https://api.lemonsqueezy.com/v1"


def create_checkout_url(user: User) -> str:
    """Create a Lemon Squeezy checkout session and return the URL.

    Passes the user's ID in custom_data so we can identify them
    when the webhook fires.
    """
    api_key = settings.lemon_squeezy_api_key
    store_id = settings.lemon_squeezy_store_id
    variant_id = settings.lemon_squeezy_variant_id

    if not all([api_key, store_id, variant_id]):
        raise ValueError("Lemon Squeezy is not configured. Set LEMON_SQUEEZY_* env vars.")

    payload = {
        "data": {
            "type": "checkouts",
            "attributes": {
                "checkout_data": {
                    "email": user.email,
                    "custom": {
                        "user_id": str(user.id),
                    },
                },
                "product_options": {
                    "redirect_url": f"{settings.frontend_url}/dashboard?upgraded=true",
                },
            },
            "relationships": {
                "store": {
                    "data": {"type": "stores", "id": store_id},
                },
                "variant": {
                    "data": {"type": "variants", "id": variant_id},
                },
            },
        },
    }

    resp = httpx.post(
        f"{LS_API_BASE}/checkouts",
        json=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json",
        },
        timeout=15,
    )
    resp.raise_for_status()

    data = resp.json()
    checkout_url = data["data"]["attributes"]["url"]
    logger.info("Created checkout session for user %s", user.id)
    return checkout_url


def create_portal_url(user: User) -> str:
    """Retrieve the Lemon Squeezy customer portal URL for a user.

    Uses the ls_customer_id stored on the user record.
    """
    api_key = settings.lemon_squeezy_api_key
    customer_id = user.ls_customer_id

    if not api_key:
        raise ValueError("Lemon Squeezy is not configured.")
    if not customer_id:
        raise ValueError("No Lemon Squeezy customer ID for this user.")

    resp = httpx.get(
        f"{LS_API_BASE}/customers/{customer_id}",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/vnd.api+json",
        },
        timeout=15,
    )
    resp.raise_for_status()

    data = resp.json()
    portal_url = data["data"]["attributes"].get("urls", {}).get("customer_portal")
    if not portal_url:
        raise ValueError("No portal URL available for this customer.")

    logger.info("Retrieved portal URL for user %s", user.id)
    return portal_url


def verify_webhook_signature(
    raw_body: bytes,
    signature_header: str | None,
    secret: str | None = None,
) -> bool:
    """Verify Lemon Squeezy webhook signature using HMAC SHA256.

    Lemon Squeezy sends the signature in the X-Signature header as a
    hex-encoded HMAC-SHA256 digest of the raw request body.
    """
    if not signature_header:
        return False

    webhook_secret = secret or settings.lemon_squeezy_webhook_secret
    if not webhook_secret:
        logger.warning("No webhook secret configured; rejecting signature")
        return False

    expected = hmac.new(
        webhook_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, signature_header)


def handle_webhook_event(
    payload: dict[str, Any],
    user_lookup_fn,
    db_session_factory,
) -> None:
    """Process a validated Lemon Squeezy webhook event.

    Args:
        payload: The parsed JSON webhook body.
        user_lookup_fn: A callable (db, user_id) -> User | None to find a user.
        db_session_factory: A callable that returns a DB session.
    """
    event_name = payload.get("meta", {}).get("event_name", "")
    data = payload.get("data", {})
    attributes = data.get("attributes", {})
    custom_data = attributes.get("custom_data", {}) or {}

    user_id_str = custom_data.get("user_id")
    if not user_id_str:
        logger.warning("Webhook missing custom_data.user_id: event=%s", event_name)
        return

    db = db_session_factory()
    try:
        user = user_lookup_fn(db, user_id_str)
        if user is None:
            logger.warning("Webhook user not found: %s", user_id_str)
            return

        if event_name == "subscription_created":
            _handle_created(user, attributes)
        elif event_name in ("subscription_updated", "subscription_cancelled"):
            _handle_updated(user, attributes)
        elif event_name == "subscription_expired":
            _handle_expired(user)
        else:
            logger.info("Unhandled webhook event: %s", event_name)

        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to process webhook event=%s user=%s", event_name, user_id_str)
    finally:
        db.close()


def _handle_created(user: User, attributes: dict) -> None:
    """Handle subscription_created event."""
    user.ls_customer_id = (
        attributes.get("customer_id") or user.ls_customer_id
    )
    user.ls_subscription_id = (
        attributes.get("id") or user.ls_subscription_id
    )
    user.subscription_status = "active"
    user.subscription_tier = "pro"

    ends_at = attributes.get("renews_at") or attributes.get("ends_at")
    if ends_at:
        user.subscription_current_period_end = _parse_datetime(ends_at)

    logger.info(
        "Subscription created for user %s: tier=pro status=active",
        user.id,
    )


def _handle_updated(user: User, attributes: dict) -> None:
    """Handle subscription_updated / subscription_cancelled event."""
    status = attributes.get("status")
    if status:
        user.subscription_status = status

    # Map LS status to our tier
    if status in ("active", "paused"):
        user.subscription_tier = "pro"
    elif status in ("cancelled", "expired"):
        user.subscription_tier = "free"

    ends_at = attributes.get("renews_at") or attributes.get("ends_at")
    if ends_at:
        user.subscription_current_period_end = _parse_datetime(ends_at)

    logger.info(
        "Subscription updated for user %s: tier=%s status=%s",
        user.id,
        user.subscription_tier,
        user.subscription_status,
    )


def _handle_expired(user: User) -> None:
    """Handle subscription_expired event — downgrade to free."""
    user.subscription_status = "expired"
    user.subscription_tier = "free"
    user.subscription_current_period_end = None

    logger.info("Subscription expired for user %s; downgraded to free", user.id)


def _parse_datetime(value: str) -> datetime | None:
    """Parse an ISO datetime string, returning None on failure."""
    try:
        # Lemon Squeezy uses ISO 8601 format
        dt = datetime.fromisoformat(value)
        return dt
    except (ValueError, TypeError):
        return None
