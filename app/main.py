import asyncio
from typing import Type  # noqa

from fastapi import APIRouter, FastAPI
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel

from app import api
from app.build.api_builder import ApiBuilder
from app.build.endpoint_builders.objects.object_latest_endpoint_builder import ObjectLatestEndpointBuilder
from app.container import Container

container = Container()
# container.wire(modules=[__name__])
container.wire(modules=["app.api.domains.objects.endpoints.object_latest_endpoint"])

api_builder: ApiBuilder = container.build_package.api_builder()
routes = api_builder.build()
endpoints = [r.endpoint for r in routes]
# container.wire(modules=[__name__])

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

# endpoints = [
#     ObjectLatestEndpointBuilder().build_endpoint_config()
# ]
# container.wire(modules=[__name__])


app = FastAPI()
app.include_router(router)


# router = APIRouter()
# for endpoint_config in endpoints:
#     router.add_api_route(
#         endpoint_config.path,
#         endpoint_config.endpoint,
#         methods=endpoint_config.methods,
#         response_class=endpoint_config.response_class,
#         summary=endpoint_config.summary,
#         description=endpoint_config.description,
#         tags=endpoint_config.tags,
#     )

# app.include_router(router)


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
