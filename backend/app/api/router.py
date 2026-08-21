from fastapi import APIRouter

from app.api.routes import auth, foods, health, nutrition, onboarding

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(onboarding.router)
api_router.include_router(foods.router)
api_router.include_router(nutrition.router)
