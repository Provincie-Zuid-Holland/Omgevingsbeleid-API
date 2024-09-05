import asyncio
import os
from uuid import UUID

import click
from dso.act_builder.state_manager.input_data.input_data_loader import InputData, InputDataExporter
from fastapi import FastAPI

from app.dynamic.utils.commands import resolve_dependencies
from app.extensions.publications.dependencies import (
    depends_act_package_builder_factory,
    depends_publication_version_repository,
)
from app.extensions.publications.enums import MutationStrategy, PackageType
from app.extensions.publications.repository.publication_version_repository import PublicationVersionRepository
from app.extensions.publications.services.act_package.act_package_builder import ActPackageBuilder
from app.extensions.publications.services.act_package.act_package_builder_factory import ActPackageBuilderFactory


def write_json_file(input_data: str, filename: str) -> None:
    with open(filename, "w") as file:
        file.write(input_data)


@click.command()
@click.option("--publication_version", default=None, help="Publication version")
@click.pass_obj
def create_dso_json_scenario(fastapi_app: FastAPI, publication_version) -> None:
    asyncio.run(_do_create_dso_json_scenario(fastapi_app, publication_version))


async def _do_create_dso_json_scenario(fastapi_app: FastAPI, publication_version) -> None:
    if not publication_version:
        publication_version = click.prompt("Please enter the publication_version UUID:", type=str)

    output_path = os.path.join(os.getcwd(), "output")
    version_uuid = UUID(publication_version)
    package_type_obj = PackageType.PUBLICATION

    services = await resolve_dependencies(
        fastapi_app,
        {
            "publication_version_repository": depends_publication_version_repository,
            "package_builder_factory": depends_act_package_builder_factory,
        },
    )

    pv_repository: PublicationVersionRepository = services["publication_version_repository"]
    package_builder_factory: ActPackageBuilderFactory = services["package_builder_factory"]

    pub_version = pv_repository.get_by_uuid(version_uuid)
    if not pub_version:
        click.echo(click.style("Publication version UUID does not exist in DB", fg="red"))
        return

    click.echo(click.style("Creating DSO JSON scenario from publication version: %s" % publication_version, fg="green"))

    builder: ActPackageBuilder = package_builder_factory.create_builder(
        pub_version,
        package_type_obj,
        MutationStrategy.RENVOOI,
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
