from typing import List
from fastapi import APIRouter, FastAPI, Request
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
import sqlalchemy
import sqlalchemy.exc

import logging
from fastapi.exception_handlers import http_exception_handler
from app.api.api_container import ApiContainer
from app.api.exceptions import LoggedHttpException
from app.api.health_endpoint import health_check
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint


logger = logging.getLogger(__name__)


class FastAPIBuilder:
    def build(self, container: ApiContainer, routes: List[ConfiguiredFastapiEndpoint]) -> FastAPI:
        app: FastAPI = FastAPI()
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

    def _add_routes(self, app: FastAPI, routes: List[ConfiguiredFastapiEndpoint]):
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
            logger.error(
                "Unhandled HTTPException: %s, Path: %s",
                exc.get_log_message(),
                request.url.path,
                exc_info=True,
            )
            return await http_exception_handler(request, exc)

    def _configure_operation_ids(self, app: FastAPI) -> None:
        used_operation_ids = set()

        for route in app.routes:
            if isinstance(route, APIRoute):
                operation_id = route.name
                if operation_id.endswith("_endpoint"):
                    operation_id = operation_id[:-9]
                if operation_id in used_operation_ids:
                    logger.warning(
                        "Duplicate operation id detected: %s. This may cause issues with operation IDs.",
                        operation_id,
                    )
                used_operation_ids.add(operation_id)
                route.operation_id = operation_id
