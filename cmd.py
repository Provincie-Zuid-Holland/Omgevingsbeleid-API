import click

from app.tests.testutils.data_loader import FixtureLoader
from app.db.session import SessionLocal


@click.group()
def cli():
    pass


@click.command()
def initdb():
    click.echo('Initialized the database')
    with SessionLocal() as session:
        loader = FixtureLoader(session)
        loader.load_fixtures()

    click.echo('Done')


@click.command()
def dropdb():
    click.echo('Dropped the database')


cli.add_command(initdb)
cli.add_command(dropdb)


if __name__ == '__main__':
    cli()
