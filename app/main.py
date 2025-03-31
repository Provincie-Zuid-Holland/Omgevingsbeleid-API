import asyncio  # noqa

from fastapi import APIRouter, FastAPI
from fastapi.openapi.utils import get_openapi

from app import api
from app.build.api_builder import ApiBuilder
from app.build.endpoint_builders.objects.object_latest_endpoint_builder import ObjectLatestEndpointBuilder
from app.container import Container

container = Container()
container.wire(modules=[__name__])

api_builder: ApiBuilder = container.build_package.api_builder()
api_builder.build()


# endpoints = [
#     ObjectLatestEndpointBuilder().build_endpoint_config()
# ]
# container.wire(modules=[__name__])


app = FastAPI()

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


# def custom_openapi():
#     if app.openapi_schema:
#         return app.openapi_schema

#     openapi_schema = get_openapi(
#         title="Omgevingsdienst API",
#         version="1.0.0",
#         openapi_version="3.1.0",
#         description="Omgevingsdienst API",
#         routes=app.routes,
#     )
#     openapi_schema["info"]["x-logo"] = {"url": "https://avatars.githubusercontent.com/u/60095455?s=200&v=4"}
#     app.openapi_schema = openapi_schema
#     return app.openapi_schema

# app.openapi = custom_openapi


a = True
