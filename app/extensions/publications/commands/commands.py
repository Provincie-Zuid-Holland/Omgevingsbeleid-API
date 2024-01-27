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
from app.extensions.publications.enums import Bill_Type
from app.extensions.publications.models import PublicationBill, PublicationConfig, PublicationPackage
from app.extensions.publications.repository.ow_object_repository import OWObjectRepository
from app.extensions.publications.repository.publication_object_repository import PublicationObjectRepository
from app.extensions.publications.repository.publication_repository import PublicationRepository
from app.extensions.publications.tables.ow import (
    OWAmbtsgebiedTable,
    OWAssociationTable,
    OWDivisieTable,
    OWDivisietekstTable,
    OWGebiedTable,
    OWGebiedenGroepTable,
    OWTekstdeelTable,
)
from app.extensions.publications.tables.tables import DSOStateExportTable
from app.extensions.source_werkingsgebieden.repository import MssqlGeometryRepository


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
        state_exported = json.loads(service.get_filtered_export_state())

        # Step 4: Store results in database + OW Objects
        # new_export = DSOStateExportTable(
        #     UUID=uuid.uuid4(),
        #     Created_Date=datetime.now(),
        #     Modified_Date=datetime.now(),
        #     Package_UUID=package_arg,
        #     Export_Data=state_exported,
        # )
        # new_export = pub_repo.create_dso_state_export(new_export)

        ow_objects = create_ow_objects_from_json(
            exported_state=state_exported,
            package_uuid=package.UUID,
            bill_type=bill.Bill_Type,
        )
        ow_repo = OWObjectRepository(db)
        result = ow_repo.create_ow_objects(ow_objects)

        for obj in result:
            click.echo("Created OW object: " + str(obj.OW_ID))

        click.echo("---FINISHED MANUAL DSO PACKAGE GENERATION---")


def create_ow_objects_from_json(exported_state, package_uuid: uuid.UUID, bill_type: Bill_Type):
    # Check if 'ow_repository' key exists in the data
    if "ow_repository" not in exported_state:
        raise ValueError("Invalid data format: 'ow_repository' key not found.")

    ow_data = exported_state["ow_repository"]

    created_objects = []

    # Set shared values for created ow objects
    current_time = datetime.now()
    shared_ow_attrs = {
        "Created_Date": current_time,
        "Modified_Date": current_time,
        "Package_UUID": package_uuid,
        "Procedure_Status": bill_type,
    }

    # Process 'locaties_content'
    if "locaties_content" in ow_data:
        locaties_content = ow_data["locaties_content"]

        # Process 'gebiedengroepen'
        for gebiedengroep in locaties_content.get("gebiedengroepen", []):
            group = OWGebiedenGroepTable(
                UUID=uuid.uuid4(),
                OW_ID=gebiedengroep["OW_ID"],
                Geo_UUID=gebiedengroep.get("geo_uuid"),
                Noemer=gebiedengroep.get("noemer"),
                **shared_ow_attrs,
            )
            created_objects.append(group)

        # Process 'gebieden'
        for gebied in locaties_content.get("gebieden", []):
            area = OWGebiedTable(
                UUID=uuid.uuid4(),
                OW_ID=gebied["OW_ID"],
                Geo_UUID=gebied.get("geo_uuid"),
                Noemer=gebied.get("noemer"),
                **shared_ow_attrs,
            )
            created_objects.append(area)

        # Process 'ambtsgebieden'
        for ambtsgebied in locaties_content.get("ambtsgebieden", []):
            office_area = OWAmbtsgebiedTable(
                UUID=uuid.uuid4(),
                OW_ID=ambtsgebied["OW_ID"],
                Bestuurlijke_grenzen_id=ambtsgebied["bestuurlijke_genzenverwijzing"]["bestuurlijke_grenzen_id"],
                Domein=ambtsgebied["bestuurlijke_genzenverwijzing"]["domein"],
                Geldig_Op=ambtsgebied["bestuurlijke_genzenverwijzing"]["geldig_op"],
                **shared_ow_attrs,
            )
            created_objects.append(office_area)

    if "divisie_content" in ow_data:
        div_content = ow_data["divisie_content"]

        # Process 'divisie' and "divisietekst" annotations
        for annotation in div_content.get("annotaties", []):
            required_keys = ["tekstdeel"]
            optional_keys = ["divisie_aanduiding", "divisietekst_aanduiding"]

            missing_required_keys = [key for key in required_keys if key not in annotation]
            missing_optional_keys = [key for key in optional_keys if key not in annotation]

            if missing_required_keys or len(missing_optional_keys) == len(optional_keys):
                raise ValueError("Invalid data format: Required keys are missing in annotation.")

            if annotation.get("divisie_aanduiding"):
                division_pointer = annotation["divisie_aanduiding"]
                div = OWDivisieTable(
                    UUID=uuid.uuid4(), OW_ID=division_pointer["OW_ID"], WID=division_pointer["wid"], **shared_ow_attrs
                )
                created_objects.append(div)
            if annotation.get("divisietekst_aanduiding"):
                division_pointer = annotation["divisietekst_aanduiding"]
                div = OWDivisietekstTable(
                    UUID=uuid.uuid4(), OW_ID=division_pointer["OW_ID"], WID=division_pointer["wid"], **shared_ow_attrs
                )
                created_objects.append(div)

            if "tekstdeel" not in annotation:
                raise ValueError("Invalid data format: 'tekstdeel' key not found in divisie_content item.")

            # Process 'tekstdeel' annotation
            annotation_item = OWTekstdeelTable(
                UUID=uuid.uuid4(),
                OW_ID=annotation["tekstdeel"]["OW_ID"],
                Divisie_ref=annotation["tekstdeel"]["divisie"],
                **shared_ow_attrs,
            )

            if "locations" in annotation["tekstdeel"]:
                for location_ow_id in annotation["tekstdeel"]["locations"]:
                    matching_object = next((obj for obj in created_objects if obj.OW_ID == location_ow_id), None)
                    annotation_item.Locations.append(matching_object)
                    # loc_relation = OWAssociationTable(OW_ID_1=annotation_item.OW_ID, OW_ID_2=location_ow_id)
                    # created_objects.append(loc_relation)

            created_objects.append(annotation_item)

    return created_objects
