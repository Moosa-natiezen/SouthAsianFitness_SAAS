"""Vapi.ai webhook — voice-based AI nutritionist tool calls.

Vapi delivers server events to:

  POST /api/vapi/webhook  — tool-calls (and other server message types)

Flow for a ``log_meal`` tool call:
1. The caller's phone number is resolved to a user via
   ``users.whatsapp_phone`` — the same WhatsApp link users create in
   Settings, so one linked number works on both surfaces.
2. The spoken food text is passed to the shared extraction pipeline
   (OpenAI function calling) and persisted to ``food_log_entries``.
3. The response uses Vapi's exact tool-calls schema so the assistant can
   speak the confirmation back to the caller:

   ``{"results": [{"toolCallId": ..., "result": ...}]}`

Contract rules: Vapi treats non-2xx responses as server errors and retries,
and the voice call hangs waiting — so unknown message types are acknowledged
with an empty result list, per-tool failures are reported *inside* the
result string, and payloads are authenticated with the ``x-vapi-secret``
header when ``VAPI_SERVER_SECRET`` is configured.
"""

from __future__ import annotations

import hashlib
import hmac
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse
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
)

logger = get_logger(__name__)

router = APIRouter(prefix="/vapi", tags=["vapi"])

_UNLINKED_RESULT = (
    "This phone number isn't linked to a South Asian Fitness account yet. "
    "Sign up at southasianfitness.com and add this number in Settings to "
    "log meals by voice."
)

_HELP_RESULT = (
    "I couldn't find any food in that. Tell me what you ate, like "
    '"2 roti and a bowl of daal".'
)


# ── Authentication ───────────────────────────────────────────────────────────


def verify_vapi_secret(
    x_vapi_secret: Annotated[str | None, Header()] = None,
) -> bool:
    """Validate the ``x-vapi-secret`` header when VAPI_SERVER_SECRET is set.

    Vapi lets you configure a Server Secret that it sends as a header on
    every server-message webhook. When the secret is not configured (local
    dev), verification is skipped with a warning — always set it in
    production, otherwise anyone who finds the URL can log food to users.
    """
    secret = settings.vapi_server_secret
    if not secret:
        logger.warning(
            "VAPI_SERVER_SECRET not set — skipping Vapi webhook authentication"
        )
        return True
    if not x_vapi_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing x-vapi-secret header",
        )
    if not hmac.compare_digest(
        hmac.new(b"vapi", x_vapi_secret.encode(), hashlib.sha256).hexdigest(),
        hmac.new(b"vapi", secret.encode(), hashlib.sha256).hexdigest(),
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid x-vapi-secret header",
        )
    return True


# ── Webhook ──────────────────────────────────────────────────────────────────


@router.post("/webhook")
async def vapi_webhook(
    request: Request,
    _: Annotated[bool, Depends(verify_vapi_secret)],
    db: Annotated[Session, Depends(get_db)],
) -> JSONResponse:
    """Receive Vapi server messages and answer ``tool-calls`` requests.

    The response body follows Vapi's tool-calls schema exactly::

        {"results": [{"toolCallId": "<id from request>", "result": "<string>"}]}
    """
    try:
        payload: dict[str, Any] = await request.json()
    except (ValueError, TypeError):
        logger.warning("Vapi webhook received non-JSON body")
        return JSONResponse({"results": []})

    message = payload.get("message") or {}

    if message.get("type") != "tool-calls":
        # Vapi also sends other server message types (status-update,
        # transcript, end-of-call-report…). They need no answer — an empty
        # result list is the correct "nothing to say" acknowledgment.
        logger.info("Vapi webhook ignoring message type=%s", message.get("type"))
        return JSONResponse({"results": []})

    tool_calls = message.get("toolCallList") or []
    results: list[dict[str, str]] = []
    for call in tool_calls:
        tool_call_id = call.get("id") or ""
        name = call.get("name") or ""
        arguments = call.get("arguments") or {}
        if isinstance(arguments, str):
            # Vapi may deliver arguments as a JSON string.
            try:
                import json

                arguments = json.loads(arguments)
            except ValueError:
                arguments = {}
        if name == "log_meal":
            result_text = await _handle_log_meal(db, arguments)
        else:
            result_text = f'Unknown tool "{name}". Only "log_meal" is supported.'

        results.append({"toolCallId": tool_call_id, "result": result_text})

    return JSONResponse({"results": results})


# ── Tool handlers ────────────────────────────────────────────────────────────


async def _handle_log_meal(db: Session, arguments: dict[str, Any]) -> str:
    """Log a meal for the caller and return a speakable confirmation.

    Never raises: any failure becomes a descriptive result string so Vapi
    speaks the problem instead of hanging up on a 500.
    """
    phone = normalize_phone(str(arguments.get("phone_number") or ""))
    food_text = str(arguments.get("food_text") or "").strip()

    if not phone:
        return (
            "I couldn't get your phone number from the call. Please link "
            "your number in Settings first."
        )
    if not food_text:
        return _HELP_RESULT

    user = resolve_user_by_phone(db, phone)
    if user is None:
        logger.info("Vapi log_meal from unlinked number (wa_id=%s)", phone)
        return _UNLINKED_RESULT

    extraction = await extract_foods_from_text(food_text)
    if extraction.get("items"):
        persist_food_log(db, user_id=user.id, raw_text=food_text, extraction=extraction)
    daily = get_daily_totals(db, user_id=user.id)

    profile = user.profile
    calorie_target = (
        float(profile.target_calories)
        if profile is not None and profile.target_calories
        else None
    )

    return build_confirmation_message(
        extraction, daily, calorie_target=calorie_target
    )
