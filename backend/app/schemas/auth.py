from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str = Field(..., min_length=2, max_length=150)
    # Marketing attribution captured client-side (best-effort, optional).
    utm_source: str | None = Field(default=None, max_length=200)
    utm_medium: str | None = Field(default=None, max_length=200)
    utm_campaign: str | None = Field(default=None, max_length=200)

    @field_validator("utm_source", "utm_medium", "utm_campaign", mode="before")
    @classmethod
    def _strip_blank_utms(cls, value: object) -> object:
        """Empty/whitespace-only UTM values are treated as absent."""
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=8, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)


class AuthUser(BaseModel):
    id: UUID
    email: EmailStr
    display_name: str
    is_active: bool
    is_onboarded: bool
    subscription_tier: str = "free"
    customer_portal_url: str | None = None
    has_google_account: bool = False


class AuthSession(BaseModel):
    user: AuthUser
    csrf_token: str
