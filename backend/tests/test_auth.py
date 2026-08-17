from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-1234567890abcdefg")
os.environ.setdefault("CSRF_SECRET_KEY", "test-csrf-secret-key-1234567890abcdef")
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("DEBUG", "false")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app import models as app_models  # noqa: F401
from app.core.config import settings
from app.core.rate_limit import login_rate_limiter
from app.core.security import hash_password, verify_password
from app.db import session as db_session
from app.db.base import Base
from app.main import app
from app.models.currency import Currency
from app.models.enums import UnitSystem
from app.models.geography import Country


def reset_db() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db_session.engine = engine
    db_session.SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)
    settings.database_url = str(engine.url)


def make_client() -> TestClient:
    reset_db()
    login_rate_limiter.clear()
    return TestClient(app)


def seed_country_and_currency() -> str:
    db = db_session.SessionLocal()
    try:
        currency = db.query(Currency).filter(Currency.code == "PKR").first()
        if currency is None:
            currency = Currency(code="PKR", name="Pakistani Rupee", symbol="Rs", minor_units=2)
            db.add(currency)
            db.flush()

        country = db.query(Country).filter(Country.iso_code == "PK").first()
        if country is None:
            country = Country(
                name="Pakistan",
                iso_code="PK",
                currency_code="PKR",
                default_unit_system=UnitSystem.METRIC,
            )
            db.add(country)
            db.flush()
        country_id = str(country.id)
    finally:
        db.commit()
        db.close()
    return country_id


def register_user(client: TestClient, email: str = "user@example.com") -> tuple[TestClient, dict[str, str]]:
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "StrongPass!123",
            "display_name": "Test User",
        },
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    csrf_resp = client.get("/api/auth/csrf")
    assert csrf_resp.status_code == 200, csrf_resp.text
    return client, payload


def login_user(client: TestClient, email: str = "user@example.com") -> tuple[TestClient, dict[str, str]]:
    response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": "StrongPass!123",
        },
    )
    if response.status_code == 401:
        register_user(client, email)
        response = client.post(
            "/api/auth/login",
            json={
                "email": email,
                "password": "StrongPass!123",
            },
        )
    assert response.status_code == 200, response.text
    payload = response.json()
    csrf_resp = client.get("/api/auth/csrf")
    assert csrf_resp.status_code == 200, csrf_resp.text
    return client, payload


def test_successful_registration() -> None:
    client = make_client()
    client, payload = register_user(client)
    assert payload["user"]["email"] == "user@example.com"
    assert "saf_session" in client.cookies


def test_duplicate_registration_handling() -> None:
    client = make_client()
    register_user(client)
    response = client.post(
        "/api/auth/register",
        json={
            "email": "user@example.com",
            "password": "StrongPass!123",
            "display_name": "Another User",
        },
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Account already exists."


def test_successful_login() -> None:
    client = make_client()
    register_user(client)
    client = TestClient(app)
    response = client.post(
        "/api/auth/login",
        json={
            "email": "user@example.com",
            "password": "StrongPass!123",
        },
    )
    assert response.status_code == 200
    assert response.json()["user"]["email"] == "user@example.com"


def test_invalid_login() -> None:
    client = make_client()
    register_user(client)
    response = client.post(
        "/api/auth/login",
        json={
            "email": "user@example.com",
            "password": "WrongPass!123",
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_logout() -> None:
    client = make_client()
    client, _ = login_user(client)
    csrf = client.get("/api/auth/csrf").json()["csrf_token"]
    response = client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf})
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_protected_route_without_auth() -> None:
    client = make_client()
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_protected_route_with_valid_auth() -> None:
    client = make_client()
    client, _ = login_user(client)
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"


def test_password_hash_verification() -> None:
    password = "StrongPass!123"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPass!123", hashed) is False


def test_onboarding_submission() -> None:
    client = make_client()
    country_id = seed_country_and_currency()
    client, _ = login_user(client)
    csrf = client.get("/api/auth/csrf").json()["csrf_token"]
    response = client.post(
        "/api/auth/onboarding",
        json={
            "country_id": country_id,
            "region_id": None,
            "preferred_currency_code": "PKR",
            "preferred_language": "en",
            "unit_system": "metric",
            "age_years": 27,
            "sex": "male",
            "height_cm": 175,
            "weight_kg": 72,
            "activity_level": "moderately_active",
            "fitness_goal": "general_fitness",
            "dietary_tag_slugs": ["high-protein"],
            "allergen_tag_slugs": ["peanuts"],
            "food_dislikes": ["fried food"],
            "preferred_foods": ["roti", "dal"],
            "weekly_budget_amount": 2500,
            "budget_period": "weekly",
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert response.status_code == 200, response.text
    assert response.json()["is_onboarded"] is True


def test_invalid_onboarding_data() -> None:
    client = make_client()
    country_id = seed_country_and_currency()
    client, _ = login_user(client)
    csrf = client.get("/api/auth/csrf").json()["csrf_token"]
    response = client.post(
        "/api/auth/onboarding",
        json={
            "country_id": country_id,
            "preferred_currency_code": "PKR",
            "preferred_language": "en",
            "unit_system": "metric",
            "age_years": 0,
            "sex": "male",
            "height_cm": 175,
            "weight_kg": 72,
            "activity_level": "moderately_active",
            "fitness_goal": "general_fitness",
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert response.status_code == 422


def test_auth_cookie_behavior() -> None:
    client = make_client()
    client, _ = login_user(client)
    cookies = client.cookies
    assert "saf_session" in cookies
    assert cookies.get("saf_session")


def test_basic_rate_limit_behavior() -> None:
    login_rate_limiter.clear()
    client = make_client()
    for _ in range(11):
        response = client.post(
            "/api/auth/login",
            json={
                "email": "user@example.com",
                "password": "WrongPass!123",
            },
        )
    assert response.status_code == 429
    assert response.json()["detail"] == "Too many login attempts. Please try again later."
