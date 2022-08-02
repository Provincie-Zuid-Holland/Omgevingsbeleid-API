from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware

from app.api.api_general.api import api_router as api_router_general
from app.api.api_v01.api import api_router as api_router_v01
from app.core.config import settings
from app.core import exceptions

app = FastAPI(
    title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V01_STR}/openapi.json"
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Routes
app.include_router(api_router_general)
app.include_router(api_router_v01, prefix=settings.API_V01_STR)

# Exception Handlers
app.add_exception_handler(
    exceptions.FilterNotAllowed, exceptions.filter_valdiation_handler
)
