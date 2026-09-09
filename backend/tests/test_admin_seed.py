"""Tests for the admin seed endpoint and meal-plans trailing-slash fix.

Covers:
- GET /api/admin/seed-foods — seeds the prepared dish catalog (idempotent)
- GET /api/meal-plans (no trailing slash) — direct 200, no 307 redirect
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-1234567890abcdefg")
os.environ.setdefault("CSRF_SECRET_KEY", "test-csrf-secret-key-1234567890abcdef")
os.environ.setdefault("ENVIRONMENT", "testing")

from app import models as app_models  # noqa: F401
from app.db import session as db_session
from app.db.base import Base
from app.main import app
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
    return TestClient(app, follow_redirects=False)


def api_register(client: TestClient, email: str) -> dict:
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "StrongPass!123",
            "display_name": "Test User",
        },
    )
    assert response.status_code == 201, response.text
    client.get("/api/auth/csrf")
    return response.json()


def api_login(client: TestClient, email: str) -> dict:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "StrongPass!123"},
    )
    assert response.status_code == 200, response.text
    client.get("/api/auth/csrf")
    return response.json()


def setup_authenticated_client(email: str) -> TestClient:
    """Register, create fresh client, login. Returns authenticated client."""
    client = make_client()
    api_register(client, email)
    client = TestClient(app)
    api_login(client, email)
    return client


# ── GET /api/admin/seed-foods ─────────────────────────────────────────────


class TestSeedFoodsEndpoint:
    def test_seeds_dishes_on_first_call(self):
        client = make_client()
        resp = client.get("/api/admin/seed-foods")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "success"
        assert body["created"] > 0
        assert body["skipped"] == 0
        # Spot-check a few dishes landed in the DB
        from app.models.food import Food

        db = db_session.SessionLocal()
        try:
            for slug in ("chicken-biryani", "anda-paratha", "khichdi", "aloo-keema"):
                food = db.query(Food).filter(Food.slug == slug).first()
                assert food is not None, f"expected {slug} to be seeded"
                assert food.verification_status is not None
        finally:
            db.close()

    def test_idempotent_second_call_skips_existing(self):
        client = make_client()
        first = client.get("/api/admin/seed-foods")
        assert first.status_code == 200
        assert first.json()["created"] > 0

        second = client.get("/api/admin/seed-foods")
        assert second.status_code == 200
        body = second.json()
        assert body["status"] == "success"
        assert body["created"] == 0
        assert body["skipped"] == first.json()["created"]

    def test_self_sufficient_on_empty_db(self):
        """Endpoint works on a completely empty database (creates its own
        category and unit), which is exactly the Render free-tier scenario."""
        client = make_client()
        resp = client.get("/api/admin/seed-foods")
        assert resp.status_code == 200, resp.text
        assert resp.json()["created"] >= 25


# ── GET /api/meal-plans trailing slash ────────────────────────────────────


class TestMealPlansTrailingSlash:
    def test_no_trailing_slash_direct_200(self):
        """/api/meal-plans (no slash) must return 200 directly — no 307."""
        client = setup_authenticated_client("slash@test.com")
        resp = client.get("/api/meal-plans?limit=20")
        assert resp.status_code == 200, resp.text
        assert resp.history == [], "expected no redirect hop"
        assert resp.json()["total"] == 0

    def test_with_trailing_slash_still_works(self):
        client = setup_authenticated_client("slash2@test.com")
        resp = client.get("/api/meal-plans/?limit=20")
        assert resp.status_code == 200, resp.text
        assert resp.history == [], "expected no redirect hop"
