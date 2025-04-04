import asyncio  # noqa

from fastapi import APIRouter, FastAPI
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel

from app.api.api_container import ApiContainer
from app.build.api_builder import ApiBuilder
from app.build.build_container import BuildContainer

build_container = BuildContainer()
build_container.wire(packages=["app.build"])

api_container = ApiContainer(models_provider=build_container.models_provider)
api_container.wire(packages=["app.core", "app.api"])
api_container.init_resources()

api_builder: ApiBuilder = build_container.api_builder()
routes = api_builder.build()

router = APIRouter()
for endpoint_config in routes:
    route_kwargs = {
        "path": endpoint_config.path,
        "endpoint": endpoint_config.endpoint,
        "methods": endpoint_config.methods,
        "summary": endpoint_config.summary,
        "description": endpoint_config.description,
        "tags": endpoint_config.tags,
    }

    if isinstance(endpoint_config.response_type, type) and issubclass(endpoint_config.response_type, BaseModel):
        route_kwargs["response_model"] = endpoint_config.response_type
    else:
        route_kwargs["response_type"] = endpoint_config.response_type

    router.add_api_route(**route_kwargs)


app = FastAPI()
app.container = api_container
app.include_router(router)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Omgevingsdienst API",
        version="1.0.0",
        openapi_version="3.1.0",
        description="Omgevingsdienst API",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {"url": "https://avatars.githubusercontent.com/u/60095455?s=200&v=4"}
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


a = True
