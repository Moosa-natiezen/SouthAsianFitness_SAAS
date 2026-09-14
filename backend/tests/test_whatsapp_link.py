"""Tests for the authenticated WhatsApp phone-link routes.

Covers:
- GET returns the current link status (linked + unlinked)
- PATCH links a valid number (formats like +92 300 1234567 normalize to wa_id)
- PATCH rejects non-E.164 input (letters, too short/too long) with 422
- PATCH rejects numbers already bound to a different account (409)
- PATCH re-linking the same account's own number is a no-op success
- PATCH with null/empty unlinks (clears users.whatsapp_phone, deactivates link)
- Route requires authentication (401 without a session)
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-1234567890abcdefg")
os.environ.setdefault("CSRF_SECRET_KEY", "test-csrf-secret-key-1234567890abcdef")
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("DEBUG", "false")

from app import models as app_models  # noqa: F401
from app.core.config import settings
from app.db import session as db_session
from app.db.base import Base
from app.main import app
from app.models.user import User
from app.models.whatsapp import WhatsAppLink
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

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


def make_user(db: Session, email: str = "link@example.com", phone: str | None = None) -> User:
    user = User(
        email=email,
        display_name="Link User",
        password_hash="fakehash",
        whatsapp_phone=phone,
    )
    db.add(user)
    db.commit()
    return user


def auth_headers(db: Session, user: User) -> dict[str, str]:
    """Create a real session row and return session + CSRF headers."""
    from datetime import UTC, datetime, timedelta

    from app.core.security import generate_token, hash_token, password_version

    token = generate_token()
    from app.models.user import UserSession

    db.add(
        UserSession(
            user_id=user.id,
            token_hash=hash_token(token),
            expires_at=datetime.now(UTC)
            + timedelta(seconds=settings.session_lifetime_seconds),
            password_version=password_version(user.password_changed_at),
        )
    )
    db.commit()
    return {
        "Cookie": f"{settings.session_cookie_name}={token}; {settings.csrf_cookie_name}=csrf",
        "X-CSRF-Token": "csrf",
    }


def make_client() -> TestClient:
    reset_db()
    return TestClient(app)


# ── GET status ───────────────────────────────────────────────────────────────


def test_get_returns_unlinked_when_no_phone():
    client = make_client()
    db = db_session.SessionLocal()
    user = make_user(db)
    response = client.get("/api/users/me/whatsapp", headers=auth_headers(db, user))
    assert response.status_code == 200
    assert response.json() == {"linked": False, "whatsapp_phone": None}


def test_get_returns_linked_phone():
    client = make_client()
    db = db_session.SessionLocal()
    user = make_user(db, phone="923001234567")
    response = client.get("/api/users/me/whatsapp", headers=auth_headers(db, user))
    assert response.status_code == 200
    assert response.json() == {"linked": True, "whatsapp_phone": "923001234567"}


# ── PATCH linking ────────────────────────────────────────────────────────────


def test_patch_links_formatted_number():
    client = make_client()
    db = db_session.SessionLocal()
    user = make_user(db)

    response = client.patch(
        "/api/users/me/whatsapp",
        json={"whatsapp_phone": "+92 300 1234567"},
        headers=auth_headers(db, user),
    )
    assert response.status_code == 200
    body = response.json()
    assert body == {"status": "ok", "linked": True, "whatsapp_phone": "923001234567"}

    db.expire_all()
    assert user.whatsapp_phone == "923001234567"
    link = db.query(WhatsAppLink).filter(WhatsAppLink.user_id == user.id).one()
    assert link.phone_e164 == "923001234567"
    assert link.is_active is True


def test_patch_rejects_non_numeric_phone():
    client = make_client()
    db = db_session.SessionLocal()
    user = make_user(db)

    response = client.patch(
        "/api/users/me/whatsapp",
        json={"whatsapp_phone": "not-a-phone"},
        headers=auth_headers(db, user),
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "INVALID_PHONE"
    db.expire_all()
    assert user.whatsapp_phone is None


def test_patch_rejects_too_short_number():
    client = make_client()
    db = db_session.SessionLocal()
    user = make_user(db)

    response = client.patch(
        "/api/users/me/whatsapp",
        json={"whatsapp_phone": "12345"},
        headers=auth_headers(db, user),
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "INVALID_PHONE"


def test_patch_rejects_too_long_number():
    client = make_client()
    db = db_session.SessionLocal()
    user = make_user(db)

    response = client.patch(
        "/api/users/me/whatsapp",
        json={"whatsapp_phone": "12345678901234567890"},  # 20 digits > E.164 max 15
        headers=auth_headers(db, user),
    )
    assert response.status_code == 422


def test_patch_rejects_number_linked_to_another_account():
    client = make_client()
    db = db_session.SessionLocal()
    other = make_user(db, email="other@example.com", phone="923007654321")
    db.add(WhatsAppLink(phone_e164="923007654321", user_id=other.id))
    db.commit()

    user = make_user(db, email="me@example.com")
    response = client.patch(
        "/api/users/me/whatsapp",
        json={"whatsapp_phone": "+92 300 765 4321"},
        headers=auth_headers(db, user),
    )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "PHONE_ALREADY_LINKED"
    db.expire_all()
    assert user.whatsapp_phone is None


def test_patch_same_number_again_is_noop_success():
    client = make_client()
    db = db_session.SessionLocal()
    user = make_user(db, phone="923001234567")
    db.add(WhatsAppLink(phone_e164="923001234567", user_id=user.id))
    db.commit()

    response = client.patch(
        "/api/users/me/whatsapp",
        json={"whatsapp_phone": "923001234567"},
        headers=auth_headers(db, user),
    )
    assert response.status_code == 200
    assert response.json()["linked"] is True
    assert db.query(WhatsAppLink).count() == 1


def test_patch_null_unlinks():
    client = make_client()
    db = db_session.SessionLocal()
    user = make_user(db, phone="923001234567")
    db.add(WhatsAppLink(phone_e164="923001234567", user_id=user.id))
    db.commit()

    response = client.patch(
        "/api/users/me/whatsapp",
        json={"whatsapp_phone": None},
        headers=auth_headers(db, user),
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "linked": False, "whatsapp_phone": None}

    db.expire_all()
    assert user.whatsapp_phone is None
    link = db.query(WhatsAppLink).one()
    assert link.is_active is False


def test_patch_empty_string_unlinks():
    client = make_client()
    db = db_session.SessionLocal()
    user = make_user(db, phone="923001234567")
    db.commit()

    response = client.patch(
        "/api/users/me/whatsapp",
        json={"whatsapp_phone": "   "},
        headers=auth_headers(db, user),
    )
    assert response.status_code == 200
    assert response.json()["linked"] is False
    db.expire_all()
    assert user.whatsapp_phone is None


# ── Auth required ────────────────────────────────────────────────────────────


def test_get_requires_auth():
    client = make_client()
    response = client.get("/api/users/me/whatsapp")
    assert response.status_code == 401


def test_patch_requires_auth():
    client = make_client()
    response = client.patch("/api/users/me/whatsapp", json={"whatsapp_phone": "923001234567"})
    assert response.status_code == 401
