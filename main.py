import sys

import debugpy
from fastapi import FastAPI, Request
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

if __name__ == "__main__":
    # Allow starting app from main file
    # to setup DebugPy instance
    host = sys.argv[1]
    port = int(sys.argv[2])
    dap_port = int(sys.argv[3])

    print("---Initializing Debug application and DAP server---")
    print("Socket serving debug Application: ", host, port)
    print("DAP server listening on socket: ", host, dap_port)

    debugpy.listen((host, dap_port))
    uvicorn.run(app, host=host, port=port)
