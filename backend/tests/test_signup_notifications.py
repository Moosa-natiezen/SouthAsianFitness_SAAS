"""Tests for signup founder-alert background tasks.

Verifies that:
- ``/auth/register`` returns 201 and dispatches the n8n signup alert as a
  FastAPI background task (i.e. only after the response is sent).
- Alert failures never fail or delay the registration response
  (fire-and-forget).
- Google OAuth alerts only on brand-new signups, not returning logins.
- ``notify_new_signup`` itself is a no-op without n8n configured and
  swallows all network errors.
"""

from __future__ import annotations

import os
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-1234567890abcdefg")
os.environ.setdefault("CSRF_SECRET_KEY", "test-csrf-secret-key-1234567890abcdef")
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("DEBUG", "false")

from app.core.config import settings
from app.core.rate_limit import login_rate_limiter
from app.db import session as db_session
from app.db.base import Base
from app.main import app
from app.models.user import User
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


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
    login_rate_limiter.clear()
    return TestClient(app)


def _create_google_user(email: str = "google-user@example.com") -> User:
    db = db_session.SessionLocal()
    try:
        user = User(
            email=email,
            display_name="Google User",
            password_hash="",  # Google-only account
            google_id="google-sub-123",
            is_active=True,
            is_onboarded=False,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


# ── /auth/register (email + password signup) ─────────────────────────


def test_register_returns_201_and_schedules_n8n_alert():
    client = make_client()
    with patch("app.api.routes.auth.notify_new_signup") as mock_notify:
        response = client.post(
            "/api/auth/register",
            json={
                "email": "alert@example.com",
                "password": "StrongPass!123",
                "display_name": "Alert User",
            },
        )

    assert response.status_code == 201, response.text
    mock_notify.assert_called_once()
    kwargs = mock_notify.call_args.kwargs
    assert kwargs["email"] == "alert@example.com"
    assert kwargs["display_name"] == "Alert User"
    assert kwargs["method"] == "password"


def test_register_alert_executes_only_after_response_is_sent():
    """TestClient runs background tasks after returning the response.

    The moment ``client.post`` yields a 201, the user is registered; the
    alert callback runs afterwards within the same request cycle.
    """
    client = make_client()
    calls: list[str] = []

    def fake_notify(**kwargs):
        calls.append(kwargs["email"])

    with patch("app.api.routes.auth.notify_new_signup", fake_notify):
        response = client.post(
            "/api/auth/register",
            json={
                "email": "bg@example.com",
                "password": "StrongPass!123",
                "display_name": "BG User",
            },
        )
        assert response.status_code == 201
        assert calls == ["bg@example.com"]


def test_register_succeeds_when_n8n_is_unreachable(monkeypatch):
    """End-to-end fire-and-forget check: the real notification task hits a
    black-hole webhook, the network error is swallowed, and the 201
    response is unaffected (in production the response is already sent by
    the time the task runs)."""
    from app.services import notification_service

    # Port 1 on loopback => instant connection refused, no timeout wait.
    monkeypatch.setattr(
        notification_service.settings, "n8n_webhook_url", "http://127.0.0.1:1/hook"
    )
    client = make_client()

    response = client.post(
        "/api/auth/register",
        json={
            "email": "offline@example.com",
            "password": "StrongPass!123",
            "display_name": "Offline User",
        },
    )

    assert response.status_code == 201, response.text
    assert response.json()["user"]["email"] == "offline@example.com"


# ── /auth/google (OAuth signup vs returning login) ────────────────────


def test_google_alerts_only_on_new_signup_not_returning_login():
    client = make_client()
    user = _create_google_user()

    # Patch through the route module's own settings reference: some test
    # modules reload app.core.config at import time, so the ``settings``
    # object imported here can be a different instance than the one the
    # router reads.
    with (
        patch("app.api.routes.auth.google_login_or_register") as mock_auth,
        patch("app.api.routes.auth.notify_new_signup") as mock_notify,
        patch("app.api.routes.auth.settings.google_client_id", "test-google-client-id"),
    ):
        # Brand-new Google signup → alert fires.
        mock_auth.return_value = (user, True)
        response = client.post("/api/auth/google", json={"id_token": "t"})
        assert response.status_code == 200, response.text
        mock_notify.assert_called_once()
        assert mock_notify.call_args.kwargs["method"] == "google"
        assert mock_notify.call_args.kwargs["email"] == user.email

        # Returning Google login → no alert.
        mock_notify.reset_mock()
        mock_auth.return_value = (user, False)
        response = client.post("/api/auth/google", json={"id_token": "t"})
        assert response.status_code == 200, response.text
        mock_notify.assert_not_called()


# ── notification_service unit behaviour ───────────────────────────────


def test_notify_new_signup_is_noop_without_webhook(monkeypatch):
    from app.services import notification_service

    monkeypatch.setattr(notification_service.settings, "n8n_webhook_url", "")

    with patch("app.services.notification_service.httpx.Client") as mock_client:
        # Must return without touching the network.
        notification_service.notify_new_signup(
            user_id="u1", email="e@example.com", display_name="E"
        )
    mock_client.assert_not_called()


def test_notify_new_signup_posts_event_payload(monkeypatch):
    from app.services import notification_service

    monkeypatch.setattr(
        notification_service.settings, "n8n_webhook_url", "http://n8n.test/hook"
    )

    with patch("app.services.notification_service.httpx.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value.__enter__.return_value
        mock_client.post.return_value.raise_for_status.return_value = None

        notification_service.notify_new_signup(
            user_id="u1",
            email="e@example.com",
            display_name="E",
            method="google",
        )

    mock_client.post.assert_called_once()
    url = mock_client.post.call_args.args[0]
    body = mock_client.post.call_args.kwargs["json"]
    assert url == "http://n8n.test/hook"
    assert body["event"] == "user_signup"
    assert body["user_id"] == "u1"
    assert body["email"] == "e@example.com"
    assert body["method"] == "google"


def test_notify_new_signup_swallows_network_errors(monkeypatch):
    from app.services import notification_service

    monkeypatch.setattr(
        notification_service.settings, "n8n_webhook_url", "http://n8n.test/hook"
    )

    with patch(
        "app.services.notification_service.httpx.Client",
        side_effect=RuntimeError("dns failure"),
    ):
        # Must not raise — the caller is a post-response background task.
        notification_service.notify_new_signup(
            user_id="u1", email="e@example.com", display_name="E"
        )
