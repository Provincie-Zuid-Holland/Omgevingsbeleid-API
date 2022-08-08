import click

from app.tests.testutils.data_loader import FixtureLoader
from app.db import base  # noqa: F401
from app.db.session import SessionLocal, engine


@click.group()
def cli():
    pass


@click.command()
def initdb():
    click.echo("Initialized the database")
    with SessionLocal() as session:
        loader = FixtureLoader(session)
        loader.load_fixtures()

    click.echo("Done")


# @click.command()
# def initview():
#     click.echo('Initialized the views')
#     # base.Base.metadata.create_all(
#     #     bind=engine,
#     #     checkfirst=True,
#     #     tables=[
#     #         base.valid_ambitie_view,
#     #     ]
#     # )
#     # print(base.Base.metadata.tables.keys())
#     # print("\n\n")
#     # print(base.valid_ambitie_view.create(bind=engine))

#     base.Base.metadata.create_all(
#         bind=engine,
#         checkfirst=True,
#         tables=[
#             base.valid_ambitie_view,
#         ]
#     )

#     click.echo('Done')


@click.command()
def dropdb():
    click.echo("Dropped the database")


cli.add_command(initdb)
# cli.add_command(initview)
cli.add_command(dropdb)


if __name__ == "__main__":
    cli()
