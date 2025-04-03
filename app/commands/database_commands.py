from typing import Annotated

import click
from dependency_injector.wiring import Provide, inject
from sqlalchemy import Engine

from app.core.db import table_metadata
from app.api.api_container import ApiContainer


@click.command()
@inject
def initdb(
    db_engine: Annotated[Engine, Provide[ApiContainer.db_engine]]
):
    click.echo("Initialized the database")
    table_metadata.create_all(db_engine)
    click.echo("Done")


@click.command()
@inject
def dropdb(
    db_engine: Annotated[Engine, Provide[ApiContainer.db_engine]]
):
    click.echo("Dropping database")
    table_metadata.drop_all(db_engine)
    click.echo("Dropped the database")


# @click.command()
# def dropdb():
#     click.echo("Dropping database")
#     table_metadata.drop_all(engine)
#     click.echo("Dropped the database")


# @click.command()
# def load_fixtures():
#     click.echo("Start loading fixtures")
#     with SessionLocal() as db:
#         loader: DatabaseFixtures = DatabaseFixtures(db)
#         loader.create_all()
#         db.flush()
#         db.commit()
#     click.echo("Done")
