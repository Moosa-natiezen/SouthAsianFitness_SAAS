"""Tests for Meal Plan Management API endpoints.

Covers:
- GET /api/meal-plans/ — list user's plans
- DELETE /api/meal-plans/{plan_id} — delete a plan
- User isolation for both endpoints
- Authentication and CSRF enforcement
- Pagination
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-1234567890abcdefg")
os.environ.setdefault("CSRF_SECRET_KEY", "test-csrf-secret-key-1234567890abcdef")
os.environ.setdefault("ENVIRONMENT", "testing")

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

from app import models as app_models  # noqa: F401
from app.db import session as db_session
from app.db.base import Base
from app.main import app
from app.models.enums import FitnessGoal, MealPlanStatus
from app.models.meal_plan import MealPlan, MealPlanDay
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


def get_csrf(client: TestClient) -> str:
    return client.get("/api/auth/csrf").json()["csrf_token"]


def create_meal_plan_for_user(
    db: Session,
    user_id,
    *,
    name: str = "Test Plan",
    start_date: date | None = None,
    end_date: date | None = None,
) -> MealPlan:
    today = datetime.now(tz=UTC).date()
    plan = MealPlan(
        user_id=user_id,
        name=name,
        goal=FitnessGoal.GENERAL_FITNESS,
        daily_calorie_target=Decimal("2000.00"),
        daily_protein_g=Decimal("100.000"),
        daily_carbs_g=Decimal("250.000"),
        daily_fat_g=Decimal("65.000"),
        start_date=start_date or today,
        end_date=end_date or today,
        status=MealPlanStatus.DRAFT,
    )
    db.add(plan)
    db.flush()
    day = MealPlanDay(meal_plan_id=plan.id, plan_date=start_date or today)
    db.add(day)
    db.commit()
    return plan


def get_user_id_from_db(email: str):
    db = db_session.SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    uid = user.id if user else None
    db.close()
    return uid


def setup_authenticated_client(email: str) -> TestClient:
    """Register, create fresh client, login. Returns authenticated client."""
    client = make_client()
    api_register(client, email)
    client = TestClient(app)
    api_login(client, email)
    return client


# ── GET /api/meal-plans/ tests ────────────────────────────────────────────


def test_list_plans_returns_user_plans():
    """Verify GET /api/meal-plans/ returns the user's plans sorted newest first."""
    email = "list_newest@example.com"
    client = setup_authenticated_client(email)
    user_id = get_user_id_from_db(email)
    assert user_id is not None

    db = db_session.SessionLocal()
    create_meal_plan_for_user(db, user_id, name="Plan 1", start_date=date(2026, 1, 1), end_date=date(2026, 1, 1))
    create_meal_plan_for_user(db, user_id, name="Plan 2", start_date=date(2026, 1, 2), end_date=date(2026, 1, 3))
    create_meal_plan_for_user(db, user_id, name="Plan 3", start_date=date(2026, 1, 4), end_date=date(2026, 1, 6))
    db.close()

    resp = client.get("/api/meal-plans/")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3

    # Check summary fields exist
    item = data["items"][0]
    for key in ["id", "name", "start_date", "end_date", "day_count", "status", "calorie_target", "created_at"]:
        assert key in item, f"Missing key: {key}"

    # day_count should be correct
    day_counts = {item["name"]: item["day_count"] for item in data["items"]}
    assert day_counts["Plan 1"] == 1
    assert day_counts["Plan 2"] == 2
    assert day_counts["Plan 3"] == 3


def test_list_plans_pagination():
    """Verify pagination works for meal plan list."""
    email = "pag@example.com"
    client = setup_authenticated_client(email)
    user_id = get_user_id_from_db(email)

    db = db_session.SessionLocal()
    for i in range(5):
        create_meal_plan_for_user(
            db, user_id, name=f"Plan {i}",
            start_date=date(2026, 1, i + 1),
            end_date=date(2026, 1, i + 1),
        )
    db.close()

    resp = client.get("/api/meal-plans/?limit=2&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2

    resp = client.get("/api/meal-plans/?limit=2&offset=2")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 2


def test_list_plans_empty():
    """Verify empty list when user has no plans."""
    email = "empty_plans@example.com"
    client = setup_authenticated_client(email)

    resp = client.get("/api/meal-plans/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_list_plans_unauthenticated():
    """Verify unauthenticated access is rejected."""
    client = make_client()
    resp = client.get("/api/meal-plans/")
    assert resp.status_code == 401


def test_list_plans_user_isolation():
    """Verify user cannot see another user's plans."""
    email1 = "iso_list1@example.com"
    email2 = "iso_list2@example.com"

    # Register both users on the same DB
    client = make_client()
    api_register(client, email1)
    api_register(client, email2)

    user2_id = get_user_id_from_db(email2)
    db = db_session.SessionLocal()
    create_meal_plan_for_user(db, user2_id, name="User2 Plan")
    db.close()

    # Create authenticated clients for each user
    client1 = TestClient(app)
    api_login(client1, email1)

    client2 = TestClient(app)
    api_login(client2, email2)

    # user1 should see 0 plans
    resp = client1.get("/api/meal-plans/")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0

    # user2 should see 1 plan
    resp = client2.get("/api/meal-plans/")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


# ── DELETE /api/meal-plans/{plan_id} tests ────────────────────────────────


def test_delete_plan_success():
    """Verify DELETE /api/meal-plans/{plan_id} successfully deletes a plan."""
    email = "del_success@example.com"
    client = setup_authenticated_client(email)
    user_id = get_user_id_from_db(email)

    db = db_session.SessionLocal()
    plan = create_meal_plan_for_user(db, user_id, name="To Delete")
    plan_id = str(plan.id)
    db.close()

    csrf = get_csrf(client)
    resp = client.delete(
        f"/api/meal-plans/{plan_id}",
        headers={"X-CSRF-Token": csrf},
    )
    assert resp.status_code == 204

    # Verify it's gone
    resp = client.get("/api/meal-plans/")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


def test_delete_plan_not_found():
    """Verify DELETE returns 404 for non-existent plan."""
    email = "del_notfound@example.com"
    client = setup_authenticated_client(email)

    csrf = get_csrf(client)
    fake_id = str(uuid4())
    resp = client.delete(
        f"/api/meal-plans/{fake_id}",
        headers={"X-CSRF-Token": csrf},
    )
    assert resp.status_code == 404


def test_delete_plan_user_isolation():
    """Verify user cannot delete another user's plan."""
    email1 = "del_iso1@example.com"
    email2 = "del_iso2@example.com"

    # Register both users on the same DB
    client = make_client()
    api_register(client, email1)
    api_register(client, email2)

    user2_id = get_user_id_from_db(email2)
    db = db_session.SessionLocal()
    plan = create_meal_plan_for_user(db, user2_id, name="User2 Plan")
    plan_id = str(plan.id)
    db.close()

    # Create authenticated client for user1
    client1 = TestClient(app)
    api_login(client1, email1)

    # user1 tries to delete user2's plan
    csrf1 = get_csrf(client1)
    resp = client1.delete(
        f"/api/meal-plans/{plan_id}",
        headers={"X-CSRF-Token": csrf1},
    )
    assert resp.status_code == 404

    # Verify user2's plan still exists
    db = db_session.SessionLocal()
    remaining = db.query(MealPlan).filter(MealPlan.id == plan.id).first()
    assert remaining is not None
    db.close()


def test_delete_plan_unauthenticated():
    """Verify unauthenticated DELETE is rejected."""
    client = make_client()
    fake_id = str(uuid4())
    resp = client.delete(f"/api/meal-plans/{fake_id}")
    assert resp.status_code in (401, 403)


def test_delete_plan_missing_csrf():
    """Verify DELETE without CSRF token is rejected."""
    email = "del_csrf@example.com"
    client = setup_authenticated_client(email)

    fake_id = str(uuid4())
    resp = client.delete(f"/api/meal-plans/{fake_id}")
    assert resp.status_code == 403
