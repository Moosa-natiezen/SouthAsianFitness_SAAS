"""Tests for the Vapi.ai tool-calls webhook.

Covers:
- Tool-calls payload returns Vapi's exact response schema
  ({"results": [{"toolCallId", "result"}]}) with the id echoed back
- log_meal end-to-end: linked phone → LLM extraction → FoodLogEntry →
  confirmation string with meal macros and remaining daily calories
- Unlinked phone numbers get the sign-up nudge, not a crash (and skip the LLM)
- Non-food text returns help without persisting anything
- Unknown tool names are reported inside the result, not as an HTTP error
- Non tool-calls message types (status-update, transcript) get an empty
  results list
- Authentication: rejected without x-vapi-secret when VAPI_SERVER_SECRET
  is set; accepted with the right secret; skipped-with-warning when unset
- Arguments delivered as a JSON string are parsed (Vapi does this sometimes)
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-1234567890abcdefg")
os.environ.setdefault("CSRF_SECRET_KEY", "test-csrf-secret-key-1234567890abcdef")
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("DEBUG", "false")

from decimal import Decimal
from unittest.mock import AsyncMock

from app import models as app_models  # noqa: F401
from app.api.routes import vapi
from app.core.config import settings
from app.db import session as db_session
from app.db.base import Base
from app.main import app
from app.models.user import User
from app.models.whatsapp import FoodLogEntry
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
    ],
    "totals": {"calories": 620.0, "protein_g": 28.0, "carbs_g": 75.0, "fat_g": 22.0},
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
    return TestClient(app)


def make_user(db: Session, *, phone: str | None = WA_ID) -> User:
    user = User(
        email="vapi@example.com",
        display_name="Voice User",
        password_hash="fakehash",
        whatsapp_phone=phone,
    )
    db.add(user)
    db.commit()
    return user


def tool_call_payload(
    *,
    tool_call_id: str = "call_123",
    name: str = "log_meal",
    arguments: dict | str | None = None,
    message_type: str = "tool-calls",
) -> dict:
    message: dict = {"type": message_type}
    if message_type == "tool-calls":
        args = arguments if arguments is not None else {
            "phone_number": f"+{WA_ID}",
            "food_text": "a plate of chicken biryani",
        }
        message["toolCallList"] = [
            {"id": tool_call_id, "name": name, "arguments": args}
        ]
    return {"message": message}


def post_payload(client: TestClient, payload: dict, *, secret: str | None = None):
    headers = {"Content-Type": "application/json"}
    if secret is not None:
        headers["x-vapi-secret"] = secret
    return client.post("/api/vapi/webhook", json=payload, headers=headers)


# ── Response schema + end-to-end logging ────────────────────────────────────


def test_log_meal_returns_vapi_schema_and_logs(monkeypatch):
    client = make_client()
    db = db_session.SessionLocal()
    make_user(db)
    monkeypatch.setattr(vapi, "extract_foods_from_text", AsyncMock(return_value=EXTRACTION))

    response = post_payload(client, tool_call_payload(tool_call_id="call_abc"))

    assert response.status_code == 200
    body = response.json()
    # Exact Vapi tool-calls response schema
    assert set(body.keys()) == {"results"}
    assert len(body["results"]) == 1
    result = body["results"][0]
    assert set(result.keys()) == {"toolCallId", "result"}
    assert result["toolCallId"] == "call_abc"

    # Entry persisted through the shared WhatsApp pipeline
    entry = db.query(FoodLogEntry).one()
    assert float(entry.calories) == 620.0
    assert entry.source == "whatsapp"  # shared pipeline default

    # Result string: meal macros + remaining daily calories
    assert "Logged" in result["result"]
    assert "This meal:* 620 kcal" in result["result"]


def test_log_meal_includes_remaining_calories(monkeypatch):
    client = make_client()
    db = db_session.SessionLocal()
    user = make_user(db)
    from app.models.enums import ActivityLevel, Sex
    from app.models.user import UserProfile

    db.add(
        UserProfile(
            user_id=user.id,
            age_years=28,
            sex=Sex.MALE,
            height_cm=Decimal(175),
            weight_kg=Decimal(75),
            activity_level=ActivityLevel.MODERATELY_ACTIVE,
            fitness_goal="muscle_building",
            target_calories=2000,
        )
    )
    db.commit()
    monkeypatch.setattr(vapi, "extract_foods_from_text", AsyncMock(return_value=EXTRACTION))

    response = post_payload(client, tool_call_payload())
    result = response.json()["results"][0]["result"]
    # 2000 target - 620 logged = 1380 remaining
    assert "Remaining today:* 1380 kcal" in result


# ── Unlinked / invalid inputs ────────────────────────────────────────────────


def test_unlinked_phone_returns_nudge_without_llm(monkeypatch):
    client = make_client()
    db = db_session.SessionLocal()
    make_user(db, phone="999999999999")  # different number
    llm_mock = AsyncMock(return_value=EXTRACTION)
    monkeypatch.setattr(vapi, "extract_foods_from_text", llm_mock)

    response = post_payload(client, tool_call_payload())
    result = response.json()["results"][0]["result"]

    assert "isn't linked" in result
    assert "southasianfitness.com" in result
    llm_mock.assert_not_awaited()
    assert db.query(FoodLogEntry).count() == 0


def test_missing_food_text_returns_help(monkeypatch):
    client = make_client()
    db = db_session.SessionLocal()
    make_user(db)
    llm_mock = AsyncMock(return_value=EMPTY_EXTRACTION)
    monkeypatch.setattr(vapi, "extract_foods_from_text", llm_mock)

    response = post_payload(
        client, tool_call_payload(arguments={"phone_number": f"+{WA_ID}", "food_text": ""})
    )
    result = response.json()["results"][0]["result"]

    assert "couldn't find any food" in result
    llm_mock.assert_not_awaited()
    assert db.query(FoodLogEntry).count() == 0


def test_missing_phone_returns_error_result():
    client = make_client()
    db = db_session.SessionLocal()
    make_user(db)

    response = post_payload(
        client, tool_call_payload(arguments={"food_text": "2 roti"})
    )
    result = response.json()["results"][0]["result"]
    assert "phone number" in result.lower()


def test_non_food_text_not_persisted(monkeypatch):
    client = make_client()
    db = db_session.SessionLocal()
    make_user(db)
    monkeypatch.setattr(vapi, "extract_foods_from_text", AsyncMock(return_value=EMPTY_EXTRACTION))

    response = post_payload(
        client, tool_call_payload(arguments={"phone_number": f"+{WA_ID}", "food_text": "haha lol"})
    )
    assert response.status_code == 200
    result = response.json()["results"][0]["result"]
    assert "couldn't find any food" in result
    assert db.query(FoodLogEntry).count() == 0


# ── Protocol edge cases ──────────────────────────────────────────────────────


def test_unknown_tool_reported_in_result():
    client = make_client()
    response = post_payload(
        client, tool_call_payload(name="order_pizza", arguments={})
    )
    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["toolCallId"] == "call_123"
    assert "order_pizza" in result["result"]
    assert "Unknown tool" in result["result"]


def test_non_tool_calls_message_type_gets_empty_results():
    client = make_client()
    for message_type in ("status-update", "transcript", "end-of-call-report"):
        response = post_payload(
            client, tool_call_payload(message_type=message_type)
        )
        assert response.status_code == 200
        assert response.json() == {"results": []}


def test_arguments_as_json_string_are_parsed(monkeypatch):
    client = make_client()
    db = db_session.SessionLocal()
    make_user(db)
    monkeypatch.setattr(vapi, "extract_foods_from_text", AsyncMock(return_value=EXTRACTION))

    import json

    response = post_payload(
        client,
        tool_call_payload(
            arguments=json.dumps({"phone_number": f"+{WA_ID}", "food_text": "daal"})
        ),
    )
    result = response.json()["results"][0]["result"]
    assert "Logged" in result
    assert db.query(FoodLogEntry).count() == 1


# ── Authentication ───────────────────────────────────────────────────────────


def test_rejects_missing_secret_when_configured(monkeypatch):
    monkeypatch.setattr(vapi.settings, "vapi_server_secret", "s3cret")
    client = make_client()
    response = post_payload(client, tool_call_payload())
    assert response.status_code == 401


def test_rejects_wrong_secret_when_configured(monkeypatch):
    monkeypatch.setattr(vapi.settings, "vapi_server_secret", "s3cret")
    client = make_client()
    response = post_payload(client, tool_call_payload(), secret="wrong")
    assert response.status_code == 401


def test_accepts_correct_secret(monkeypatch):
    monkeypatch.setattr(vapi.settings, "vapi_server_secret", "s3cret")
    client = make_client()
    response = post_payload(client, tool_call_payload(), secret="s3cret")
    assert response.status_code == 200


def test_skips_verification_when_secret_unset(monkeypatch):
    monkeypatch.setattr(vapi.settings, "vapi_server_secret", "")
    client = make_client()
    db = db_session.SessionLocal()
    make_user(db)
    monkeypatch.setattr(vapi, "extract_foods_from_text", AsyncMock(return_value=EXTRACTION))
    response = post_payload(client, tool_call_payload())  # no header at all
    assert response.status_code == 200


def test_send_whatsapp_reply_not_used_by_vapi():
    # Voice results are returned in the HTTP response — no outbound sends.
    import inspect

    from app.api.routes import vapi as vapi_module

    source = inspect.getsource(vapi_module)
    assert "send_whatsapp_reply" not in source
