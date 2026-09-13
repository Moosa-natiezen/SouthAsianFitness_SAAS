"""Tests for AI generation abuse prevention (user-level + IP-level limits).

Verifies the two-layer fraud-prevention architecture on the generation
endpoints:
- User-level: free tier capped at 3 meal plans per calendar month →
  402 Payment Required (upsell signal), Pro users unlimited.
- IP-level: max 10 generations per 24h per client IP regardless of account →
  429 with "Suspicious activity detected" (blocks account rotation).
- Failed generations never consume IP quota (peek-then-allow contract).
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-1234567890abcdefg")
os.environ.setdefault("CSRF_SECRET_KEY", "test-csrf-secret-key-1234567890abcdef")
os.environ.setdefault("ENVIRONMENT", "testing")

from decimal import Decimal

from app import models as app_models  # noqa: F401
from app.core.config import settings
from app.core.rate_limit import generation_ip_limiter, login_rate_limiter
from app.db import session as db_session
from app.db.base import Base
from app.main import app
from app.models.enums import FitnessGoal, MealPlanStatus
from app.models.meal_plan import MealPlan
from app.models.user import User
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

TEST_IP = "testclient"  # TestClient's request.client.host


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
    login_rate_limiter.clear()
    generation_ip_limiter.clear()
    return TestClient(app)


def api_register(client: TestClient, email: str) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "StrongPass!123",
            "display_name": "Test User",
        },
    )
    assert response.status_code == 201, response.text


def api_login(client: TestClient, email: str) -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "StrongPass!123"},
    )
    assert response.status_code == 200, response.text


def get_csrf(client: TestClient) -> str:
    return client.get("/api/auth/csrf").json()["csrf_token"]


def authenticated_client(email: str) -> TestClient:
    client = make_client()
    api_register(client, email)
    client = TestClient(app)
    api_login(client, email)
    return client


def set_tier(email: str, tier: str) -> None:
    db = db_session.SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        user.subscription_tier = tier
        db.commit()
    finally:
        db.close()


def seed_plans(user_email: str, count: int) -> None:
    """Create `count` meal plans for the user dated this month."""
    from datetime import UTC, datetime

    db = db_session.SessionLocal()
    try:
        user = db.query(User).filter(User.email == user_email).first()
        today = datetime.now(tz=UTC).date()
        for i in range(count):
            db.add(
                MealPlan(
                    user_id=user.id,
                    name=f"Plan {i}",
                    goal=FitnessGoal.GENERAL_FITNESS,
                    daily_calorie_target=Decimal("2000.00"),
                    daily_protein_g=Decimal("100.000"),
                    daily_carbs_g=Decimal("250.000"),
                    daily_fat_g=Decimal("65.000"),
                    start_date=today,
                    end_date=today,
                    status=MealPlanStatus.DRAFT,
                )
            )
        db.commit()
    finally:
        db.close()


def post_generate(client: TestClient) -> object:
    return client.post(
        "/api/meal-plans/generate",
        json={"plan_days": 1, "meal_count": 4},
        headers={"X-CSRF-Token": get_csrf(client)},
    )


# ── User-level limit: 402 upsell ─────────────────────────────────────────────


class TestUserLevelLimit:
    def test_free_user_at_limit_returns_402(self):
        """4th generation attempt for a free user returns 402 (not 403)."""
        email = "limit402@example.com"
        client = authenticated_client(email)
        seed_plans(email, 3)

        resp = post_generate(client)
        assert resp.status_code == 402, resp.text
        assert "Free trial limit reached" in resp.json()["detail"]
        assert "upgrade to Pro" in resp.json()["detail"]

    def test_free_user_below_limit_passes_user_check(self):
        """With 2 plans this month, the request must NOT be rejected with 402.

        The user has no onboarding profile, so generation itself fails with a
        structured failure response (200) — but the 402 quota check passes.
        """
        email = "belowlimit@example.com"
        client = authenticated_client(email)
        seed_plans(email, 2)

        resp = post_generate(client)
        assert resp.status_code == 200, resp.text
        assert resp.json().get("success") is False  # failed on missing profile, not quota

    def test_pro_user_bypasses_user_limit(self):
        """Pro users can generate regardless of existing plan count."""
        email = "pro402@example.com"
        client = authenticated_client(email)
        seed_plans(email, 10)
        set_tier(email, "pro")

        resp = post_generate(client)
        # No 402: the pro user passes the quota check (generation may still
        # fail on missing profile → structured 200 failure).
        assert resp.status_code == 200, resp.text
        assert resp.json().get("success") is False

    def test_402_raises_before_any_generation(self):
        """The 402 must fire before the optimizer runs (no side effects)."""
        email = "early402@example.com"
        client = authenticated_client(email)
        seed_plans(email, 3)

        resp = post_generate(client)
        assert resp.status_code == 402

        # No new plans were created by the rejected request
        db = db_session.SessionLocal()
        try:
            assert db.query(MealPlan).count() == 3
        finally:
            db.close()


# ── IP-level limit: 429 risk block ───────────────────────────────────────────


class TestIpLevelLimit:
    def test_ip_at_limit_returns_429_with_suspicious_message(self):
        """An IP with 10 generations in 24h gets 429 'Suspicious activity'."""
        client = authenticated_client("ip429@example.com")
        for _ in range(10):
            generation_ip_limiter.allow(TEST_IP)

        resp = post_generate(client)
        assert resp.status_code == 429, resp.text
        assert "Suspicious activity detected" in resp.json()["detail"]

    def test_ip_limit_is_account_independent(self):
        """New accounts from a capped IP stay blocked — rotation is useless."""
        email_a = "rotator_a@example.com"
        client = authenticated_client(email_a)
        for _ in range(10):
            generation_ip_limiter.allow(TEST_IP)

        # First account is blocked
        resp_a = post_generate(client)
        assert resp_a.status_code == 429

        # A brand-new account from the same IP is blocked too.
        # NOTE: reset_db() only, NOT make_client() — make_client clears the
        # generation limiter, which would defeat the point of this test.
        reset_db()
        client_b = TestClient(app)
        api_register(client_b, "rotator_b@example.com")
        client_b = TestClient(app)
        api_login(client_b, "rotator_b@example.com")
        resp_b = post_generate(client_b)
        assert resp_b.status_code == 429, resp_b.text

    def test_ip_below_limit_passes_ip_check(self):
        """With fewer than 10 generations, the IP check does not block.

        The user has no profile, so generation returns a structured failure
        (200) — proving the 429 path was not taken.
        """
        client = authenticated_client("ipok@example.com")
        for _ in range(9):
            generation_ip_limiter.allow(TEST_IP)

        resp = post_generate(client)
        assert resp.status_code == 200, resp.text

    def test_pro_users_are_still_ip_capped(self):
        """The IP limit applies regardless of subscription tier."""
        email = "pro_ip@example.com"
        client = authenticated_client(email)
        set_tier(email, "pro")
        for _ in range(10):
            generation_ip_limiter.allow(TEST_IP)

        resp = post_generate(client)
        assert resp.status_code == 429, resp.text


# ── peek/allow contract: failures are free ───────────────────────────────────


class TestFailedGenerationsDontConsumeQuota:
    def test_failed_generations_never_consume_ip_quota(self):
        """11 failed generations (no profile → optimizer error) must never
        trigger the 429 — quota is only consumed on successful generation.
        This is the peek-then-allow contract: honest users whose generation
        fails should be able to retry without burning their daily quota.
        """
        client = authenticated_client("failfree@example.com")

        for attempt in range(11):
            resp = post_generate(client)
            assert resp.status_code == 200, (
                f"attempt {attempt}: {resp.status_code} {resp.text}"
            )
            assert resp.json().get("success") is False
