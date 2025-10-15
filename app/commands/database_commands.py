from typing import Annotated

import click
from dependency_injector.wiring import Provide, inject
from sqlalchemy import Engine

from app.api.api_container import ApiContainer
from app.api.domains.users.services.security import Security
from app.api.domains.werkingsgebieden.repositories.area_geometry_repository import AreaGeometryRepository
from app.api.domains.werkingsgebieden.repositories.geometry_repository import GeometryRepository
from app.core.db import table_metadata
from app.core.db.session import SessionFactoryType, session_scope_with_context
from app.tests.fixtures.database_fixtures_old import DatabaseFixturesOld


@click.command()
@inject
def initdb(db_engine: Annotated[Engine, Provide[ApiContainer.db_engine]]):
    click.echo("Initialized the database")
    table_metadata.create_all(db_engine)
    click.echo("Done")


@click.command()
@inject
def dropdb(db_engine: Annotated[Engine, Provide[ApiContainer.db_engine]]):
    click.echo("Dropping database")
    table_metadata.drop_all(db_engine)
    click.echo("Dropped the database")


@click.command()
@inject
def load_fixtures(
    db_session_factory: Annotated[SessionFactoryType, Provide[ApiContainer.db_session_factory]],
    geometry_repository: Annotated[GeometryRepository, Provide[ApiContainer.geometry_repository]],
    area_geometry_repository: Annotated[AreaGeometryRepository, Provide[ApiContainer.area_geometry_repository]],
    security: Annotated[Security, Provide[ApiContainer.security]],
):
    with session_scope_with_context(db_session_factory) as session:
        loader: DatabaseFixturesOld = DatabaseFixturesOld(
            session,
            geometry_repository,
            area_geometry_repository,
            security,
        )
        loader.create_all()

        session.flush()
        session.commit()
        click.echo("Done")
