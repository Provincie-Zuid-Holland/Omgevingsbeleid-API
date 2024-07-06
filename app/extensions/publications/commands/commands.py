import os
from uuid import UUID

import click
from dso.act_builder.state_manager.input_data.input_data_loader import InputData, InputDataExporter

from app.core.dependencies import db_in_context_manager
from app.extensions.areas.repository.area_repository import AreaRepository
from app.extensions.html_assets.repository.assets_repository import AssetRepository
from app.extensions.publications.enums import PackageType
from app.extensions.publications.repository.publication_aoj_repository import PublicationAOJRepository
from app.extensions.publications.repository.publication_object_repository import PublicationObjectRepository
from app.extensions.publications.services.act_frbr_provider import ActFrbrProvider
from app.extensions.publications.services.act_package.act_package_builder import ActPackageBuilder
from app.extensions.publications.services.act_package.act_package_builder_factory import ActPackageBuilderFactory
from app.extensions.publications.services.act_package.act_publication_data_provider import ActPublicationDataProvider
from app.extensions.publications.services.act_package.werkingsgebieden_provider import (
    PublicationWerkingsgebiedenProvider,
)
from app.extensions.publications.services.assets.asset_remove_transparency import AssetRemoveTransparency
from app.extensions.publications.services.assets.publication_asset_provider import PublicationAssetProvider
from app.extensions.publications.services.bill_frbr_provider import BillFrbrProvider
from app.extensions.publications.services.purpose_provider import PurposeProvider
from app.extensions.publications.services.state.data.state_v1 import StateV1
from app.extensions.publications.services.state.state_loader import StateLoader
from app.extensions.publications.services.state.state_version_factory import StateVersionFactory
from app.extensions.publications.services.template_parser import TemplateParser
from app.extensions.publications.tables.tables import PublicationVersionTable


def write_json_file(input_data: str, filename: str) -> None:
    with open(filename, "w") as file:
        file.write(input_data)


@click.command()
@click.argument("publication_version")
@click.argument("package_type")
@click.option("--output", default="main.json", help="Output file name")
def create_dso_json_scenario(publication_version, package_type, output) -> None:
    output_path = os.path.join(os.getcwd(), "output")
    version_UUID = UUID(publication_version)
    package_type_obj = PackageType(package_type)

    click.echo(click.style("Creating DSO JSON scenario from publication version: %s" % publication_version, fg="green"))

    with db_in_context_manager() as db:
        pub_version = db.query(PublicationVersionTable).filter(PublicationVersionTable.UUID == version_UUID).one()

        # Manually sertup the ActPackageBuilder dependencies since
        # we cannot use the FastAPI Depends()
        state_version_factory = StateVersionFactory()
        state_version_factory.add(StateV1)  # TODO: still StateV1 until upgraded

        publication_asset_provider = PublicationAssetProvider(AssetRepository(db), AssetRemoveTransparency())
        publication_werkingsgebieden_provider = PublicationWerkingsgebiedenProvider(AreaRepository(db))

        act_publication_data_provider = ActPublicationDataProvider(
            publication_object_repository=PublicationObjectRepository(db),
            publication_asset_provider=publication_asset_provider,
            publication_werkingsgebieden_provider=publication_werkingsgebieden_provider,
            publication_aoj_repository=PublicationAOJRepository(db),
            template_parser=TemplateParser(),
        )

        package_builder_factory = ActPackageBuilderFactory(
            db=db,
            bill_frbr_provider=BillFrbrProvider(db),
            act_frbr_provider=ActFrbrProvider(db),
            purpose_provider=PurposeProvider(db),
            state_loader=StateLoader(state_version_factory),
            publication_data_provider=act_publication_data_provider,
        )

        builder: ActPackageBuilder = package_builder_factory.create_builder(pub_version, package_type_obj)

    # extract the final InputData without starting the .build_publication_files() process
    dso_input_data: InputData = builder.input_data
    exporter = InputDataExporter(input_data=dso_input_data, output_dir=output_path)

    try:
        exporter.export_full_scenario()
        click.echo(click.style(f"DSO JSON scenario saved in: {output}", fg="green"))
        click.echo(click.style("---finished---", fg="green"))
    except Exception as e:
        click.echo(click.style(f"Error while exporting DSO JSON scenario:", fg="red"))
        click.echo(click.style(f"{e}", fg="red"))
        return
