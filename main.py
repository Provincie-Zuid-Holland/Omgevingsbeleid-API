import logging
import sys

import debugpy
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from starlette.middleware.cors import CORSMiddleware
import uvicorn

from app.api.api_general.api import api_router as api_router_general
from app.api.api_v01.api import api_router as api_router_v01
from app.core import exceptions
from app.core.config import get_settings

settings = get_settings()

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME, 
        openapi_url=f"{settings.API_V01_STR}/spec"
    )

    # Set all CORS enabled origins
    if settings.BACKEND_CORS_ORIGINS:
        origins = [str(origin) for origin in settings.BACKEND_CORS_ORIGINS]
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Routes
    app.include_router(api_router_general)
    app.include_router(api_router_v01, prefix=settings.API_V01_STR)

    # Exception Handlers
    app.add_exception_handler(
        exceptions.FilterNotAllowed, exceptions.filter_validation_handler
    )

    return app

# Main app instance
app = create_app()

# OpenAPI extending
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=settings.PROJECT_NAME,
        version="1.1.5",
        description=settings.PROJECT_DESC,
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = { "url": settings.OPENAPI_LOGO }
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Logging
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Allow starting app from main file
    # primarily to setup extra DebugPy instance
    host = sys.argv[1]
    port = int(sys.argv[2])
    if settings.DEBUG_MODE:
        dap_port = int(sys.argv[3])
        logger.info("---Initializing Debug application and DAP server---")
        logger.info("Socket serving debug Application: ", host, port)
        logger.info("DAP server listening on socket: ", host, dap_port)
        debugpy.listen((host, dap_port))

    uvicorn.run(app, host=host, port=port, debug=settings.DEBUG_MODE)
