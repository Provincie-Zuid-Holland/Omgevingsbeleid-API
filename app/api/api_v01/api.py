from fastapi import APIRouter
from fastapi.utils import re

from app.api.api_v01.endpoints import (
    ambities,
    belangen,
    beleidsdoelen,
    beleidskeuzes,
    beleidsmodules,
    beleidsprestaties,
    beleidsregels,
    beleidsrelaties,
    edits,
    graph,
    gebruikers,
    gebiedsprogrammas,
    login,
    maatregelen,
    search,
    themas,
    verordeningen,
    werkingsgebieden,
)

def generate_unique_id(route: "APIRouter") -> str:
    route_name = route.name
    operation_id = route_name
    operation_id = re.sub("[^0-9a-zA-Z_]", "_", operation_id)
    # assert route.methods
    # operation_id = operation_id + "_" + list(route.methods)[0].lower()
    return operation_id

api_router = APIRouter(generate_unique_id_function=generate_unique_id)
api_router.include_router(login.router, tags=["login"])
api_router.include_router(ambities.router, tags=["ambities"])
api_router.include_router(belangen.router, tags=["belangen"])
api_router.include_router(beleidskeuzes.router, tags=["beleidskeuzes"])
api_router.include_router(beleidsdoelen.router, tags=["beleidsdoelen"])
api_router.include_router(beleidsmodules.router, tags=["beleidsmodules"])
api_router.include_router(beleidsprestaties.router, tags=["beleidsprestaties"])
api_router.include_router(beleidsrelaties.router, tags=["beleidsrelaties"])
api_router.include_router(beleidsregels.router, tags=["beleidsregels"])
api_router.include_router(edits.router, tags=["edits"])
api_router.include_router(graph.router, tags=["graph"])
api_router.include_router(gebruikers.router, tags=["gebruikers"])
api_router.include_router(gebiedsprogrammas.router, tags=["gebiedsprogrammas"])
api_router.include_router(search.router, tags=["search"])
api_router.include_router(themas.router, tags=["themas"])
api_router.include_router(verordeningen.router, tags=["verordeningen"])
api_router.include_router(maatregelen.router, tags=["maatregelen"])
api_router.include_router(werkingsgebieden.router, tags=["werkingsgebieden"])
