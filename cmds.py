import click

from sqlalchemy.orm import Session

from app.core.db import table_metadata, engine
from app.core.db.session import SessionLocal
from app.main import app # noqa We need this to load all sqlalchemy tables
from app.tests.database_fixtures import DatabaseFixtures


@click.group()
def cli():
    pass


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


cli.add_command(initdb, "init-db")
cli.add_command(dropdb, "drop-db")
cli.add_command(load_fixtures, "load-fixtures")


if __name__ == "__main__":
    cli()
