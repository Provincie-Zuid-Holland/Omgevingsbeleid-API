from fastapi import APIRouter

from app.api.api_v01.endpoints import ambities, login

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(ambities.router, prefix="/ambities", tags=["ambities"])
