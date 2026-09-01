"""Tests for saving AI-generated meal plans.

Covers:
- POST /api/ai/meal-plans/save — save an AI plan
- GET /api/ai/meal-plans/saved — list saved plans
- Authentication enforcement
- User isolation
- Pagination
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-1234567890abcdefg")
os.environ.setdefault("CSRF_SECRET_KEY", "test-csrf-secret-key-1234567890abcdef")
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-fake-key")
os.environ.setdefault("LEMON_SQUEEZY_API_KEY", "ls_test")
os.environ.setdefault("LEMON_SQUEEZY_WEBHOOK_SECRET", "ls_test_secret")
os.environ.setdefault("LEMON_SQUEEZY_STORE_ID", "1")
os.environ.setdefault("LEMON_SQUEEZY_VARIANT_ID", "1")
os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")

from app import models as app_models  # noqa: F401
from app.db import session as db_session
from app.db.base import Base
from app.main import app
from app.models.meal_plan import SavedMealPlan
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


def api_register(client: TestClient, email: str = "save_test@example.com") -> dict:
    resp = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "StrongPass!123",
            "display_name": "Save Test User",
        },
    )
    assert resp.status_code == 201, resp.text
    client.get("/api/auth/csrf")
    return resp.json()


def api_login(client: TestClient, email: str = "save_test@example.com") -> dict:
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


def setup_authenticated_client(email: str = "save_test@example.com") -> TestClient:
    client = make_client()
    api_register(client, email)
    client = TestClient(app)
    api_login(client, email)
    return client


# ── Save tests ────────────────────────────────────────────────────────────


def test_save_ai_meal_plan_success():
    """Verify POST /api/ai/meal-plans/save persists a plan."""
    client = setup_authenticated_client()

    resp = client.post(
        "/api/ai/meal-plans/save",
        json={
            "title": "High-Protein South Asian Plan",
            "content": "# Meal Plan\n\n## Breakfast\n- 2 eggs\n- Roti",
            "target_calories": 2200,
            "protein_g": 120,
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "success"
    assert "id" in data

    # Verify it's in the database
    from uuid import UUID
    db = db_session.SessionLocal()
    plan_uuid = UUID(data["id"])
    saved = db.query(SavedMealPlan).filter(SavedMealPlan.id == plan_uuid).first()
    assert saved is not None
    assert saved.title == "High-Protein South Asian Plan"
    assert saved.target_calories == 2200
    assert saved.protein_g == 120
    db.close()


def test_save_ai_meal_plan_unauthenticated():
    """Verify unauthenticated save is rejected."""
    client = make_client()
    resp = client.post(
        "/api/ai/meal-plans/save",
        json={"title": "Test", "content": "content"},
    )
    assert resp.status_code == 401


def test_save_ai_meal_plan_missing_title():
    """Verify save rejects empty title."""
    client = setup_authenticated_client()
    resp = client.post(
        "/api/ai/meal-plans/save",
        json={"title": "", "content": "content"},
    )
    assert resp.status_code == 422


def test_save_ai_meal_plan_missing_content():
    """Verify save rejects empty content."""
    client = setup_authenticated_client()
    resp = client.post(
        "/api/ai/meal-plans/save",
        json={"title": "Test", "content": ""},
    )
    assert resp.status_code == 422


def test_save_ai_meal_plan_optional_fields():
    """Verify save works with only required fields (no calories/protein)."""
    client = setup_authenticated_client()

    resp = client.post(
        "/api/ai/meal-plans/save",
        json={"title": "Simple Plan", "content": "# Plan\n\nJust rice and dal."},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"


# ── List tests ────────────────────────────────────────────────────────────


def test_list_saved_plans_returns_user_plans():
    """Verify GET /api/ai/meal-plans/saved returns the user's plans."""
    client = setup_authenticated_client()

    # Save 3 plans
    for i in range(3):
        resp = client.post(
            "/api/ai/meal-plans/save",
            json={"title": f"Plan {i}", "content": f"Content {i}"},
        )
        assert resp.status_code == 200

    resp = client.get("/api/ai/meal-plans/saved")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3
    # Newest first
    assert data["items"][0]["title"] == "Plan 2"


def test_list_saved_plans_pagination():
    """Verify pagination works."""
    client = setup_authenticated_client()

    for i in range(5):
        client.post(
            "/api/ai/meal-plans/save",
            json={"title": f"Plan {i}", "content": f"Content {i}"},
        )

    resp = client.get("/api/ai/meal-plans/saved?limit=2&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2

    resp = client.get("/api/ai/meal-plans/saved?limit=2&offset=2")
    data = resp.json()
    assert len(data["items"]) == 2


def test_list_saved_plans_unauthenticated():
    """Verify unauthenticated list is rejected."""
    client = make_client()
    resp = client.get("/api/ai/meal-plans/saved")
    assert resp.status_code == 401


def test_list_saved_plans_user_isolation():
    """Verify user cannot see another user's saved plans."""
    client = make_client()
    api_register(client, "user_a@example.com")
    api_register(client, "user_b@example.com")
    client1 = TestClient(app)
    api_login(client1, "user_a@example.com")
    client2 = TestClient(app)
    api_login(client2, "user_b@example.com")

    # User A saves a plan
    client1.post(
        "/api/ai/meal-plans/save",
        json={"title": "A's Plan", "content": "A content"},
    )

    # User A sees 1 plan
    resp = client1.get("/api/ai/meal-plans/saved")
    assert resp.json()["total"] == 1

    # User B sees 0 plans
    resp = client2.get("/api/ai/meal-plans/saved")
    assert resp.json()["total"] == 0
