import click

from app.core.db import engine, table_metadata
from app.core.db.session import SessionLocal
from app.tests.database_fixtures import DatabaseFixtures


@click.command()
def initdb():
    click.echo("Initialized the database")
    table_metadata.create_all(engine)
    click.echo("Done")


@click.command()
def dropdb():
    click.echo("Dropping database")
    table_metadata.drop_all(engine)
    click.echo("Dropped the database")


@click.command()
def load_fixtures():
    click.echo("Start loading fixtures")
    with SessionLocal() as db:
        loader: DatabaseFixtures = DatabaseFixtures(db)
        loader.create_all()
        db.flush()
        db.commit()
    click.echo("Done")
