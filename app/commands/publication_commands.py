import asyncio
import os
from typing import Annotated
from uuid import UUID

from dependency_injector.wiring import Provide, inject
import click
from app.api.api_container import ApiContainer
from app.api.domains.publications.repository.publication_version_repository import PublicationVersionRepository
from app.api.domains.publications.services.act_package.act_package_builder import ActPackageBuilder
from app.api.domains.publications.services.act_package.act_package_builder_factory import ActPackageBuilderFactory
from app.api.domains.publications.types.enums import MutationStrategy, PackageType
from dso.act_builder.state_manager.input_data.input_data_loader import InputData, InputDataExporter


@click.command()
@click.option("--publication_version", default=None, help="Publication version")
@click.option("--mutation-strategy", default=MutationStrategy.RENVOOI, help="renvooi or replace")
@click.pass_obj
@inject
def create_dso_json_scenario(
    publication_version,
    mutation_strategy,
    publication_version_repository: Annotated[PublicationVersionRepository, Provide[ApiContainer.publication.version_repository]],
    act_package_builder_factory: Annotated[ActPackageBuilderFactory, Provide[ApiContainer.publication.act_package_builder_factory]],
) -> None:
    if not publication_version:
        publication_version = click.prompt("Please enter the publication_version UUID:", type=str)

    try:
        mutation_strat = MutationStrategy(mutation_strategy)
    except ValueError:
        click.error(click.style("Invalid mutation strategy, should be renvooi or replace", fg="red"))
        return

    output_path = os.path.join(os.getcwd(), "output")
    version_uuid = UUID(publication_version)
    package_type_obj = PackageType.PUBLICATION

    pub_version = publication_version_repository.get_by_uuid(version_uuid)
    if not pub_version:
        click.echo(click.style("Publication version UUID does not exist in DB", fg="red"))
        return

    click.echo(click.style("Creating DSO JSON scenario from publication version: %s" % publication_version, fg="green"))

    builder: ActPackageBuilder = act_package_builder_factory.create_builder(
        pub_version,
        package_type_obj,
        mutation_strategy=mutation_strat,
    )

    # extract the final InputData without starting the .build_publication_files() process
    dso_input_data: InputData = builder.get_input_data()
    exporter = InputDataExporter(input_data=dso_input_data, output_dir=output_path)

    try:
        exporter.export_dev_scenario()
        click.echo(click.style(f"DSO JSON scenario saved in: {output_path}", fg="green"))
        click.echo(click.style("---finished---", fg="green"))
    except Exception as e:
        click.echo(click.style(f"Error while exporting DSO JSON scenario:", fg="red"))
        click.echo(click.style(f"{e}", fg="red"))
        return
