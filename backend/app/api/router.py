from fastapi import APIRouter

from app.api.routes import (
    admin,
    ai,
    auth,
    billing,
    foods,
    health,
    locations,
    meal_plans,
    nutrition,
    onboarding,
    progress,
    settings,
    vapi,
    whatsapp_link,
)
from app.api.whatsapp import router as whatsapp_router

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(admin.router)
api_router.include_router(auth.router)
api_router.include_router(onboarding.router)
api_router.include_router(foods.router)
api_router.include_router(nutrition.router)
api_router.include_router(meal_plans.router)
api_router.include_router(locations.router)
api_router.include_router(progress.router)
api_router.include_router(settings.router)
api_router.include_router(whatsapp_link.router)
api_router.include_router(vapi.router)
api_router.include_router(billing.router)
api_router.include_router(ai.router)
api_router.include_router(whatsapp_router)
