from typing import Annotated

import click
from dependency_injector.wiring import Provide, inject
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.core.db import table_metadata
from tests.fixtures.internal.fixtures_service import FixturesService


def _guard_non_dev_environment(db_password: str) -> None:
    if db_password not in ["Passw0rd", "password"]:
        raise RuntimeError("Database connection not in DEV environment")

def _disable_foreign_keys(dialect: str, session: Session) -> None:
    if dialect == "sqlite":
        session.execute(text("PRAGMA foreign_keys = OFF"))
    elif dialect == "postgresql":
        session.execute(text("""SET session_replication_role = 'replica';"""))
    elif dialect == "mssql":
        session.execute(text("""EXEC sp_MSforeachtable "ALTER TABLE ? NOCHECK CONSTRAINT ALL";"""))


def _enable_foreign_keys(dialect: str, session: Session) -> None:
    if dialect == "sqlite":
        session.execute(text("PRAGMA foreign_keys = OFF"))
    elif dialect == "postgresql":
        session.execute(text("""SET session_replication_role = 'origin';"""))
    elif dialect == "mssql":
        session.execute(text("""EXEC sp_MSforeachtable "ALTER TABLE ? NOCHECK CONSTRAINT ALL";"""))

@click.command()
@inject
def initdb(
    db_password: Annotated[str, Provide[ApiContainer.config.DB_PASS]],
    db_engine: Annotated[Engine, Provide[ApiContainer.db_engine]],
):
    _guard_non_dev_environment(db_password)
    click.echo("Initializing the database")

    table_metadata.create_all(db_engine)
    click.echo("Done")


@click.command()
@inject
def dropdb(
    db_password: Annotated[str, Provide[ApiContainer.config.DB_PASS]],
    db_engine: Annotated[Engine, Provide[ApiContainer.db_engine]],
):
    _guard_non_dev_environment(db_password)
    click.echo("Dropping database")

    table_metadata.drop_all(db_engine)
    click.echo("Done")


@click.command()
@inject
def load_fixtures(db_engine: Annotated[Engine, Provide[ApiContainer.db_engine]]):
    click.echo("Loading fixtures")

    try:
        with Session(db_engine) as session:
            _disable_foreign_keys(db_engine.dialect.name, session)
            FixturesService().load(session)
            _enable_foreign_keys(db_engine.dialect.name, session)
            session.commit()
    finally:
        click.echo("Done")
