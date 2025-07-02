import click  # noqa

from app.api.api_container import ApiContainer
from app.build.api_builder import ApiBuilder
from app.build.build_container import BuildContainer
from app.commands import database_commands, mssql_commands, publication_commands


@click.group()
def cli():
    """CLI for the application."""


cli.add_command(database_commands.initdb)
cli.add_command(database_commands.dropdb)
cli.add_command(database_commands.load_fixtures)
cli.add_command(mssql_commands.mssql_setup_search_database)
cli.add_command(publication_commands.create_dso_json_scenario)


if __name__ == "__main__":
    build_container = BuildContainer()
    build_container.wire(packages=["app.build"])

    api_container = ApiContainer(models_provider=build_container.models_provider)
    api_container.wire(packages=["app.core", "app.api", "app.commands"])
    api_container.init_resources()

    api_builder: ApiBuilder = build_container.api_builder()
    routes = api_builder.build()

    cli()
