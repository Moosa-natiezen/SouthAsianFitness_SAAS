"""Tests for AI-powered streaming meal plan generation endpoint.

Covers:
- POST /api/ai/meal-plans/generate (SSE streaming)
- Pro-only access enforcement
- Authentication enforcement
- SSE format correctness
- OpenAI mock streaming
"""

from __future__ import annotations

import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-1234567890abcdefg")
os.environ.setdefault("CSRF_SECRET_KEY", "test-csrf-secret-key-1234567890abcdef")
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-fake-key")
os.environ.setdefault("OPENAI_MODEL", "gpt-4o-mini")
os.environ.setdefault("LEMON_SQUEEZY_API_KEY", "ls_test")
os.environ.setdefault("LEMON_SQUEEZY_WEBHOOK_SECRET", "ls_test_secret")
os.environ.setdefault("LEMON_SQUEEZY_STORE_ID", "1")
os.environ.setdefault("LEMON_SQUEEZY_VARIANT_ID", "1")
os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")

# Force fresh settings
import importlib

from app.core.config import get_settings

get_settings.cache_clear()
import app.core.config
import app.services.ai_service

importlib.reload(app.core.config)
importlib.reload(app.services.ai_service)

from app import models as app_models  # noqa: F401
from app.db import session as db_session
from app.db.base import Base
from app.main import app
from app.models.user import User
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# ── Helpers ───────────────────────────────────────────────────────────────


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


def make_client() -> TestClient:
    reset_db()
    return TestClient(app)


def api_register(client: TestClient, email: str = "ai_test@example.com") -> dict:
    resp = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "StrongPass!123",
            "display_name": "AI Test User",
        },
    )
    assert resp.status_code == 201, resp.text
    client.get("/api/auth/csrf")
    return resp.json()


def api_login(client: TestClient, email: str = "ai_test@example.com") -> dict:
    resp = client.post(
        "/api/auth/login",
        json={"email": email, "password": "StrongPass!123"},
    )
    assert resp.status_code == 200, resp.text
    client.get("/api/auth/csrf")
    return resp.json()


def get_csrf(client: TestClient) -> str:
    return client.get("/api/auth/csrf").json()["csrf_token"]


def get_user_id_from_db(email: str):
    db = db_session.SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    uid = user.id if user else None
    db.close()
    return uid


def setup_pro_client(email: str = "ai_pro@example.com") -> TestClient:
    """Register, login, upgrade to Pro. Returns authenticated client."""
    client = make_client()
    api_register(client, email)
    client = TestClient(app)
    api_login(client, email)

    # Upgrade to pro
    uid = get_user_id_from_db(email)
    db = db_session.SessionLocal()
    user = db.query(User).filter(User.id == uid).first()
    user.subscription_tier = "pro"
    db.commit()
    db.close()
    return client


def _mock_stream_chunks(*texts: str) -> AsyncMock:
    """Build a mock OpenAI streaming response."""
    chunks = []
    for text in texts:
        delta = MagicMock()
        delta.content = text
        choice = MagicMock()
        choice.delta = delta
        choice.index = 0
        chunk = MagicMock()
        chunk.choices = [choice]
        chunks.append(chunk)

    async def _aiter():
        for chunk in chunks:
            yield chunk

    stream = AsyncMock()
    stream.__aiter__ = lambda self: _aiter()
    return stream


def _make_openai_stream_response(*texts: str) -> AsyncMock:
    """Create a mock client.chat.completions.create that yields text chunks."""
    stream = _mock_stream_chunks(*texts)

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=stream)
    return mock_client


# ── Authentication tests ──────────────────────────────────────────────────


def test_ai_generate_unauthenticated():
    """Verify unauthenticated access returns 401."""
    client = make_client()
    resp = client.post(
        "/api/ai/meal-plans/generate",
        json={"target_calories": 2000},
    )
    assert resp.status_code == 401


def test_ai_generate_rejects_free_user():
    """Verify free-tier user gets 403 with PRO_REQUIRED code."""
    client = make_client()
    api_register(client)
    client = TestClient(app)
    api_login(client)

    resp = client.post(
        "/api/ai/meal-plans/generate",
        json={"target_calories": 2000},
    )
    assert resp.status_code == 403
    body = resp.json()
    assert body["detail"]["code"] == "PRO_REQUIRED"


# ── Streaming format tests ────────────────────────────────────────────────


def test_ai_generate_streams_sse():
    """Verify the endpoint returns valid SSE-formatted streaming response."""
    client = setup_pro_client()

    mock_client = _make_openai_stream_response("Hello ", "world!")

    with (
        patch("app.services.ai_service.AsyncOpenAI", return_value=mock_client),
        patch("app.services.ai_service.settings.openai_api_key", "sk-test-fake-key"),
    ):
        resp = client.post(
            "/api/ai/meal-plans/generate",
            json={"target_calories": 2000, "protein_g": 100},
        )

    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]

    # Parse SSE data lines
    lines = resp.text.strip().split("\n")
    data_lines = [l for l in lines if l.startswith("data: ")]

    # Should have chunk1, chunk2, and [DONE]
    assert len(data_lines) >= 3

    # First chunk
    chunk1 = json.loads(data_lines[0].removeprefix("data: "))
    assert chunk1 == {"text": "Hello "}

    # Second chunk
    chunk2 = json.loads(data_lines[1].removeprefix("data: "))
    assert chunk2 == {"text": "world!"}

    # Done marker
    assert data_lines[2] == "data: [DONE]"


def test_ai_generate_no_buffering_header():
    """Verify X-Accel-Buffering: no is set for Nginx proxy compatibility."""
    client = setup_pro_client()

    mock_client = _make_openai_stream_response("test")

    with (
        patch("app.services.ai_service.AsyncOpenAI", return_value=mock_client),
        patch("app.services.ai_service.settings.openai_api_key", "sk-test-fake-key"),
    ):
        resp = client.post(
            "/api/ai/meal-plans/generate",
            json={},
        )

    assert resp.status_code == 200
    assert resp.headers.get("X-Accel-Buffering") == "no"
    assert resp.headers.get("Cache-Control") == "no-cache"


# ── Request schema tests ──────────────────────────────────────────────────


def test_ai_generate_with_all_params():
    """Verify all request parameters are accepted."""
    client = setup_pro_client()

    mock_client = _make_openai_stream_response("plan")

    with (
        patch("app.services.ai_service.AsyncOpenAI", return_value=mock_client),
        patch("app.services.ai_service.settings.openai_api_key", "sk-test-fake-key"),
    ):
        resp = client.post(
            "/api/ai/meal-plans/generate",
            json={
                "target_calories": 2200,
                "protein_g": 120,
                "dietary_preferences": ["halal", "no-pork"],
                "allergies": ["peanuts", "shellfish"],
                "cuisine_type": "South Asian",
            },
        )

    assert resp.status_code == 200

    # Verify the prompt was built with these params
    call_args = mock_client.chat.completions.create.call_args
    messages = call_args.kwargs["messages"]
    user_msg = messages[1]["content"]
    assert "2200" in user_msg
    assert "120" in user_msg
    assert "halal" in user_msg
    assert "peanuts" in user_msg
    assert "South Asian" in user_msg


def test_ai_generate_empty_request():
    """Verify empty request body is accepted."""
    client = setup_pro_client()

    mock_client = _make_openai_stream_response("plan")

    with (
        patch("app.services.ai_service.AsyncOpenAI", return_value=mock_client),
        patch("app.services.ai_service.settings.openai_api_key", "sk-test-fake-key"),
    ):
        resp = client.post(
            "/api/ai/meal-plans/generate",
            json={},
        )

    assert resp.status_code == 200


# ── Error handling tests ──────────────────────────────────────────────────


def test_ai_generate_openai_failure():
    """Verify graceful fallback to sandbox when OpenAI API call fails."""
    client = setup_pro_client()

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=Exception("OpenAI API error")
    )

    with patch("app.services.ai_service.AsyncOpenAI", return_value=mock_client):
        resp = client.post(
            "/api/ai/meal-plans/generate",
            json={"target_calories": 2000},
        )

    assert resp.status_code == 200
    lines = resp.text.strip().split("\n")
    data_lines = [l for l in lines if l.startswith("data: ")]
    assert len(data_lines) >= 2

    # First chunk should carry the sandbox flag
    first_chunk = json.loads(data_lines[0].removeprefix("data: "))
    assert first_chunk.get("sandbox") is True
    # Must end with [DONE]
    assert data_lines[-1] == "data: [DONE]"


def test_ai_generate_no_api_key():
    """Verify graceful fallback to sandbox when OPENAI_API_KEY is not set."""
    client = setup_pro_client()

    # Clear the key from settings
    from app.core.config import settings
    original_key = settings.openai_api_key
    settings.openai_api_key = ""

    try:
        resp = client.post(
            "/api/ai/meal-plans/generate",
            json={"target_calories": 2000},
        )

        assert resp.status_code == 200
        lines = resp.text.strip().split("\n")
        data_lines = [l for l in lines if l.startswith("data: ")]
        # Should stream sandbox content, not an error
        first_chunk = json.loads(data_lines[0].removeprefix("data: "))
        assert first_chunk.get("sandbox") is True
        assert data_lines[-1] == "data: [DONE]"
    finally:
        settings.openai_api_key = original_key


# ── AI context personalization tests ─────────────────────────────────────


def _setup_pro_user_with_profile(
    client: TestClient,
    email: str = "ai_pro_ctx@example.com",
) -> None:
    """Give the pro user a populated profile so AI context has data."""
    from app.models.enums import (
        ActivityLevel,
        DietPattern,
        FitnessGoal,
        Sex,
    )
    from app.models.user import UserProfile

    uid = get_user_id_from_db(email)
    db = db_session.SessionLocal()
    try:
        profile = UserProfile(
            user_id=uid,
            age_years=28,
            sex=Sex.MALE,
            height_cm=175,
            weight_kg=72,
            activity_level=ActivityLevel.MODERATELY_ACTIVE,
            fitness_goal=FitnessGoal.WEIGHT_LOSS,
            diet_pattern=DietPattern.OMNIVORE,
            target_calories=2000,
            target_protein_g=120,
        )
        db.add(profile)
        db.commit()
    finally:
        db.close()


def test_ai_generate_injects_user_context_into_system_prompt():
    """Verify the user's persistent AI context is merged into the system prompt."""
    client = setup_pro_client(email="ai_pro_ctx@example.com")
    _setup_pro_user_with_profile(client, "ai_pro_ctx@example.com")

    mock_client = _make_openai_stream_response("personalized plan")

    with (
        patch("app.services.ai_service.AsyncOpenAI", return_value=mock_client),
        patch("app.services.ai_service.settings.openai_api_key", "sk-test-fake-key"),
    ):
        resp = client.post(
            "/api/ai/meal-plans/generate",
            json={"target_calories": 2000, "protein_g": 120},
        )

    assert resp.status_code == 200

    call_args = mock_client.chat.completions.create.call_args
    messages = call_args.kwargs["messages"]
    system_msg = messages[0]["content"]

    # The merged prompt should contain the static prompt AND the user context
    assert "South Asian fitness nutritionist" in system_msg
    assert "USER CONTEXT" in system_msg
    assert "cutting" in system_msg  # WEIGHT_LOSS → cutting
    assert "2000 calories/day" in system_msg
    assert "120g protein/day" in system_msg
    assert "28 years old" in system_msg


def test_ai_generate_falls_back_to_generic_prompt_without_profile():
    """Verify users without a profile still get the generic system prompt."""
    client = setup_pro_client(email="ai_pro_noprofile@example.com")

    mock_client = _make_openai_stream_response("generic plan")

    with (
        patch("app.services.ai_service.AsyncOpenAI", return_value=mock_client),
        patch("app.services.ai_service.settings.openai_api_key", "sk-test-fake-key"),
    ):
        resp = client.post(
            "/api/ai/meal-plans/generate",
            json={"target_calories": 2000},
        )

    assert resp.status_code == 200

    call_args = mock_client.chat.completions.create.call_args
    messages = call_args.kwargs["messages"]
    system_msg = messages[0]["content"]

    # Falls back gracefully: static prompt always present, and no
    # personalisation details (no profile → no goal/targets injected)
    assert "South Asian fitness nutritionist" in system_msg
    assert "cutting" not in system_msg
    assert "2000 calories/day" not in system_msg


def test_system_prompt_mentions_south_asian():
    """Verify the system prompt instructs the AI about South Asian cuisine."""
    from app.services.ai_service import SYSTEM_PROMPT

    assert "South Asian" in SYSTEM_PROMPT
    assert "Pakistan" in SYSTEM_PROMPT
    assert "India" in SYSTEM_PROMPT
    assert "json" in SYSTEM_PROMPT.lower()
