from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import require_auth, require_csrf
from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import generate_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    AuthSession,
    AuthUser,
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
)
from app.services.auth_service import (
    _user_response,
    change_password,
    create_session_for_user,
    google_login_or_register,
    login_user,
    logout_user,
    register_user,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/csrf")
def get_csrf_token(response: Response):
    token = generate_token()
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=token,
        httponly=False,
        secure=settings.is_production or settings.secure_cookies,
        samesite=settings.cookie_samesite,
        path="/",
    )
    return {"csrf_token": token}


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
):
    user = register_user(db, payload.email, payload.password, payload.display_name)
    token = create_session_for_user(db, user, request)
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,
        secure=settings.is_production or settings.secure_cookies,
        samesite=settings.cookie_samesite,
        max_age=settings.session_lifetime_seconds,
        path="/",
    )
    csrf_token = generate_token()
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=csrf_token,
        httponly=False,
        secure=settings.is_production or settings.secure_cookies,
        samesite=settings.cookie_samesite,
        path="/",
    )
    db.commit()
    return AuthSession(user=AuthUser(**_user_response(user)), csrf_token=csrf_token)


@router.post("/login")
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
):
    user, token = login_user(db, payload.email, payload.password, request)
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,
        secure=settings.is_production or settings.secure_cookies,
        samesite=settings.cookie_samesite,
        max_age=settings.session_lifetime_seconds,
        path="/",
    )
    csrf_token = generate_token()
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=csrf_token,
        httponly=False,
        secure=settings.is_production or settings.secure_cookies,
        samesite=settings.cookie_samesite,
        path="/",
    )
    return AuthSession(user=AuthUser(**_user_response(user)), csrf_token=csrf_token)


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    user: Annotated[User, Depends(require_csrf)],
    db: Annotated[Session, Depends(get_db)],
):
    logout_user(db, request, response)
    return {"status": "ok"}


@router.get("/me")
def get_current_user_data(user: Annotated[User, Depends(require_auth)]):
    from fastapi.responses import JSONResponse

    return JSONResponse(
        content=_user_response(user),
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
        },
    )


@router.post("/google")
def google_auth(
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
):
    """Authenticate or register a user via Google OAuth ID token."""
    import asyncio

    from pydantic import BaseModel

    class GoogleTokenRequest(BaseModel):
        id_token: str

    async def _get_body():
        body = await request.body()
        return body

    # We need to parse the request body manually since we're not using Depends
    import json as _json

    async def _parse_payload():
        body = await request.body()
        return _json.loads(body)

    loop = asyncio.get_event_loop()
    payload_data = loop.run_until_complete(_parse_payload())
    id_token_str = payload_data.get("id_token", "")

    if not id_token_str:
        from fastapi import HTTPException as HE
        raise HE(status_code=status.HTTP_400_BAD_REQUEST, detail="id_token is required.")

    user = google_login_or_register(db, id_token_str)
    token = create_session_for_user(db, user, request)

    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,
        secure=settings.is_production or settings.secure_cookies,
        samesite=settings.cookie_samesite,
        max_age=settings.session_lifetime_seconds,
        path="/",
    )
    csrf_token = generate_token()
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=csrf_token,
        httponly=False,
        secure=settings.is_production or settings.secure_cookies,
        samesite=settings.cookie_samesite,
        path="/",
    )
    db.commit()
    return AuthSession(user=AuthUser(**_user_response(user)), csrf_token=csrf_token)


@router.post("/change-password")
def change_password_route(
    payload: ChangePasswordRequest,
    user: Annotated[User, Depends(require_csrf)],
    db: Annotated[Session, Depends(get_db)],
):
    change_password(db, user, payload.current_password, payload.new_password)
    return {"status": "ok"}
