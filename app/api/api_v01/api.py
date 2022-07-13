from fastapi import APIRouter

from app.api.api_v01.endpoints import ambities, beleidsmodules, login, beleidskeuzes, beleidsdoelen, maatregelen

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(ambities.router, tags=["ambities"])
api_router.include_router(beleidskeuzes.router, tags=["beleidskeuzes"])
api_router.include_router(beleidsdoelen.router, tags=["beleidsdoelen"])
api_router.include_router(beleidsmodules.router, tags=["beleidsmodules"])
api_router.include_router(maatregelen.router, tags=["maatregelen"])
