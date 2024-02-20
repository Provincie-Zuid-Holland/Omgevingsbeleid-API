import re
import uuid
from datetime import date, datetime
from typing import List, Tuple

from app.extensions.publications.enums import IMOWTYPE, OWAssociationType, ProcedureType
from app.extensions.publications.exceptions import DSOExportOWError
from app.extensions.publications.tables.ow import (
    OWAmbtsgebiedTable,
    OWAssociationTable,
    OWDivisieTable,
    OWDivisietekstTable,
    OWGebiedenGroepTable,
    OWGebiedTable,
    OWObjectTable,
    OWRegelingsgebiedTable,
    OWTekstdeelTable,
)

OW_REGEX = r"nl\.imow-(gm|pv|ws|mn|mnre)[0-9]{1,6}\.(regeltekst|gebied|gebiedengroep|lijn|lijnengroep|punt|puntengroep|activiteit|gebiedsaanwijzing|omgevingswaarde|omgevingsnorm|pons|kaart|tekstdeel|hoofdlijn|divisie|kaartlaag|juridischeregel|activiteitlocatieaanduiding|normwaarde|regelingsgebied|ambtsgebied|divisietekst)\.[A-Za-z0-9]{1,32}"


def generate_ow_id(ow_type: IMOWTYPE, unique_code: str = None) -> str:
    prefix = "nl.imow-pv28"
    if not unique_code:
        unique_code = uuid.uuid4().hex

    generated_id = f"{prefix}.{ow_type.value}.{unique_code}"

    imow_pattern = re.compile(OW_REGEX)
    if not imow_pattern.match(generated_id):
        raise Exception("generated IMOW ID does not match official regex")

    return generated_id


def create_updated_ambtsgebied_data(
    administative_borders_id: str, administative_borders_domain: str, administrative_borders_date: date
):
    new_ambtsgebied_id = generate_ow_id(ow_type=IMOWTYPE.AMBTSGEBIED)
    new_regelingsgebied_id = generate_ow_id(ow_type=IMOWTYPE.REGELINGSGEBIED)
    regelingsgebied_data = {
        "ambtsgebied": {
            "OW_ID": new_ambtsgebied_id,
            "bestuurlijke_genzenverwijzing": {
                "bestuurlijke_grenzen_id": administative_borders_id,
                "domein": administative_borders_domain,
                "geldig_op": administrative_borders_date,
            },
        },
        "regelingsgebied": {
            "OW_ID": new_regelingsgebied_id,
            "ambtsgebied": new_ambtsgebied_id,
        },
    }
    return regelingsgebied_data


def create_ow_objects_from_json(
    exported_state: dict, bill_type: ProcedureType
) -> Tuple[List[OWObjectTable], List[OWAssociationTable]]:
    """
    Parses the DSO exported state to build a list of OW objects with the correct relations.
    """

    # Check if 'ow_repository' key exists in the data
    if "ow_repository" not in exported_state:
        raise DSOExportOWError("Invalid export data format: 'ow_repository' key not found.")

    ow_data = exported_state["ow_repository"]
    created_objects = []
    created_relations = []

    # Set shared values for created ow objects
    current_time = datetime.now()
    shared_ow_attrs = {
        "Created_Date": current_time,
        "Modified_Date": current_time,
        "Procedure_Status": bill_type,
    }

    # Process 'locaties_content'
    if "locaties_content" in ow_data:
        locaties_content = ow_data["locaties_content"]

        # Process 'gebieden'
        for gebied in locaties_content.get("gebieden"):
            area = OWGebiedTable(
                UUID=uuid.uuid4(),
                OW_ID=gebied["OW_ID"],
                Geo_UUID=gebied.get("geo_uuid"),
                Noemer=gebied.get("noemer"),
                **shared_ow_attrs,
            )
            created_objects.append(area)

        # Process 'gebiedengroepen'
        for group in locaties_content.get("gebiedengroepen"):
            area_group = OWGebiedenGroepTable(
                UUID=uuid.uuid4(),
                OW_ID=group["OW_ID"],
                Geo_UUID=group["geo_uuid"],
                Noemer=group["noemer"],
                **shared_ow_attrs,
            )
            # find the matching locations from earlier created objects and fill
            # the areas contained in this group. Assocation rows are auto created.
            for location in group["locations"]:
                matching_object = next((obj for obj in created_objects if obj.OW_ID == location["OW_ID"]), None)
                if not matching_object:
                    raise DSOExportOWError("Invalid data: Could not find matching Area defined in this Area Group.")
                area_group.Gebieden.append(matching_object)

            created_objects.append(area_group)

    # Process 'divisie_content'
    if "divisie_content" in ow_data:
        div_content = ow_data["divisie_content"]

        # Process 'divisie' and "divisietekst" annotations
        for annotation in div_content.get("annotaties", []):
            required_keys = ["tekstdeel"]
            optional_keys = ["divisie_aanduiding", "divisietekst_aanduiding"]

            missing_required_keys = [key for key in required_keys if key not in annotation]
            missing_optional_keys = [key for key in optional_keys if key not in annotation]

            if missing_required_keys or len(missing_optional_keys) == len(optional_keys):
                raise DSOExportOWError("Invalid data format: Required keys are missing in annotation.")

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
                raise DSOExportOWError("Invalid data format: 'tekstdeel' key not found in divisie_content item.")

            # Process 'tekstdeel' annotations
            annotation_item = OWTekstdeelTable(
                UUID=uuid.uuid4(),
                OW_ID=annotation["tekstdeel"]["OW_ID"],
                Divisie_ref=annotation["tekstdeel"]["divisie"],
                **shared_ow_attrs,
            )

            if "locations" in annotation["tekstdeel"]:
                for location_ow_id in annotation["tekstdeel"]["locations"]:
                    # find the matching Locations in earlier created objects
                    # and fill the relation. Assocation rows are auto created.
                    matching_object = next((obj for obj in created_objects if obj.OW_ID == location_ow_id), None)
                    if not matching_object:
                        raise DSOExportOWError(
                            "Invalid data: Could not find matching OW Location defined in this Division annotation."
                        )

                    # TODO: manual relationship for now due to session bug with duplicates
                    # annotation_item.Locations.append(matching_object)
                    created_relations.append(
                        OWAssociationTable(
                            OW_ID_1_HASH=annotation_item.OW_ID_HASH,
                            OW_ID_2_HASH=matching_object.OW_ID_HASH,
                            Type=OWAssociationType.TEKSTDEEL_LOCATION.value,
                        )
                    )

            created_objects.append(annotation_item)

    # Process regelingsgebied_content
    if "locaties_content" in ow_data:
        for ambtsgebied in ow_data["locaties_content"].get("ambtsgebieden", []):
            ambts_ow = OWAmbtsgebiedTable(
                UUID=uuid.uuid4(),
                OW_ID=ambtsgebied["OW_ID"],
                Bestuurlijke_grenzen_id=ambtsgebied["bestuurlijke_genzenverwijzing"]["bestuurlijke_grenzen_id"],
                Domein=ambtsgebied["bestuurlijke_genzenverwijzing"]["domein"],
                Geldig_Op=ambtsgebied["bestuurlijke_genzenverwijzing"]["geldig_op"],
                **shared_ow_attrs,
            )
            created_objects.append(ambts_ow)
    if "regelingsgebied_content" in ow_data:
        for regelingsgebied in ow_data["regelingsgebied_content"].get("regelingsgebieden", []):
            rg_object = OWRegelingsgebiedTable(
                UUID=uuid.uuid4(),
                OW_ID=regelingsgebied["OW_ID"],
                Ambtsgebied=regelingsgebied["ambtsgebied"],
                **shared_ow_attrs,
            )
            created_objects.append(rg_object)
    return created_objects, created_relations
