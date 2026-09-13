"""Tests for the WhatsApp webhook and chat-based meal logging service.

Covers:
- GET subscription handshake (correct + wrong verify token)
- POST signature verification (valid, invalid, unset secret)
- Unlinked phone numbers get the sign-up nudge, not a crash (and skip the LLM)
- End-to-end food logging: LLM extraction → FoodLogEntry → confirmation
  reply with the updated daily calorie count and remaining-vs-target
- "No food found" messages reply with usage help
- Non-text messages get help without touching the LLM
- Meta redelivery de-duplication by message id
- Status receipts (no messages) are ignored gracefully
- Service units: phone normalization, daily totals, confirmation formatting
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-1234567890abcdefg")
os.environ.setdefault("CSRF_SECRET_KEY", "test-csrf-secret-key-1234567890abcdef")
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("DEBUG", "false")

import hashlib
import hmac
import json
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from app import models as app_models  # noqa: F401
from app.api import whatsapp as wa
from app.core.config import settings
from app.db import session as db_session
from app.db.base import Base
from app.main import app
from app.models.enums import ActivityLevel, DietPattern, FitnessGoal, Sex
from app.models.user import User, UserProfile
from app.models.whatsapp import FoodLogEntry
from app.services.whatsapp_service import (
    build_confirmation_message,
    get_daily_totals,
    normalize_phone,
    persist_food_log,
)
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

WA_ID = "923001234567"

EXTRACTION = {
    "items": [
        {
            "name": "Chicken Biryani",
            "portion": "1 plate",
            "calories": 620.0,
            "protein_g": 28.0,
            "carbs_g": 75.0,
            "fat_g": 22.0,
        },
        {
            "name": "Roti",
            "portion": "1 piece",
            "calories": 120.0,
            "protein_g": 4.0,
            "carbs_g": 20.0,
            "fat_g": 3.0,
        },
    ],
    "totals": {"calories": 740.0, "protein_g": 32.0, "carbs_g": 95.0, "fat_g": 25.0},
}

EMPTY_EXTRACTION = {
    "items": [],
    "totals": {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0},
}


# ── Test helpers ─────────────────────────────────────────────────────────────


def reset_db() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db_session.engine = engine
    db_session.SessionLocal = sessionmaker(
        bind=engine, autocommit=False, autoflush=False, class_=Session
    )
    settings.database_url = str(engine.url)


def make_client() -> TestClient:
    reset_db()
    # The inbound-message de-dup cache is process-global — clear it so
    # identical message ids across tests don't suppress processing.
    wa._recent_message_ids.clear()
    return TestClient(app)


def make_user(db: Session, *, phone: str | None = WA_ID) -> User:
    user = User(
        email="wa@example.com",
        display_name="WhatsApp User",
        password_hash="fakehash",
        whatsapp_phone=phone,
    )
    db.add(user)
    db.commit()
    return user


def wa_payload(
    text: str | None = "2 roti and a bowl of daal",
    *,
    type_: str = "text",
    message_id: str = "wamid.test001",
) -> bytes:
    message: dict = {"from": WA_ID, "id": message_id, "timestamp": "1726200000", "type": type_}
    if type_ == "text" and text is not None:
        message["text"] = {"body": text}
    return json.dumps(
        {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "WABA123",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {"phone_number_id": "PNID"},
                                "contacts": [{"wa_id": WA_ID}],
                                "messages": [message],
                            },
                            "field": "messages",
                        }
                    ],
                }
            ],
        }
    ).encode()


def signed(body: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def post_message(client: TestClient, body: bytes, *, secret: str | None = None) -> object:
    headers = {"Content-Type": "application/json"}
    if secret is not None:
        headers["X-Hub-Signature-256"] = signed(body, secret)
    return client.post("/api/whatsapp/webhook", content=body, headers=headers)


# ── GET subscription handshake ───────────────────────────────────────────────


def test_verify_webhook_accepts_correct_token(monkeypatch):
    # Patch via the route module's binding (wa.settings), not our imported
    # reference — the known settings-reload quirk can leave two Settings
    # instances alive in full-suite ordering, and the route reads its own.
    monkeypatch.setattr(wa.settings, "whatsapp_verify_token", "tok123")
    client = make_client()
    response = client.get(
        "/api/whatsapp/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "tok123",
            "hub.challenge": "CHALLENGE_42",
        },
    )
    assert response.status_code == 200
    assert response.text == "CHALLENGE_42"


def test_verify_webhook_rejects_wrong_token(monkeypatch):
    monkeypatch.setattr(wa.settings, "whatsapp_verify_token", "tok123")
    client = make_client()
    response = client.get(
        "/api/whatsapp/webhook",
        params={"hub.mode": "subscribe", "hub.verify_token": "WRONG", "hub.challenge": "X"},
    )
    assert response.status_code == 403


# ── POST signature verification ──────────────────────────────────────────────


def test_post_rejects_invalid_signature(monkeypatch):
    monkeypatch.setattr(wa.settings, "whatsapp_app_secret", "appsecret")
    client = make_client()
    response = client.post(
        "/api/whatsapp/webhook",
        content=wa_payload(),
        headers={
            "X-Hub-Signature-256": "sha256=" + "0" * 64,
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 401


def test_post_accepts_valid_signature(monkeypatch):
    monkeypatch.setattr(wa.settings, "whatsapp_app_secret", "appsecret")
    client = make_client()
    make_user(db_session.SessionLocal())
    monkeypatch.setattr(wa, "extract_foods_from_text", AsyncMock(return_value=EXTRACTION))
    # send_whatsapp_reply is sync (httpx.post) — MagicMock, not AsyncMock.
    monkeypatch.setattr(wa, "send_whatsapp_reply", MagicMock(return_value=True))

    response = post_message(client, wa_payload(), secret="appsecret")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_post_without_secret_configured_skips_verification(monkeypatch):
    # Dev mode: no WHATSAPP_APP_SECRET → payload accepted unsigned.
    monkeypatch.setattr(wa.settings, "whatsapp_app_secret", "")
    client = make_client()
    make_user(db_session.SessionLocal())
    monkeypatch.setattr(wa, "extract_foods_from_text", AsyncMock(return_value=EXTRACTION))
    monkeypatch.setattr(wa, "send_whatsapp_reply", MagicMock(return_value=True))

    response = post_message(client, wa_payload())
    assert response.status_code == 200


# ── Message processing ───────────────────────────────────────────────────────


def test_food_message_persists_entry_and_replies_with_daily_total(monkeypatch):
    client = make_client()
    db = db_session.SessionLocal()
    make_user(db)
    monkeypatch.setattr(wa, "extract_foods_from_text", AsyncMock(return_value=EXTRACTION))
    reply_mock = MagicMock(return_value=True)
    monkeypatch.setattr(wa, "send_whatsapp_reply", reply_mock)

    response = post_message(client, wa_payload())
    assert response.status_code == 200

    # Entry persisted with the LLM-extracted totals
    entry = db.query(FoodLogEntry).one()
    assert float(entry.calories) == 740.0
    assert float(entry.protein_g) == 32.0
    assert entry.source == "whatsapp"
    assert "Biryani" in entry.food_items_json

    # Reply echoes the meal + updated daily count
    assert reply_mock.call_count == 1
    reply_text = reply_mock.call_args.args[1]
    assert "Logged" in reply_text
    assert "This meal:* 740 kcal" in reply_text
    today_section = reply_text.split("Today so far")[1]
    assert "740 kcal" in today_section
    assert "P 32g" in today_section


def test_food_message_includes_remaining_vs_target(monkeypatch):
    client = make_client()
    db = db_session.SessionLocal()
    user = make_user(db)
    db.add(
        UserProfile(
            user_id=user.id,
            age_years=28,
            sex=Sex.MALE,
            height_cm=Decimal(175),
            weight_kg=Decimal(75),
            activity_level=ActivityLevel.MODERATELY_ACTIVE,
            fitness_goal=FitnessGoal.WEIGHT_LOSS,
            diet_pattern=DietPattern.OMNIVORE,
            target_calories=2000,
        )
    )
    db.commit()

    monkeypatch.setattr(wa, "extract_foods_from_text", AsyncMock(return_value=EXTRACTION))
    reply_mock = MagicMock(return_value=True)
    monkeypatch.setattr(wa, "send_whatsapp_reply", reply_mock)

    post_message(client, wa_payload())

    reply_text = reply_mock.call_args.args[1]
    assert "Remaining today:* 1260 kcal" in reply_text


def test_message_with_no_food_replies_with_help(monkeypatch):
    client = make_client()
    db = db_session.SessionLocal()
    make_user(db)
    monkeypatch.setattr(wa, "extract_foods_from_text", AsyncMock(return_value=EMPTY_EXTRACTION))
    reply_mock = MagicMock(return_value=True)
    monkeypatch.setattr(wa, "send_whatsapp_reply", reply_mock)

    response = post_message(client, wa_payload("haha lol"))
    assert response.status_code == 200

    assert "couldn't find any food" in reply_mock.call_args.args[1]
    # Nothing persisted for a no-food message
    assert db.query(FoodLogEntry).count() == 0


def test_unlinked_number_gets_signup_nudge_and_skips_llm(monkeypatch):
    client = make_client()
    db = db_session.SessionLocal()
    make_user(db, phone="9999999999")  # different number
    llm_mock = AsyncMock(return_value=EXTRACTION)
    monkeypatch.setattr(wa, "extract_foods_from_text", llm_mock)
    reply_mock = MagicMock(return_value=True)
    monkeypatch.setattr(wa, "send_whatsapp_reply", reply_mock)

    response = post_message(client, wa_payload())
    assert response.status_code == 200

    assert "isn't linked" in reply_mock.call_args.args[1]
    assert llm_mock.await_count == 0  # token saver: no LLM call for strangers
    assert db.query(FoodLogEntry).count() == 0


def test_non_text_message_gets_help_without_llm(monkeypatch):
    client = make_client()
    db = db_session.SessionLocal()
    make_user(db)
    llm_mock = AsyncMock(return_value=EXTRACTION)
    monkeypatch.setattr(wa, "extract_foods_from_text", llm_mock)
    reply_mock = MagicMock(return_value=True)
    monkeypatch.setattr(wa, "send_whatsapp_reply", reply_mock)

    response = post_message(client, wa_payload(None, type_="image"))
    assert response.status_code == 200
    assert llm_mock.await_count == 0
    assert "Send me what you ate" in reply_mock.call_args.args[1]


def test_meta_redelivery_is_deduplicated_by_message_id(monkeypatch):
    client = make_client()
    db = db_session.SessionLocal()
    make_user(db)
    monkeypatch.setattr(wa, "extract_foods_from_text", AsyncMock(return_value=EXTRACTION))
    monkeypatch.setattr(wa, "send_whatsapp_reply", MagicMock(return_value=True))

    for _ in range(2):
        response = post_message(client, wa_payload())
        assert response.status_code == 200

    # Only ONE food log entry despite Meta's double delivery
    assert db.query(FoodLogEntry).count() == 1


def test_status_receipt_without_messages_is_ignored(monkeypatch):
    client = make_client()
    make_user(db_session.SessionLocal())
    llm_mock = AsyncMock(return_value=EXTRACTION)
    monkeypatch.setattr(wa, "extract_foods_from_text", llm_mock)

    payload = json.dumps(
        {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "WABA123",
                    "changes": [
                        {
                            "value": {"statuses": [{"id": "wamid.x", "status": "delivered"}]},
                            "field": "messages",
                        }
                    ],
                }
            ],
        }
    ).encode()
    response = client.post(
        "/api/whatsapp/webhook", content=payload, headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 200
    assert llm_mock.await_count == 0


# ── Service units ────────────────────────────────────────────────────────────


def test_normalize_phone_strips_non_digits_and_leading_zeros():
    assert normalize_phone("+92 300-1234567") == "923001234567"
    assert normalize_phone("(0300) 123-4567") == "3001234567"
    assert normalize_phone("923001234567") == "923001234567"


def test_get_daily_totals_sums_multiple_entries():
    db = db_session.SessionLocal()
    user = User(
        email="totals@example.com",
        display_name="Totals",
        password_hash="fakehash",
    )
    db.add(user)
    db.commit()

    extraction_a = {
        "items": [{"name": "Daal", "portion": "1 bowl", "calories": 200.0, "protein_g": 12.0, "carbs_g": 30.0, "fat_g": 4.0}],
        "totals": {"calories": 200.0, "protein_g": 12.0, "carbs_g": 30.0, "fat_g": 4.0},
    }
    extraction_b = {
        "items": [{"name": "Roti", "portion": "2", "calories": 240.0, "protein_g": 8.0, "carbs_g": 40.0, "fat_g": 6.0}],
        "totals": {"calories": 240.0, "protein_g": 8.0, "carbs_g": 40.0, "fat_g": 6.0},
    }

    persist_food_log(db, user_id=user.id, raw_text="daal", extraction=extraction_a)
    persist_food_log(db, user_id=user.id, raw_text="roti", extraction=extraction_b)

    daily = get_daily_totals(db, user.id)
    assert daily["calories"] == 440.0
    assert daily["protein_g"] == 20.0
    assert daily["carbs_g"] == 70.0
    assert daily["fat_g"] == 10.0


def test_build_confirmation_message_empty_extraction():
    message = build_confirmation_message(EMPTY_EXTRACTION, EMPTY_EXTRACTION["totals"])
    assert "couldn't find any food" in message


def test_build_confirmation_message_flags_over_target():
    extraction = {
        "items": [{"name": "Biryani", "portion": "2 plates", "calories": 1200.0, "protein_g": 40.0, "carbs_g": 150.0, "fat_g": 45.0}],
        "totals": {"calories": 1200.0, "protein_g": 40.0, "carbs_g": 150.0, "fat_g": 45.0},
    }
    daily = {"calories": 1800.0, "protein_g": 70.0, "carbs_g": 220.0, "fat_g": 60.0}

    over = build_confirmation_message(extraction, daily, calorie_target=1500)
    assert "300 kcal over" in over

    within = build_confirmation_message(extraction, daily, calorie_target=2000)
    assert "Remaining today:* 200 kcal" in within
