import logging
import sys

import debugpy
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
import uvicorn

from app.api.api_general.api import api_router as api_router_general
from app.api.api_v01.api import api_router as api_router_v01
from app.core import exceptions
from app.core.config import settings

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

# Logging
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    # Allow starting app from main file
    # primarily to setup extra DebugPy instance
    host = sys.argv[1]
    port = int(sys.argv[2])
    print(f"MODE IS ---------- {settings.DEBUG_MODE}")
    if settings.DEBUG_MODE:
        dap_port = int(sys.argv[3])
        logger.info("---Initializing Debug application and DAP server---")
        logger.info("Socket serving debug Application: ", host, port)
        logger.info("DAP server listening on socket: ", host, dap_port)
        debugpy.listen((host, dap_port))
    else:
        logger.info("DEBUG_MODE False, skipping DAP instance")

    uvicorn.run(app, host=host, port=port, debug=settings.DEBUG_MODE)
