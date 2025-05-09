import logging
import sys
from datetime import datetime, timezone

import sqlalchemy.exc
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.exception_handlers import http_exception_handler
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session

from app.app import dynamic_app
from app.core.db.session import SessionLocal
from app.core.exceptions import LoggedHttpException

# Logging
logger = logging.getLogger(__name__)

app: FastAPI = dynamic_app.run()
build_datetime: datetime = datetime.now(timezone.utc)


@app.get("/health")
async def health_check():
    health_info = {
        "status": "healthy",
        "database": "ok",
        "version": "11",
        "build": str(build_datetime),
    }

    try:
        session: Session = SessionLocal()
        session.close()
    except sqlalchemy.exc.SQLAlchemyError:
        health_info["status"] = "unhealthy"
        health_info["database"] = "not connected"

    if health_info["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_info)

    return health_info


@app.exception_handler(sqlalchemy.exc.IntegrityError)
async def sql_exception_handler(request, exc):  # noqa
    return JSONResponse(
        {
            "msg": "Foreign key error",
            "__debug__exception": str(exc),
        },
        status_code=400,
    )


@app.exception_handler(LoggedHttpException)
async def logged_http_exception_handler(request, exc: LoggedHttpException):  # noqa
    logger.error("Unhandled HTTPException: %s, Path: %s", exc.get_log_message(), request.url.path, exc_info=True)
    return await http_exception_handler(request, exc)


def set_operator_id_from_unique_id(app: FastAPI) -> None:
    """
    The prefix of the operator_id is currently the function name of the route,
    which is undesirable for the Frontend as it results in cluttered auto-generated names.
    As a temporary solution, we are generating the operation_id from the unique_id and
    eliminating the function name. However, this approach is not sustainable if
    we transition to an open-source platform.

    @todo: we should use the generate_unique_id_function in adding the endpoint instead
    """
    for route in app.routes:
        if isinstance(route, APIRoute):
            route.operation_id = route.unique_id.replace("fastapi_handler_", "", 1)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.state.settings.PROJECT_NAME,
        version=app.state.settings.PROJECT_VERSION,
        openapi_version="3.1.0",
        description=app.state.settings.PROJECT_DESC,
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {"url": app.state.settings.OPENAPI_LOGO}
    app.openapi_schema = openapi_schema
    return app.openapi_schema


set_operator_id_from_unique_id(app)
app.openapi = custom_openapi


if __name__ == "__main__":
    # Allow starting app from main file
    # primarily to setup extra DebugPy instance
    host = sys.argv[1]
    port = int(sys.argv[2])
    dap_port = int(sys.argv[3])
    logger.info("---Initializing Debug application and DAP server---")
    logger.info("Socket serving debug Application: ", host, port)
    logger.info("DAP server listening on socket: ", host, dap_port)
    import debugpy

    debugpy.listen((host, dap_port))

    uvicorn.run(app, host=host, port=port)
