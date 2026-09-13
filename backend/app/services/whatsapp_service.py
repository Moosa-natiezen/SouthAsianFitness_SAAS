"""WhatsApp chat-based meal logging service.

Inbound flow:
1. Meta sends a webhook POST with a message from a known phone number.
2. The phone (``wa_id``, E.164 digits) is resolved to a user via
   ``users.whatsapp_phone``.
3. The message text is passed to OpenAI (function calling) to extract
   structured food items with estimated macros.
4. Entries are persisted to ``food_log_entries`` and the user's daily total
   is computed.
5. A formatted confirmation reply is sent back through the Cloud API.

All Meta API calls are best-effort: outbound reply failures are logged, not
raised, so webhook processing never breaks because of a delivery hiccup.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

import httpx
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.ai_metrics import ai_metrics
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


# ── Phone normalization ──────────────────────────────────────────────────────


def normalize_phone(raw: str) -> str:
    """Normalize a phone string to E.164 digits-only (Meta wa_id format).

    Strips whitespace, dashes, parentheses, leading + and any leading zeros
    from international notation (Meta's wa_id never has a leading +).
    """
    digits = "".join(c for c in raw if c.isdigit())
    return digits.lstrip("0") or digits


# ── User resolution ──────────────────────────────────────────────────────────


def resolve_user_by_phone(db: Session, phone_e164: str) -> Any | None:
    """Return the active user linked to this WhatsApp phone, else None."""
    from app.models.user import User

    normalized = normalize_phone(phone_e164)
    return (
        db.query(User)
        .filter(User.whatsapp_phone == normalized, User.is_active.is_(True))
        .first()
    )


# ── LLM food extraction ──────────────────────────────────────────────────────

_EXTRACTION_TOOL = {
    "type": "function",
    "function": {
        "name": "log_foods",
        "description": (
            "Record the South Asian / Desi foods the user says they ate, with "
            "estimated macros per item and realistic portions."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "description": "Each distinct food or dish mentioned.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Dish name, e.g. 'Chicken Biryani', '2 Roti'",
                            },
                            "portion": {
                                "type": "string",
                                "description": "Portion as stated or estimated, e.g. '1 plate', '2 pieces'",
                            },
                            "calories": {"type": "number"},
                            "protein_g": {"type": "number"},
                            "carbs_g": {"type": "number"},
                            "fat_g": {"type": "number"},
                        },
                        "required": ["name", "calories", "protein_g", "carbs_g", "fat_g"],
                    },
                }
            },
            "required": ["items"],
        },
    },
}

_EXTRACTION_SYSTEM_PROMPT = """You are a South Asian nutritionist's intake assistant.
Extract every food/drink item the user says they ate from their message.
Estimate realistic macros for AUTHENTIC South Asian / Desi dishes (Roti, Daal,
Biryani, Karahi, Paratha, Sabzi, Chana, Paneer, etc.) using standard home
portions. Sum estimates honestly — never round down to look healthier.
Call the log_foods function with the items. If the message contains no food,
return an empty items list."""


async def extract_foods_from_text(text: str) -> dict[str, Any]:
    """Extract structured food items + macro totals from a chat message.

    Returns ``{"items": [...], "totals": {calories, protein_g, carbs_g, fat_g}}``.
    Raises nothing: on any LLM failure returns empty extraction so the
    webhook can still reply with a graceful message.
    """
    api_key = settings.openai_api_key
    if not api_key or not text.strip():
        return {"items": [], "totals": _zero_totals()}

    from langfuse.openai import AsyncOpenAI

    try:
        client = AsyncOpenAI(api_key=api_key)
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": _EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": text[:1000]},
            ],
            tools=[_EXTRACTION_TOOL],
            tool_choice={"type": "function", "function": {"name": "log_foods"}},
            temperature=0.1,
            max_tokens=600,
        )
        ai_metrics.record_llm_call()

        tool_calls = response.choices[0].message.tool_calls or []
        if not tool_calls:
            return {"items": [], "totals": _zero_totals()}

        arguments = json.loads(tool_calls[0].function.arguments or "{}")
        items: list[dict[str, Any]] = []
        for raw_item in arguments.get("items", []):
            try:
                items.append(
                    {
                        "name": str(raw_item.get("name", "food"))[:120],
                        "portion": str(raw_item.get("portion", ""))[:80],
                        "calories": max(0.0, float(raw_item.get("calories", 0))),
                        "protein_g": max(0.0, float(raw_item.get("protein_g", 0))),
                        "carbs_g": max(0.0, float(raw_item.get("carbs_g", 0))),
                        "fat_g": max(0.0, float(raw_item.get("fat_g", 0))),
                    }
                )
            except (TypeError, ValueError):
                continue

        totals = {
            "calories": round(sum(i["calories"] for i in items), 1),
            "protein_g": round(sum(i["protein_g"] for i in items), 1),
            "carbs_g": round(sum(i["carbs_g"] for i in items), 1),
            "fat_g": round(sum(i["fat_g"] for i in items), 1),
        }
        return {"items": items, "totals": totals}

    except Exception:
        logger.exception("WhatsApp food extraction failed — returning empty result")
        return {"items": [], "totals": _zero_totals()}


def _zero_totals() -> dict[str, float]:
    return {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0}


# ── Persistence + daily total ────────────────────────────────────────────────


def persist_food_log(
    db: Session,
    *,
    user_id: Any,
    raw_text: str,
    extraction: dict[str, Any],
    logged_on: date | None = None,
    source: str = "whatsapp",
) -> Any:
    """Persist one chat message's foods as a FoodLogEntry row."""
    from app.models.whatsapp import FoodLogEntry

    entry = FoodLogEntry(
        user_id=user_id,
        logged_on=logged_on or datetime.now(tz=UTC).date(),
        source=source,
        raw_text=raw_text[:1000],
        food_items_json=json.dumps(extraction.get("items", []))[:2000],
        calories=Decimal(str(extraction["totals"]["calories"])),
        protein_g=Decimal(str(extraction["totals"]["protein_g"])),
        carbs_g=Decimal(str(extraction["totals"]["carbs_g"])),
        fat_g=Decimal(str(extraction["totals"]["fat_g"])),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_daily_totals(db: Session, user_id: Any, day: date | None = None) -> dict[str, float]:
    """Sum today's logged macros for the user."""
    from app.models.whatsapp import FoodLogEntry

    day = day or datetime.now(tz=UTC).date()
    row = (
        db.query(
            func.coalesce(func.sum(FoodLogEntry.calories), 0.0),
            func.coalesce(func.sum(FoodLogEntry.protein_g), 0.0),
            func.coalesce(func.sum(FoodLogEntry.carbs_g), 0.0),
            func.coalesce(func.sum(FoodLogEntry.fat_g), 0.0),
        )
        .filter(FoodLogEntry.user_id == user_id, FoodLogEntry.logged_on == day)
        .one()
    )
    return {
        "calories": float(row[0]),
        "protein_g": float(row[1]),
        "carbs_g": float(row[2]),
        "fat_g": float(row[3]),
    }


# ── Confirmation reply ───────────────────────────────────────────────────────


def build_confirmation_message(
    extraction: dict[str, Any],
    daily: dict[str, float],
    *,
    calorie_target: float | None = None,
) -> str:
    """Format the WhatsApp reply: what was logged + updated daily count."""
    items = extraction.get("items", [])
    if not items:
        return (
            "🤔 I couldn't find any food in that message. Try something like:\n"
            "*\"2 roti and a bowl of daal\"*"
        )

    lines = ["✅ *Logged!*", ""]
    for item in items:
        portion = f" ({item['portion']})" if item.get("portion") else ""
        lines.append(
            f"• {item['name']}{portion} — {item['calories']:.0f} kcal, "
            f"{item['protein_g']:.0f}g protein"
        )

    totals = extraction.get("totals", _zero_totals())
    lines += [
        "",
        (
            f"🍽️ *This meal:* {totals['calories']:.0f} kcal · "
            f"P {totals['protein_g']:.0f}g · C {totals['carbs_g']:.0f}g · F {totals['fat_g']:.0f}g"
        ),
        (
            f"📊 *Today so far:* {daily['calories']:.0f} kcal · "
            f"P {daily['protein_g']:.0f}g · C {daily['carbs_g']:.0f}g · F {daily['fat_g']:.0f}g"
        ),
    ]

    if calorie_target:
        remaining = calorie_target - daily["calories"]
        if remaining >= 0:
            lines.append(f"🎯 *Remaining today:* {remaining:.0f} kcal")
        else:
            lines.append(f"⚠️ *{abs(remaining):.0f} kcal over* your daily target")

    return "\n".join(lines)


# ── Outbound WhatsApp reply ──────────────────────────────────────────────────


def send_whatsapp_reply(to_phone_e164: str, message: str) -> bool:
    """Send a text reply via the Meta Cloud API. Best-effort, never raises."""
    token = settings.whatsapp_access_token
    phone_id = settings.whatsapp_phone_number_id
    if not token or not phone_id:
        logger.warning(
            "WhatsApp reply skipped: WHATSAPP_ACCESS_TOKEN / "
            "WHATSAPP_PHONE_NUMBER_ID not configured"
        )
        return False

    url = f"https://graph.facebook.com/{settings.whatsapp_api_version}/{phone_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": normalize_phone(to_phone_e164),
        "type": "text",
        "text": {"preview_url": False, "body": message[:4096]},
    }
    try:
        response = httpx.post(
            url,
            json=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=10.0,
        )
        if response.status_code >= 400:
            logger.error(
                "WhatsApp reply failed (%s): %s",
                response.status_code,
                response.text[:300],
            )
            return False
        return True
    except httpx.HTTPError:
        logger.exception("WhatsApp reply network error")
        return False
