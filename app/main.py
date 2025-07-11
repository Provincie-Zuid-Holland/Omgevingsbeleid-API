import asyncio  # noqa

from fastapi import FastAPI

from app.api.api_container import ApiContainer
from app.build.api_builder import ApiBuilder
from app.build.build_container import BuildContainer
from app.build.fastapi_builder import FastAPIBuilder
from app.core.db.session import session_scope
from app.core.settings import Settings

build_container = BuildContainer()
build_container.wire(packages=["app.build"])

api_container = ApiContainer(
    db_session_factory=build_container.db_session_factory,
    config=build_container.config,
    main_config=build_container.main_config,
    models_provider=build_container.models_provider,
)
api_container.wire(packages=["app.core", "app.api"])
api_container.init_resources()


session_maker = build_container.db_session_factory()
with session_scope(session_maker) as session:
    api_builder: ApiBuilder = build_container.api_builder()
    routes = api_builder.build(session)


fastapi_builder: FastAPIBuilder = FastAPIBuilder()
# @todo
print(Settings().SQLALCHEMY_DATABASE_URI[:20])
app: FastAPI = fastapi_builder.build(api_container, routes)
