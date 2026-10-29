from typing import Annotated

import click
from dependency_injector.wiring import Provide, inject
from sqlalchemy import Connection, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.api.api_container import ApiContainer
from app.commands.async_runner import run_with_connection, run_with_session
from app.core.db import table_metadata
from app.core.db.session import AsyncSessionFactoryType
from tests.fixtures.internal.fixtures_service import FixturesService


def _guard_non_dev_environment(db_password: str) -> None:
    if db_password not in ["Passw0rd", "password", "omgevingsbeleid"]:
        raise RuntimeError("Database connection not in DEV environment")


async def _disable_foreign_keys(dialect: str, session: AsyncSession) -> None:
    if dialect == "sqlite":
        await session.execute(text("PRAGMA foreign_keys = OFF"))
    elif dialect == "postgresql":
        await session.execute(text("""SET session_replication_role = 'replica';"""))


async def _enable_foreign_keys(dialect: str, session: AsyncSession) -> None:
    if dialect == "sqlite":
        await session.execute(text("PRAGMA foreign_keys = OFF"))
    elif dialect == "postgresql":
        await session.execute(text("""SET session_replication_role = 'origin';"""))


@click.command()
@inject
def initdb(
    db_password: Annotated[str, Provide[ApiContainer.config.DB_PASS]],
    db_engine: Annotated[AsyncEngine, Provide[ApiContainer.db_engine]],
):
    _guard_non_dev_environment(db_password)
    click.echo("Initializing the database")

    run_with_connection(db_engine, table_metadata.create_all)
    click.echo("Done")


@click.command()
@inject
def dropdb(
    db_password: Annotated[str, Provide[ApiContainer.config.DB_PASS]],
    db_engine: Annotated[AsyncEngine, Provide[ApiContainer.db_engine]],
):
    _guard_non_dev_environment(db_password)
    click.echo("Dropping database")

    run_with_connection(db_engine, _drop_all)
    click.echo("Done")


def _drop_all(connection: Connection) -> None:
    if connection.dialect.name == "sqlite":
        connection.exec_driver_sql("PRAGMA foreign_keys = OFF")
    table_metadata.drop_all(connection)


@click.command()
@inject
def load_fixtures(
    db_session_factory: Annotated[AsyncSessionFactoryType, Provide[ApiContainer.db_session_factory]],
):
    click.echo("Loading fixtures")

    try:
        run_with_session(db_session_factory, _load_fixtures)
    finally:
        click.echo("Done")


async def _load_fixtures(session: AsyncSession) -> None:
    dialect: str = session.bind.dialect.name
    await _disable_foreign_keys(dialect, session)
    await FixturesService().load(session)
    await _enable_foreign_keys(dialect, session)
