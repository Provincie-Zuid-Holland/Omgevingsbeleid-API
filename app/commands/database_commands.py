from typing import Annotated

import click
from dependency_injector.wiring import Provide, inject
from sqlalchemy import Engine, event, text
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.core.db import table_metadata
from tests.fixtures.internal.fixtures_service import FixturesService


@click.command()
@inject
def initdb(db_engine: Annotated[Engine, Provide[ApiContainer.db_engine]]):
    click.echo("Initialized the database")
    if db_engine.dialect.name != "sqlite":
        if not click.confirm("Database is not SQLite. Do you want to continue?"):
            return

    table_metadata.create_all(db_engine)
    click.echo("Done")


@click.command()
@inject
def dropdb(db_engine: Annotated[Engine, Provide[ApiContainer.db_engine]]):
    click.echo("Dropping database")
    if db_engine.dialect.name != "sqlite":
        if not click.confirm("Database is not SQLite. Do you want to continue?"):
            return

    table_metadata.drop_all(db_engine)
    click.echo("Dropped the database")


@click.command()
@inject
def load_fixtures(db_engine: Annotated[Engine, Provide[ApiContainer.db_engine]]):
    click.echo("Loading fixtures")
    if db_engine.dialect.name != "sqlite":
        if not click.confirm("Database is not SQLite. Do you want to continue?"):
            return

    def _disable_foreign_keys(dbapi_connection, _record) -> None:
        if db_engine.dialect.name == "sqlite":
            dbapi_connection.execute("PRAGMA foreign_keys = OFF")
        elif db_engine.dialect.name == "mssql":
            dbapi_connection.execute("""EXEC sp_MSforeachtable "ALTER TABLE ? NOCHECK CONSTRAINT ALL";""")

    event.listen(db_engine, "connect", _disable_foreign_keys)
    try:
        with Session(db_engine) as session:
            FixturesService().load(session)
            session.commit()

            if db_engine.dialect.name == "mssql":
                session.execute(text("""EXEC sp_MSforeachtable "ALTER TABLE ? WITH CHECK CHECK CONSTRAINT ALL";"""))
    finally:
        event.remove(db_engine, "connect", _disable_foreign_keys)
    click.echo("Done")
