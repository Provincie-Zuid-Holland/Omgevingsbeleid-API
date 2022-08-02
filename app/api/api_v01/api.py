from fastapi import APIRouter

from app.api.api_v01.endpoints import (
    ambities,
    beleidsmodules,
    beleidsprestaties,
    login,
    beleidskeuzes,
    beleidsdoelen,
    beleidsrelaties,
    beleidsregels,
    themas,
    verordeningen,
    maatregelen,
    werkingsgebieden,
)

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(ambities.router, tags=["ambities"])
api_router.include_router(beleidskeuzes.router, tags=["beleidskeuzes"])
api_router.include_router(beleidsdoelen.router, tags=["beleidsdoelen"])
api_router.include_router(beleidsmodules.router, tags=["beleidsmodules"])
api_router.include_router(beleidsprestaties.router, tags=["beleidsprestaties"])
api_router.include_router(beleidsrelaties.router, tags=["beleidsrelaties"])
api_router.include_router(beleidsregels.router, tags=["beleidsregels"])
api_router.include_router(themas.router, tags=["themas"])
api_router.include_router(verordeningen.router, tags=["verordeningen"])
api_router.include_router(maatregelen.router, tags=["maatregelen"])
api_router.include_router(werkingsgebieden.router, tags=["werkingsgebieden"])
