import json
import uuid
from datetime import datetime

import click

from app.core.db.session import SessionLocal
from app.extensions.html_assets.repository.assets_repository import AssetRepository
from app.extensions.publications.dso.dso_assets_factory import DsoAssetsFactory
from app.extensions.publications.dso.dso_service import DSOService
from app.extensions.publications.dso.dso_werkingsgebieden_factory import DsoWerkingsgebiedenFactory
from app.extensions.publications.dso.template_parser import TemplateParser
from app.extensions.publications.dso.templates.omgevingsprogramma import OmgevingsprogrammaTextTemplate
from app.extensions.publications.dso.templates.omgevingsvisie import OmgevingsvisieTextTemplate
from app.extensions.publications.models import PublicationBill, PublicationConfig, PublicationPackage
from app.extensions.publications.repository.publication_object_repository import PublicationObjectRepository
from app.extensions.publications.repository.publication_repository import PublicationRepository
from app.extensions.publications.tables.tables import DSOStateExportTable
from app.extensions.werkingsgebieden.repository import MssqlGeometryRepository


@click.command()
@click.argument("package_arg", type=click.UUID)
def generate_dso_package(package_arg: uuid.UUID):
    """
    Command entrypoint to manually generate a DSO package.
    """
    with SessionLocal() as db:
        click.echo("---STARTED MANUAL DSO PACKAGE GENERATION---")
        click.echo("package uuid: " + str(package_arg))

        # Step 1: Fetch required data from database
        pub_repo = PublicationRepository(db)
        package_db = pub_repo.get_publication_package(uuid=package_arg)
        bill_db = pub_repo.get_publication_bill(uuid=package_db.Bill_UUID)
        config_db = pub_repo.get_latest_config()

        bill = PublicationBill.from_orm(bill_db)
        package = PublicationPackage.from_orm(package_db)
        config = PublicationConfig.from_orm(config_db)

        pub_object_repository = PublicationObjectRepository(db)
        objects = pub_object_repository.fetch_objects(
            module_id=bill.Module_ID,
            timepoint=datetime.utcnow(),
            object_types=[
                "visie_algemeen",
                "ambitie",
                "beleidsdoel",
                "beleidskeuze",
            ],
            field_map=[
                "UUID",
                "Object_Type",
                "Object_ID",
                "Code",
                "Hierarchy_Code",
                "Gebied_UUID",
                "Title",
                "Description",
                "Cause",
                "Provincial_Interest",
                "Explanation",
            ],
        )

        click.echo("Building DSO package for objects:")
        for obj in objects:
            click.echo(obj["UUID"])

        # Step 2: Call DSO service to prepare input data and build package
        service = DSOService(
            {
                "Omgevingsvisie": TemplateParser(template_style=OmgevingsvisieTextTemplate()),
                "Omgevingsprogramma": TemplateParser(template_style=OmgevingsprogrammaTextTemplate()),
            },
            DsoWerkingsgebiedenFactory(MssqlGeometryRepository(db)),
            DsoAssetsFactory(AssetRepository(db)),
        )

        input_data = service.prepare_publication_input(bill, package, config, objects)
        service.build_dso_package(input_data)

        # Step 3: TAKE STATE AND BUILD EXPORT FORMAT
        state_exported = service.get_exported_state()

        # Step 4: Store results in database + OW Objects
        new_export = DSOStateExportTable(
            UUID=uuid.uuid4(),
            Created_Date=datetime.now(),
            Modified_Date=datetime.now(),
            Package_UUID=package_arg,
            Export_Data=json.loads(state_exported),
        )
        result = pub_repo.create_dso_state_export(new_export)

        click.echo("Result:")
        click.echo(result)

        # ow_repo = OWObjectRepository(db)
        # pub_repo.create_ow_object()
        click.echo("---FINISHED MANUAL DSO PACKAGE GENERATION---")
