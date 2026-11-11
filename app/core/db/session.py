from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import event, make_url
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

AsyncSessionFactoryType = async_sessionmaker[AsyncSession]


def _enable_aiosqlite_extensions(dbapi_connection, connection_record) -> None:
    async def load_spatialite(driver_connection) -> None:
        await driver_connection.enable_load_extension(True)
        await driver_connection.load_extension("mod_spatialite")

    dbapi_connection.run_async(load_spatialite)

    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.close()


def as_async_uri(uri: str) -> str:
    url = make_url(uri)
    if url.drivername in ("sqlite", "sqlite+pysqlite"):
        url = url.set(drivername="sqlite+aiosqlite")
    return url.render_as_string(hide_password=False)


def create_async_db_engine(uri: str, echo: str) -> AsyncEngine:
    engine: AsyncEngine = create_async_engine(
        as_async_uri(uri),
        pool_pre_ping=True,
        echo=echo,
    )
    if engine.dialect.name == "sqlite":
        event.listen(engine.sync_engine, "connect", _enable_aiosqlite_extensions)

    return engine


@asynccontextmanager
async def async_session_scope(session_factory: AsyncSessionFactoryType) -> AsyncGenerator[AsyncSession]:
    async with session_factory.begin() as session:
        yield session
