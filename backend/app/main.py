from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.api.router import api_router
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.logging import get_logger, setup_logging
from app.core.request_limits import RequestSizeLimitMiddleware
from app.core.security_headers import SecurityHeadersMiddleware
from app.db.session import SessionLocal
from app.models.food import Food
from app.scripts.seed_reference_data import seed_all

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

    # Seed food dataset (idempotent — skip if foods already exist)
    try:
        food_db = SessionLocal()
        try:
            has_foods = food_db.execute(
                select(Food.id).limit(1)
            ).scalar() is not None
            if has_foods:
                logger.info("Food dataset already present; skipping import")
            else:
                dataset_path = (
                    Path(__file__).resolve().parent.parent / "data" / "south_asian_foods.json"
                )
                if dataset_path.exists():
                    from app.services.food_import_service import import_foods_from_file

                    result = import_foods_from_file(food_db, dataset_path)
                    logger.info(
                        "Food dataset imported: %d imported, %d skipped, %d failed",
                        result.imported,
                        result.skipped,
                        result.failed,
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
