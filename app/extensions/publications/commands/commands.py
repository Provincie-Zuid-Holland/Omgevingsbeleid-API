import uuid

import click

from app.core.db.session import SessionLocal


@click.command()
@click.argument("package_arg", type=click.UUID)
def generate_dso_package(package_arg: uuid.UUID):
    """
    Command entrypoint to manually generate a DSO package.
    """
    with SessionLocal() as db:
        click.echo("---STARTED MANUAL DSO PACKAGE GENERATION---")
        # TODO:
        click.echo("---FINISHED MANUAL DSO PACKAGE GENERATION---")
