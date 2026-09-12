"""Outbound notification helpers for non-critical side effects.

All functions in this module are strictly fire-and-forget: they are
dispatched via FastAPI's ``BackgroundTasks`` (which run *after* the HTTP
response has been sent) and swallow every error, so a notification
failure can never delay or fail an API response.

Currently used for founder alerts through n8n.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def notify_new_signup(
    user_id: str,
    email: str,
    display_name: str,
    method: str = "password",
) -> None:
    """Send a "new user signed up" founder alert to n8n.

    Intended to run as a FastAPI background task: the response has already
    been sent by the time this executes, so blocking network I/O here
    costs the user nothing.

    Pass plain values (never ORM objects) — the request's DB session is
    closed before background tasks run.

    Args:
        user_id: ID of the newly registered user.
        email: The user's (normalized) email address.
        display_name: The user's chosen display name.
        method: Signup method, ``"password"`` or ``"google"``.
    """
    webhook_url = settings.n8n_webhook_url
    if not webhook_url:
        return

    body: dict[str, Any] = {
        "source": "signup",
        "event": "user_signup",
        "user_id": user_id,
        "email": email,
        "display_name": display_name,
        "method": method,
        "occurred_at": datetime.now(UTC).isoformat(),
    }

    try:
        with httpx.Client(timeout=3.0) as client:
            resp = client.post(webhook_url, json=body)
            resp.raise_for_status()
        logger.info(
            "Signup alert sent to n8n for user %s (status=%s)",
            user_id, resp.status_code,
        )
    except Exception:
        logger.warning(
            "Failed to send signup alert to n8n for user %s", user_id,
            exc_info=True,
        )
