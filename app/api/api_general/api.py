from fastapi import APIRouter

from app.api.api_general.endpoints import health

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
