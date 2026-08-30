from fastapi import APIRouter

from app.api.routes import (
    auth,
    foods,
    health,
    locations,
    meal_plans,
    nutrition,
    onboarding,
    progress,
    settings,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(onboarding.router)
api_router.include_router(foods.router)
api_router.include_router(nutrition.router)
api_router.include_router(meal_plans.router)
api_router.include_router(locations.router)
api_router.include_router(progress.router)
api_router.include_router(settings.router)
