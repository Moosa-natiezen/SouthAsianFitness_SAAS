from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
ROOT_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(ROOT_DIR / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "South Asian Fitness API"
    environment: str = "development"
    debug: bool = True
    api_prefix: str = "/api"

    database_url: str = Field(
        ...,
        description="SQLAlchemy database URL, e.g. postgresql+psycopg://user:pass@host:5432/db",
    )
    secret_key: str = Field(
        ...,
        min_length=32,
        description="Secret key used for secure cookie and session signing",
    )
    csrf_secret_key: str = Field(
        ...,
        min_length=32,
        description="Secret key used for CSRF token generation",
    )
    session_cookie_name: str = "saf_session"
    csrf_cookie_name: str = "saf_csrf"
    session_lifetime_seconds: int = 60 * 60 * 24 * 7
    secure_cookies: bool = False
    csrf_cookie_samesite: str = "lax"
    login_max_attempts: int = 5
    login_lockout_minutes: int = 15
    login_rate_limit_window_seconds: int = 300
    login_rate_limit_max_requests: int = 10

    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
