import asyncio  # noqa

from fastapi import FastAPI

from app.api.api_container import ApiContainer
from app.build.api_builder import ApiBuilder
from app.build.build_container import BuildContainer
from app.build.fastapi_builder import FastAPIBuilder

build_container = BuildContainer()
build_container.wire(packages=["app.build"])

api_container = ApiContainer(
    models_provider=build_container.models_provider,
    permission_service=build_container.permission_service,
)
api_container.wire(packages=["app.core", "app.api"])
api_container.init_resources()

api_builder: ApiBuilder = build_container.api_builder()
routes = api_builder.build()

fastapi_builder: FastAPIBuilder = FastAPIBuilder()
app: FastAPI = fastapi_builder.build(api_container, routes)
