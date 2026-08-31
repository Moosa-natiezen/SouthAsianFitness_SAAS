"""Tests for Lemon Squeezy billing API endpoints.

Covers:
- Checkout session creation returns a URL
- Unauthenticated users cannot access checkout/portal
- Webhook correctly updates user subscription tier on subscription_created
- Invalid webhook signature is rejected (401)
- Webhook handles subscription_expired correctly
- Portal returns URL for existing customer
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from unittest.mock import MagicMock, patch

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-1234567890abcdefg")
os.environ.setdefault("CSRF_SECRET_KEY", "test-csrf-secret-key-1234567890abcdef")
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("LEMON_SQUEEZY_API_KEY", "ls_test_api_key")
os.environ.setdefault("LEMON_SQUEEZY_WEBHOOK_SECRET", "ls_test_webhook_secret")
os.environ.setdefault("LEMON_SQUEEZY_STORE_ID", "123")
os.environ.setdefault("LEMON_SQUEEZY_VARIANT_ID", "456")
os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")

# Force fresh settings by clearing cache and re-creating
from app.core.config import get_settings

get_settings.cache_clear()
import importlib

import app.core.config

importlib.reload(app.core.config)
# Also reload billing_service so it picks up the fresh settings
import app.services.billing_service
from app.core.config import settings

importlib.reload(app.services.billing_service)

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


def api_register(client: TestClient, email: str = "billing@example.com") -> dict:
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "StrongPass!123",
            "display_name": "Billing User",
        },
    )
    assert response.status_code == 201, response.text
    client.get("/api/auth/csrf")
    return response.json()


def api_login(client: TestClient, email: str = "billing@example.com") -> dict:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "StrongPass!123"},
    )
    assert response.status_code == 200, response.text
    client.get("/api/auth/csrf")
    return response.json()


def get_csrf(client: TestClient) -> str:
    return client.get("/api/auth/csrf").json()["csrf_token"]


def get_user_id_from_db(email: str):
    db = db_session.SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    uid = user.id if user else None
    db.close()
    return uid


def sign_payload(payload_bytes: bytes, secret: str) -> str:
    """Create HMAC-SHA256 signature for webhook testing."""
    return hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()


# ── Checkout tests ────────────────────────────────────────────────────────


def test_checkout_returns_url():
    """Verify POST /api/billing/checkout returns a checkout URL."""
    client = make_client()
    api_register(client)
    client = TestClient(app)
    api_login(client)
    csrf = get_csrf(client)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "data": {
            "attributes": {
                "url": "https://checkout.lemonsqueezy.com/abc123",
            },
        },
    }

    with patch("app.services.billing_service.httpx.post", return_value=mock_response):
        resp = client.post(
            "/api/billing/checkout",
            headers={"X-CSRF-Token": csrf},
        )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "checkout_url" in data
    assert "lemonsqueezy.com" in data["checkout_url"]


def test_checkout_unauthenticated():
    """Verify unauthenticated checkout is rejected."""
    client = make_client()
    resp = client.post("/api/billing/checkout")
    assert resp.status_code in (401, 403)


def test_checkout_missing_csrf():
    """Verify checkout without CSRF token is rejected."""
    client = make_client()
    api_register(client)
    client = TestClient(app)
    api_login(client)

    resp = client.post("/api/billing/checkout")
    assert resp.status_code == 403


# ── Portal tests ──────────────────────────────────────────────────────────


def test_portal_returns_url():
    """Verify POST /api/billing/portal returns a portal URL."""
    client = make_client()
    api_register(client)
    client = TestClient(app)
    api_login(client)
    csrf = get_csrf(client)

    # Set ls_customer_id on the user
    db = db_session.SessionLocal()
    user = db.query(User).filter(User.email == "billing@example.com").first()
    user.ls_customer_id = "ls_cust_123"
    db.commit()
    db.close()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "data": {
            "attributes": {
                "urls": {
                    "customer_portal": "https://portal.lemonsqueezy.com/xyz",
                },
            },
        },
    }

    with patch("app.services.billing_service.httpx.get", return_value=mock_response):
        resp = client.post(
            "/api/billing/portal",
            headers={"X-CSRF-Token": csrf},
        )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "portal_url" in data
    assert "lemonsqueezy.com" in data["portal_url"]


def test_portal_no_customer_id():
    """Verify portal returns 200 with null portal_url when user has no ls_customer_id."""
    client = make_client()
    api_register(client)
    client = TestClient(app)
    api_login(client)
    csrf = get_csrf(client)

    resp = client.post(
        "/api/billing/portal",
        headers={"X-CSRF-Token": csrf},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["portal_url"] is None


# ── Webhook tests ─────────────────────────────────────────────────────────


def test_webhook_subscription_created():
    """Verify webhook correctly updates user tier on subscription_created."""
    client = make_client()
    api_register(client)

    user_id = get_user_id_from_db("billing@example.com")
    assert user_id is not None

    payload = {
        "meta": {"event_name": "subscription_created"},
        "data": {
            "type": "subscriptions",
            "id": "ls_sub_789",
            "attributes": {
                "id": "ls_sub_789",
                "customer_id": "ls_cust_456",
                "status": "active",
                "renews_at": "2026-09-30T00:00:00Z",
                "custom_data": {
                    "user_id": str(user_id),
                },
            },
        },
    }

    raw_body = json.dumps(payload).encode("utf-8")
    signature = sign_payload(raw_body, settings.lemon_squeezy_webhook_secret)

    resp = client.post(
        "/api/billing/webhook",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Signature": signature,
        },
    )
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"status": "ok"}

    # Verify user was updated
    db = db_session.SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    assert user.subscription_tier == "pro"
    assert user.subscription_status == "active"
    assert user.ls_customer_id == "ls_cust_456"
    assert user.ls_subscription_id == "ls_sub_789"
    assert user.subscription_current_period_end is not None
    db.close()


def test_webhook_subscription_expired():
    """Verify webhook downgrades user on subscription_expired."""
    client = make_client()
    api_register(client)

    user_id = get_user_id_from_db("billing@example.com")

    # First, set user to pro
    db = db_session.SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    user.subscription_tier = "pro"
    user.subscription_status = "active"
    db.commit()
    db.close()

    payload = {
        "meta": {"event_name": "subscription_expired"},
        "data": {
            "type": "subscriptions",
            "id": "ls_sub_789",
            "attributes": {
                "custom_data": {"user_id": str(user_id)},
            },
        },
    }

    raw_body = json.dumps(payload).encode("utf-8")
    signature = sign_payload(raw_body, settings.lemon_squeezy_webhook_secret)

    resp = client.post(
        "/api/billing/webhook",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Signature": signature,
        },
    )
    assert resp.status_code == 200

    db = db_session.SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    assert user.subscription_tier == "free"
    assert user.subscription_status == "expired"
    db.close()


def test_webhook_invalid_signature():
    """Verify webhook with invalid X-Signature is rejected."""
    client = make_client()

    payload = {"meta": {"event_name": "test"}, "data": {}}
    raw_body = json.dumps(payload).encode("utf-8")

    resp = client.post(
        "/api/billing/webhook",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Signature": "invalid_signature_123",
        },
    )
    assert resp.status_code == 401


def test_webhook_no_signature():
    """Verify webhook with no X-Signature header is rejected."""
    client = make_client()

    payload = {"meta": {"event_name": "test"}, "data": {}}
    raw_body = json.dumps(payload).encode("utf-8")

    resp = client.post(
        "/api/billing/webhook",
        content=raw_body,
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 401


def test_webhook_missing_user_id():
    """Verify webhook handles missing custom_data.user_id gracefully."""
    client = make_client()

    payload = {
        "meta": {"event_name": "subscription_created"},
        "data": {
            "attributes": {
                "custom_data": {},
            },
        },
    }

    raw_body = json.dumps(payload).encode("utf-8")
    signature = sign_payload(raw_body, settings.lemon_squeezy_webhook_secret)

    resp = client.post(
        "/api/billing/webhook",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Signature": signature,
        },
    )
    # Should still return 200 — we just skip processing
    assert resp.status_code == 200


def test_webhook_signature_verification():
    """Verify the signature verification function directly."""
    from app.services.billing_service import verify_webhook_signature

    body = b"test body"
    secret = "test_secret"
    correct_sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    assert verify_webhook_signature(body, correct_sig, secret) is True
    assert verify_webhook_signature(body, "wrong_sig", secret) is False
    assert verify_webhook_signature(body, None, secret) is False
    assert verify_webhook_signature(body, correct_sig, "") is False
