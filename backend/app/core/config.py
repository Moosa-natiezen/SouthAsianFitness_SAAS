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

    @property
    def sqlalchemy_database_url(self) -> str:
        """Return the database URL with the correct psycopg v3 driver prefix.

        Neon and many providers issue plain ``postgresql://`` URLs.  SQLAlchemy
        interprets that as the psycopg2 dialect which this project does not
        install.  Normalise to ``postgresql+psycopg://`` so the psycopg v3 driver
        (specified in pyproject.toml) is always used.
        """
        url = self.database_url
        if url.startswith("postgresql://"):
            url = "postgresql+psycopg://" + url[len("postgresql://") :]
        return url
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

    # ── OpenAI ────────────────────────────────────────────────────────
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # ── Lemon Squeezy ─────────────────────────────────────────────────
    lemon_squeezy_api_key: str = ""
    lemon_squeezy_webhook_secret: str = ""
    lemon_squeezy_store_id: str = ""
    lemon_squeezy_variant_id: str = ""
    frontend_url: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def cookie_samesite(self) -> str:
        """SameSite attribute for authentication cookies.

        Production uses None (cross-site) because the Vercel frontend and
        Render backend live on different origins.  Development keeps Lax.
        """
        return "none" if self.is_production else "lax"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
