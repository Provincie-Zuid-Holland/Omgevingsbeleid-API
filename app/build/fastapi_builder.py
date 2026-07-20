import logging
import os
from typing import List, Set

import sqlalchemy
import sqlalchemy.exc
from fastapi import APIRouter, FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from app.api.api_container import ApiContainer
from app.api.exceptions import LoggedHttpException
from app.api.health_endpoint import health_check
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint
from app.core.logging import init_logging


logger = logging.getLogger(os.getenv("LOG_LOGGER_NAME", "obzh"))


def _generate_unique_id_function(route: APIRoute) -> str:
    operation_id = route.name
    if operation_id.endswith("_endpoint"):
        operation_id = operation_id[:-9]
    if len(route.tags) == 1:
        operation_id = f"{route.tags[0].lower()}_{operation_id}"
    return operation_id


class FastAPIBuilder:
    def build(self, container: ApiContainer, routes: List[ConfiguredFastapiEndpoint]) -> FastAPI:
        init_logging()

        app: FastAPI = FastAPI(
            generate_unique_id_function=_generate_unique_id_function,
        )
        app.container = container

        self._add_routes(app, routes)
        app.openapi = self._configure_openapi(
            app,
            container.config.PROJECT_VERSION(),
            container.config.PROJECT_NAME(),
            container.config.PROJECT_DESC(),
            container.config.OPENAPI_LOGO(),
        )

        self._configure_exception_handlers(app)
        self._configure_operation_ids(app)
        app.add_api_route("/health", health_check)

        app.state.db_sessionmaker = container.db_session_factory()

        return app

    def _add_routes(self, app: FastAPI, routes: List[ConfiguredFastapiEndpoint]):
        router = APIRouter()
        for endpoint_config in routes:
            route_kwargs = {
                "path": endpoint_config.path,
                "endpoint": endpoint_config.endpoint,
                "methods": endpoint_config.methods,
                "response_model": endpoint_config.response_model,
                "summary": endpoint_config.summary,
                "description": endpoint_config.description,
                "tags": endpoint_config.tags,
            }
            if endpoint_config.operation_id:
                route_kwargs["operation_id"] = endpoint_config.operation_id

            router.add_api_route(**route_kwargs)

        app.include_router(router)

    def _configure_openapi(
        self,
        app: FastAPI,
        project_version: str,
        project_name: str,
        project_description: str,
        openapi_logo: str,
    ):
        def custom_openapi():
            if app.openapi_schema:
                return app.openapi_schema

            openapi_schema = get_openapi(
                title=project_name,
                version=project_version,
                openapi_version="3.1.0",
                description=project_description,
                routes=app.routes,
            )
            openapi_schema["info"]["x-logo"] = {"url": openapi_logo}
            app.openapi_schema = openapi_schema
            return app.openapi_schema

        return custom_openapi

    def _configure_exception_handlers(self, app: FastAPI):
        @app.exception_handler(sqlalchemy.exc.IntegrityError)
        async def _sql_exc(request: Request, exc: sqlalchemy.exc.IntegrityError):
            return JSONResponse(
                {"msg": "Foreign key error", "__debug__exception": str(exc)},
                status_code=400,
            )

        @app.exception_handler(LoggedHttpException)
        async def _logged_http(request: Request, exc: LoggedHttpException):
            api_env = os.getenv("API_ENV", "unknown")
            logger.error(
                msg=f"Unhandled HTTPException: {exc.get_log_message()}",
                exc_info=exc,
                extra={
                    "api_env": api_env,
                    "http_status_code": exc.status_code,
                    "request_path": request.url.path,
                    "request_method": request.method,
                    "exception_type": type(exc).__name__,
                    "exception_detail": exc.detail,
                },
            )
            return await http_exception_handler(request, exc)

    def _configure_operation_ids(self, app: FastAPI) -> None:
        used_operation_ids: Set[str] = set()

        for route in app.routes:
            if isinstance(route, APIRoute):
                operation_id = route.unique_id
                if operation_id in used_operation_ids:
                    raise RuntimeError(
                        "Duplicate operation id detected: %s. This may cause issues with operation IDs.",
                        operation_id,
                    )

                used_operation_ids.add(operation_id)
                route.operation_id = operation_id
