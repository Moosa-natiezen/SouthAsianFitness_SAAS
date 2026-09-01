from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import constant_time_equals, hash_token, password_version
from app.db.session import get_db
from app.models.user import User, UserSession

logger = get_logger(__name__)
security = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> User:
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )

    session = (
        db.query(UserSession)
        .filter(UserSession.token_hash == hash_token(token))
        .filter(UserSession.revoked_at.is_(None))
        .filter(UserSession.expires_at > datetime.now(UTC))
        .first()
    )

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )

    user = db.query(User).filter(User.id == session.user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )

    if session.password_version != password_version(user.password_changed_at):
        session.revoked_at = datetime.now(UTC)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )

    if user.locked_until and user.locked_until > datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account temporarily locked"
        )

    return user


def require_auth(user: Annotated[User, Depends(get_current_user)]) -> User:
    return user


def require_pro(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Require the authenticated user to have an active Pro subscription."""
    if (user.subscription_tier or "").lower() != "pro":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "PRO_REQUIRED",
                "message": "This feature requires an active Pro subscription.",
            },
        )
    return user


def require_csrf(
    request: Request,
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    if request.method.upper() in {"POST", "PUT", "PATCH", "DELETE"}:
        expected = request.cookies.get(settings.csrf_cookie_name)
        header_value = request.headers.get("X-CSRF-Token")
        if not expected or not header_value or not constant_time_equals(expected, header_value):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="CSRF validation failed"
            )
    return user


def get_auth_bearer(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> str | None:
    if credentials is None:
        return None
    return credentials.credentials
