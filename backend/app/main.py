import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastmcp import FastMCP
from sqlalchemy import func, select

from app.api.router import api_router
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.logging import get_logger, setup_logging
from app.core.request_limits import RequestSizeLimitMiddleware
from app.core.security_headers import SecurityHeadersMiddleware
from app.db.session import SessionLocal
from app.models.enums import VerificationStatus
from app.models.food import Food
from app.scripts.seed_reference_data import seed_all

# ── Sentry initialization ─────────────────────────────────────────────
sentry_dsn = os.getenv("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=settings.environment,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
        send_default_pii=False,
        _experiments={
            "record_http_request_bodies": False,
        },
    )
    logger_sentry = get_logger("sentry")
    logger_sentry.info("Sentry initialized for %s environment", settings.environment)

setup_logging(debug=settings.debug)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting %s (%s)", settings.app_name, settings.environment)

    # Seed reference data (idempotent — safe on every startup)
    try:
        db = SessionLocal()
        try:
            result = seed_all(db, commit=True)
            total_created = (
                result.currencies_created
                + result.countries_created
                + result.regions_created
            )
            if total_created > 0:
                logger.info(
                    "Seeded reference data: %d created (currencies=%d, countries=%d, regions=%d)",
                    total_created,
                    result.currencies_created,
                    result.countries_created,
                    result.regions_created,
                )
        finally:
            db.close()
    except Exception:
        logger.exception("Reference data seed failed; application will continue starting")

    # Seed food dataset (idempotent — skip if full dataset is present)
    EXPECTED_FOOD_COUNT = 198  # Expected total foods in south_asian_foods.json
    try:
        food_db = SessionLocal()
        try:
            existing_count = (
                food_db.execute(select(func.count(Food.id))).scalar() or 0
            )
            eligible_count = (
                food_db.execute(
                    select(func.count(Food.id)).where(
                        Food.verification_status.in_([
                            VerificationStatus.VERIFIED,
                            VerificationStatus.VERIFIED_WITH_NOTES,
                        ]),
                        Food.is_active.is_(True),
                    )
                ).scalar()
                or 0
            )

            if existing_count >= EXPECTED_FOOD_COUNT:
                logger.info(
                    "Food dataset already present: %d foods (%d eligible); "
                    "skipping import",
                    existing_count,
                    eligible_count,
                )
            elif existing_count > 0:
                logger.warning(
                    "Food dataset incomplete: %d/%d foods present (%d eligible); "
                    "importing missing records",
                    existing_count,
                    EXPECTED_FOOD_COUNT,
                    eligible_count,
                )
                from app.services.food_import_service import import_foods_from_file

                dataset_path = (
                    Path(__file__).resolve().parent.parent
                    / "data"
                    / "south_asian_foods.json"
                )
                if dataset_path.exists():
                    result = import_foods_from_file(food_db, dataset_path)
                    final_count = (
                        food_db.execute(select(func.count(Food.id))).scalar() or 0
                    )
                    logger.info(
                        "Food dataset seed completed: imported=%d skipped=%d "
                        "failed=%d total_after=%d",
                        result.imported,
                        result.skipped,
                        result.failed,
                        final_count,
                    )
                    if final_count < EXPECTED_FOOD_COUNT:
                        logger.warning(
                            "Food dataset still incomplete after import: "
                            "%d/%d foods",
                            final_count,
                            EXPECTED_FOOD_COUNT,
                        )
                else:
                    logger.warning(
                        "Food dataset not found at %s; meal plans will have no foods",
                        dataset_path,
                    )
            else:
                dataset_path = (
                    Path(__file__).resolve().parent.parent
                    / "data"
                    / "south_asian_foods.json"
                )
                if dataset_path.exists():
                    from app.services.food_import_service import import_foods_from_file

                    result = import_foods_from_file(food_db, dataset_path)
                    final_count = (
                        food_db.execute(select(func.count(Food.id))).scalar() or 0
                    )
                    logger.info(
                        "Food dataset imported from empty DB: imported=%d "
                        "skipped=%d failed=%d total_after=%d",
                        result.imported,
                        result.skipped,
                        result.failed,
                        final_count,
                    )
                    if final_count < EXPECTED_FOOD_COUNT:
                        logger.warning(
                            "Food dataset incomplete after import: "
                            "%d/%d foods",
                            final_count,
                            EXPECTED_FOOD_COUNT,
                        )
                else:
                    logger.warning(
                        "Food dataset not found at %s; meal plans will have no foods",
                        dataset_path,
                    )
        finally:
            food_db.close()
    except Exception:
        logger.exception("Food dataset seed failed; application will continue starting")

    yield
    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Accept", "X-CSRF-Token"],
    )

    register_exception_handlers(app)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestSizeLimitMiddleware)
    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()

# ── Model Context Protocol (MCP) ─────────────────────────────────────
# FastMCP inspects the FastAPI OpenAPI schema and exposes declared routes
# as MCP tools, allowing an AI agent to call our API endpoints directly.
# Agents connect via the Streamable-HTTP transport at /mcp.
mcp_server = FastMCP.from_fastapi(app=app, name=settings.app_name)
app.mount("/mcp", mcp_server.http_app(transport="streamable-http"))
