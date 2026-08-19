from typing import Annotated

import click
from dependency_injector.wiring import Provide, inject
from sqlalchemy import Engine, event
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.core.db import table_metadata
from tests.fixtures.internal.fixtures_service import FixturesService


@click.command()
@inject
def initdb(
    db_engine: Annotated[Engine, Provide[ApiContainer.db_engine]],
    database_uri: Annotated[str, Provide[ApiContainer.config.SQLALCHEMY_DATABASE_URI]],
):
    click.echo("Initialized the database")
    if database_uri[0:6] != "sqlite":
        raise RuntimeError("Can only run `initdb` for sqlite")

    table_metadata.create_all(db_engine)
    click.echo("Done")


@click.command()
@inject
def dropdb(
    db_engine: Annotated[Engine, Provide[ApiContainer.db_engine]],
    database_uri: Annotated[str, Provide[ApiContainer.config.SQLALCHEMY_DATABASE_URI]],
):
    click.echo("Dropping database")
    if database_uri[0:6] != "sqlite":
        raise RuntimeError("Can only run `dropdb` for sqlite")

    table_metadata.drop_all(db_engine)
    click.echo("Dropped the database")


@click.command()
@inject
def load_fixtures(
    db_engine: Annotated[Engine, Provide[ApiContainer.db_engine]],
    database_uri: Annotated[str, Provide[ApiContainer.config.SQLALCHEMY_DATABASE_URI]],
):
    click.echo("Loading fixtures")
    if database_uri[0:6] != "sqlite":
        raise RuntimeError("Can only run `load_fixtures` for sqlite")

    def _disable_foreign_keys(dbapi_connection, _record) -> None:
        dbapi_connection.execute("PRAGMA foreign_keys = OFF")

    event.listen(db_engine, "connect", _disable_foreign_keys)
    try:
        with Session(db_engine) as session:
            FixturesService().load(session)
            session.commit()
    finally:
        event.remove(db_engine, "connect", _disable_foreign_keys)
    click.echo("Done")
