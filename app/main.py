import asyncio  # noqa

from fastapi import FastAPI

from app.api.api_container import ApiContainer
from app.build.api_builder import ApiBuilder, ApiBuilderResult
from app.build.build_container import BuildContainer
from app.build.fastapi_builder import FastAPIBuilder
from app.core.db.session import session_scope_with_context
from app.core.settings import Settings

build_container = BuildContainer()
build_container.wire(packages=["app.build"])

session_maker = build_container.db_session_factory()
with session_scope_with_context(session_maker) as session:
    api_builder: ApiBuilder = build_container.api_builder()
    build_result: ApiBuilderResult = api_builder.build(session)

api_container = ApiContainer(
    models_provider=build_container.models_provider,
    object_field_mapping_provider=build_result.object_field_mapping_provider,
)
api_container.wire(packages=["app.core", "app.api"])
api_container.init_resources()

fastapi_builder: FastAPIBuilder = FastAPIBuilder()
# @todo
print(Settings().SQLALCHEMY_DATABASE_URI[:20])
app: FastAPI = fastapi_builder.build(api_container, build_result.routes)
