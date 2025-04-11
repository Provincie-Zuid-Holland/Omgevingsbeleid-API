from typing import List
from fastapi import APIRouter, FastAPI
from fastapi.openapi.utils import get_openapi


from app.api.api_container import ApiContainer
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint


def configure_openapi(
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


class FastAPIBuilder:
    def build(self, container: ApiContainer, routes: List[ConfiguiredFastapiEndpoint]) -> FastAPI:
        app: FastAPI = FastAPI()
        app.container = container

        self._add_routes(app, routes)
        app.openapi = configure_openapi(
            app,
            container.config.PROJECT_VERSION(),
            container.config.PROJECT_NAME(),
            container.config.PROJECT_DESC(),
            container.config.OPENAPI_LOGO(),
        )

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
