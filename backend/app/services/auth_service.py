from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.core.rate_limit import login_rate_limiter
from app.core.security import (
    generate_token,
    hash_password,
    hash_token,
    normalize_email,
    password_version,
    validate_password,
    verify_password,
)
from app.models.currency import Currency
from app.models.enums import DietaryTagKind, DietPattern
from app.models.geography import Country, Region
from app.models.tags import DietaryTag
from app.models.user import User, UserPreferences, UserProfile, UserSession

logger = get_logger(__name__)


def _user_response(user: User) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "display_name": user.display_name,
        "is_onboarded": user.is_onboarded,
    }


def ensure_dietary_tag(db: Session, slug: str, name: str, kind: DietaryTagKind) -> DietaryTag:
    normalized_slug = slug.strip().lower().replace(" ", "-")
    tag = db.query(DietaryTag).filter(DietaryTag.slug == normalized_slug).first()
    if tag is None:
        tag = DietaryTag(slug=normalized_slug, name=name or normalized_slug.replace("-", " ").title(), kind=kind)
        db.add(tag)
        db.flush()
    return tag


def register_user(db: Session, email: str, password: str, display_name: str) -> User:
    normalized_email = normalize_email(email)
    existing = db.query(User).filter(User.email == normalized_email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account already exists.")

    try:
        validate_password(password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    user = User(
        email=normalized_email,
        display_name=display_name.strip(),
        password_hash=hash_password(password),
        preferred_language="en",
        preferred_unit_system=None,
        preferred_currency_code=None,
        country_id=None,
        password_changed_at=datetime.now(UTC),
        is_onboarded=False,
        is_active=True,
    )
    db.add(user)
    db.flush()
    logger.info("Registered new account for user %s", user.id)
    return user


def create_session_for_user(db: Session, user: User, request: Request) -> str:
    token = generate_token()
    token_hash = hash_token(token)
    expires_at = datetime.now(UTC) + timedelta(seconds=settings.session_lifetime_seconds)
    session = UserSession(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
        password_version=password_version(user.password_changed_at),
    )
    db.add(session)
    db.flush()
    return token


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
        httponly=True,
        secure=settings.is_production or settings.secure_cookies,
        samesite="lax",
    )
    response.delete_cookie(
        key=settings.csrf_cookie_name,
        path="/",
        httponly=False,
        secure=settings.is_production or settings.secure_cookies,
        samesite="lax",
    )


def login_user(db: Session, email: str, password: str, request: Request) -> tuple[User, str]:
    normalized_email = normalize_email(email)
    rate_key = f"login:{normalized_email}:{request.client.host if request.client else 'unknown'}"
    if not login_rate_limiter.allow(rate_key):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many login attempts. Please try again later.")

    user = db.query(User).filter(User.email == normalized_email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

    if user.locked_until and user.locked_until > datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account temporarily locked.")

    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.login_max_attempts:
            user.locked_until = datetime.now(UTC) + timedelta(minutes=settings.login_lockout_minutes)
            logger.warning("User account locked for email %s due to repeated failed logins", normalized_email)
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = datetime.now(UTC)
    db.flush()
    token = create_session_for_user(db, user, request)
    db.commit()
    logger.info("Successful login for user %s", user.id)
    return user, token


def logout_user(db: Session, request: Request, response: Response) -> None:
    token = request.cookies.get(settings.session_cookie_name)
    if token:
        session = db.query(UserSession).filter(UserSession.token_hash == hash_token(token)).first()
        if session is not None:
            session.revoked_at = datetime.now(UTC)
            db.commit()
    clear_session_cookie(response)
    logger.info("User logged out")


def change_password(db: Session, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is invalid.")

    try:
        validate_password(new_password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if verify_password(new_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password must differ from the current password.")

    user.password_hash = hash_password(new_password)
    user.password_changed_at = datetime.now(UTC)
    user.failed_login_attempts = 0
    user.locked_until = None
    for session in user.sessions:
        session.revoked_at = datetime.now(UTC)
    db.commit()
    logger.info("Password changed for user %s", user.id)


def submit_onboarding(db: Session, user: User, payload: dict) -> User:
    country_id = payload.get("country_id")
    region_id = payload.get("region_id")
    country = db.query(Country).filter(Country.id == country_id).first() if country_id else None
    if country is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Country is required.")

    region = None
    if region_id:
        region = db.query(Region).filter(Region.id == region_id, Region.country_id == country.id).first()
        if region is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selected region is invalid for the chosen country.")

    currency = db.query(Currency).filter(Currency.code == payload.get("preferred_currency_code", "").upper()).first()
    if currency is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Preferred currency is invalid.")

    if not payload.get("preferred_language"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Preferred language is required.")

    user.country_id = country.id
    user.region_id = region.id if region else None
    user.preferred_currency_code = currency.code
    user.preferred_language = payload["preferred_language"][:16]
    user.preferred_unit_system = payload["unit_system"]
    user.is_onboarded = True

    profile = user.profile or UserProfile(user_id=user.id)
    profile.age_years = payload["age_years"]
    profile.sex = payload["sex"]
    profile.height_cm = payload["height_cm"]
    profile.weight_kg = payload["weight_kg"]
    profile.activity_level = payload["activity_level"]
    profile.fitness_goal = payload["fitness_goal"]
    profile.diet_pattern = payload.get("diet_pattern", DietPattern.OMNIVORE)
    profile.dietary_tags = []
    db.add(profile)
    db.flush()

    dietary_tag_slugs = list(payload.get("dietary_tag_slugs", [])) + list(payload.get("allergen_tag_slugs", []))
    for slug in dietary_tag_slugs:
        if not slug:
            continue
        tag_kind = DietaryTagKind.ALLERGEN if slug in payload.get("allergen_tag_slugs", []) else DietaryTagKind.DIET_PATTERN
        tag = ensure_dietary_tag(db, slug, slug, tag_kind)
        profile.dietary_tags.append(tag)

    prefs = user.preferences or UserPreferences(user_id=user.id)
    prefs.weekly_budget_amount = payload.get("weekly_budget_amount")
    prefs.budget_currency_code = currency.code
    prefs.notes = json.dumps(
        {
            "food_dislikes": payload.get("food_dislikes", []),
            "preferred_foods": payload.get("preferred_foods", []),
            "budget_period": payload.get("budget_period", "weekly"),
        },
        ensure_ascii=False,
    )
    prefs.dietary_tags = []
    prefs.cuisine_tags = []
    prefs.preferred_regions = []
    if region:
        prefs.preferred_regions.append(region)

    db.add(user)
    db.add(profile)
    db.add(prefs)
    db.flush()
    logger.info("Onboarding completed for user %s", user.id)
    return user
