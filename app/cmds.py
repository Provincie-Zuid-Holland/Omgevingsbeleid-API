import click  # noqa

from app.api.api_container import ApiContainer
from app.build.api_builder import ApiBuilder, ApiBuilderResult
from app.build.build_container import BuildContainer
from app.commands import database_commands, mssql_commands, publication_commands, gdpr_commands
from app.core.db.session import session_scope_with_context


@click.group()
def cli():
    """CLI for the application."""


cli.add_command(database_commands.initdb)
cli.add_command(database_commands.dropdb)
cli.add_command(database_commands.load_fixtures)
cli.add_command(mssql_commands.mssql_setup_search_database)
cli.add_command(publication_commands.create_dso_json_scenario)
cli.add_command(gdpr_commands.check_pdfs)


if __name__ == "__main__":
    build_container = BuildContainer()
    build_container.wire(packages=["app.build"])

    api_builder: ApiBuilder = build_container.api_builder()

    session_maker = build_container.db_session_factory()
    with session_scope_with_context(session_maker) as session:
        build_result: ApiBuilderResult = api_builder.build(session)

    api_container = ApiContainer(
        models_provider=build_container.models_provider,
        object_field_mapping_provider=build_result.object_field_mapping_provider,
    )
    api_container.wire(packages=["app.core", "app.api", "app.commands"])
    api_container.init_resources()

    cli()
