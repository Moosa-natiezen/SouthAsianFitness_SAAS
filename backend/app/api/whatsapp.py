"""WhatsApp Cloud API webhook — chat-based meal logging.

Meta delivers inbound WhatsApp events here:

  GET  /api/whatsapp/webhook  — one-time subscription verification handshake
  POST /api/whatsapp/webhook  — inbound message / status notifications

Flow for an inbound text message:
1. The sender's ``wa_id`` (E.164 digits) is resolved to a user via
   ``users.whatsapp_phone``.
2. The message body is passed to OpenAI (function calling) to extract food
   items with estimated macros.
3. Items are persisted to ``food_log_entries`` and the user's daily total is
   recomputed.
4. A formatted confirmation reply is sent back through the Cloud API.

Webhook contract rules: Meta expects a fast 2xx for every delivery and
retries with backoff otherwise — so processing errors are logged and
swallowed (never a 500), duplicate deliveries (Meta retries) are de-duped
by message id, and payloads are authenticated with the ``X-Hub-Signature-256``
HMAC when ``WHATSAPP_APP_SECRET`` is configured.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from collections import OrderedDict
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.core.logging import get_logger
from app.services.whatsapp_service import (
    build_confirmation_message,
    extract_foods_from_text,
    get_daily_totals,
    normalize_phone,
    persist_food_log,
    resolve_user_by_phone,
    send_whatsapp_reply,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

# In-memory de-dup of recently seen inbound message ids. Meta redelivers
# webhooks until they receive a 2xx, so the same message can arrive twice;
# without this the user's food log would double-count. Process-local, which
# is fine — a missed dedup just logs one extra entry.
_recent_message_ids: OrderedDict[str, None] = OrderedDict()
_RECENT_MESSAGE_ID_CAP = 500

_HELP_REPLY = (
    "👋 Send me what you ate — e.g. *\"2 roti and a bowl of daal\"* — and "
    "I'll log the calories and macros for you."
)
_UNLINKED_REPLY = (
    "This number isn't linked to a South Asian Fitness account yet. "
    "Sign up at southasianfitness.com and add this number to your profile "
    "to start logging meals by chat."
)


# ── Signature verification ───────────────────────────────────────────────────


def verify_meta_signature(raw_body: bytes, signature_header: str | None) -> bool:
    """Validate the X-Hub-Signature-256 HMAC when WHATSAPP_APP_SECRET is set.

    Meta signs every webhook payload with HMAC-SHA256 using the app secret.
    When the secret is not configured (local dev), verification is skipped
    with a warning — always configure it in production.
    """
    secret = settings.whatsapp_app_secret
    if not secret:
        logger.warning(
            "WHATSAPP_APP_SECRET not set — skipping WhatsApp webhook "
            "signature verification"
        )
        return True
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(
        secret.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header.removeprefix("sha256="))


# ── Meta subscription handshake ──────────────────────────────────────────────


@router.get("/webhook", response_class=PlainTextResponse)
def verify_webhook(
    mode: Annotated[str | None, Query(alias="hub.mode")] = None,
    token: Annotated[str | None, Query(alias="hub.verify_token")] = None,
    challenge: Annotated[str | None, Query(alias="hub.challenge")] = None,
) -> str:
    """One-time webhook subscription handshake from the Meta App Dashboard."""
    if (
        mode == "subscribe"
        and token
        and settings.whatsapp_verify_token
        and hmac.compare_digest(token, settings.whatsapp_verify_token)
    ):
        logger.info("WhatsApp webhook subscription verified by Meta")
        return challenge or ""
    logger.warning("WhatsApp webhook verification rejected (mode=%s)", mode)
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Verification failed",
    )


# ── Inbound notifications ────────────────────────────────────────────────────


@router.post("/webhook")
async def receive_webhook(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    """Receive WhatsApp message notifications.

    Always answers ``{"status": "ok"}`` for accepted payloads — a non-2xx
    here makes Meta retry, and the HTTP status is a terrible place to
    signal per-message logging failures anyway.
    """
    raw_body = await request.body()
    if not verify_meta_signature(raw_body, request.headers.get("X-Hub-Signature-256")):
        logger.warning("WhatsApp webhook signature mismatch — rejecting payload")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    try:
        payload: dict[str, Any] = await request.json()
    except (json.JSONDecodeError, ValueError):
        # Signature already validated, so this is a misbehaving-but-trusted
        # sender — acknowledge rather than trigger Meta retry storms.
        return {"status": "ignored", "reason": "invalid_json"}

    if payload.get("object") != "whatsapp_business_account":
        return {"status": "ignored", "reason": "unknown_object"}

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            # Delivery/status receipts have no "messages" key — skipped.
            for message in value.get("messages", []):
                try:
                    await _process_message(db, message)
                except Exception:
                    logger.exception(
                        "WhatsApp message processing failed (id=%s)",
                        message.get("id"),
                    )
    return {"status": "ok"}


async def _process_message(db: Session, message: dict[str, Any]) -> None:
    """Handle one inbound message end-to-end: link → extract → log → reply."""
    message_id = message.get("id")
    if not message_id:
        return
    if message_id in _recent_message_ids:
        logger.info("Skipping duplicate WhatsApp message %s", message_id)
        return
    _recent_message_ids[message_id] = None
    while len(_recent_message_ids) > _RECENT_MESSAGE_ID_CAP:
        _recent_message_ids.popitem(last=False)

    text = (message.get("text") or {}).get("body") or ""
    if message.get("type") != "text" or not text.strip():
        _reply_to(message, _HELP_REPLY)
        return

    phone = normalize_phone(message.get("from", ""))
    user = resolve_user_by_phone(db, phone) if phone else None
    if user is None:
        logger.info(
            "WhatsApp message from unlinked number (wa_id=%s)", message.get("from")
        )
        _reply_to(message, _UNLINKED_REPLY)
        return

    extraction = await extract_foods_from_text(text)
    if extraction.get("items"):
        # Zero-food messages ("haha lol") are answered with help text and
        # never logged — a 0-kcal row would only pollute the daily totals.
        persist_food_log(db, user_id=user.id, raw_text=text, extraction=extraction)
    daily = get_daily_totals(db, user_id=user.id)

    profile = user.profile
    calorie_target = (
        float(profile.target_calories)
        if profile is not None and profile.target_calories
        else None
    )

    reply = build_confirmation_message(
        extraction, daily, calorie_target=calorie_target
    )
    _reply_to(message, reply)


def _reply_to(message: dict[str, Any], body: str) -> None:
    """Best-effort outbound reply; delivery failures are logged, never raised."""
    to = message.get("from", "")
    if not to:
        return
    if not send_whatsapp_reply(to, body):
        logger.warning("WhatsApp reply not delivered (to=%s)", to)
