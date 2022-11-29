from datetime import datetime
from typing import Dict
from uuid import uuid4

from pydantic import BaseModel
from pydantic.main import ModelMetaclass

from app.db.base_class import NULL_UUID
from app.tests.utils.exceptions import SetupMethodException


test_ambitie = {
    "Begin_Geldigheid": "1992-11-23T10:00:00",
    "Eind_Geldigheid": "2033-11-23T10:00:00",
    "Titel": "Test String",
    "Omschrijving": "Test String",
    "Weblink": "Test String",
}

test_belang = {
    "Begin_Geldigheid": "1992-11-23T10:00:00",
    "Eind_Geldigheid": "2033-11-23T10:00:00",
    "Titel": "Test String",
    "Omschrijving": "Test String",
    "Weblink": "Test String",
    "Type": "Nationaal Belang",
}

reference_rich_beleidskeuze = {
    "Status": "Vigerend",
    "Titel": "Beleidsbeslissing test Swen Initial",
    "Begin_Geldigheid": "2020-10-28T12:00:00",
    "Eind_Geldigheid": "2020-10-30T12:00:00",
    "Aanleiding": "Om te testen",
    "Afweging": "Zonder aanleiding",
    "Omschrijving_Keuze": "Nam libero leo, tempus in pretium vel, rhoncus in mi.",
    "Omschrijving_Werking": "Duis neque nulla, egestas aliquet nisi ut, dapibus pellentesque neque.",
    "Provinciaal_Belang": "In het belang van de wetenschap",
    "Weblink": "www.beleid.beslissing.nl",
    "Besluitnummer": "42",
    "Tags": "Wetenschap, Test",
    "Ambities": [
        {
            "UUID": "B786487C-3E65-4DD8-B360-D2C56BF83172",
            "Koppeling_Omschrijving": "TEST",
        },
        {
            "UUID": "0254A475-08A6-4B2A-A455-96BA6BE70A19",
            "Koppeling_Omschrijving": "TEST",
        },
    ],
}


def generate_data(
    obj_schema: BaseModel,
    user_UUID=NULL_UUID,
    default_str="Test String",
    default_int=42,
    default_date="1992-11-23T10:00:00",
) -> Dict:
    """
    Take a pydantic base class and return an object filled with mock
    data for testing purposes.
    """

    if type(obj_schema) is not ModelMetaclass:
        raise Exception("Unexcepted schema type, should be Pydantic")

    result = dict()
    properties = obj_schema.__fields__

    null_uuid_fields = [
        "Eigenaar_1_UUID",
        "Eigenaar_2_UUID",
        "Portefeuillehouder_1_UUID",
        "Portefeuillehouder_2_UUID",
        "Opdrachtgever_UUID",
        "Gebied_UUID",
    ]

    for field, info in properties.items():
        ftype = info.type_

        if field == "Created_By" or field == "Modified_By":
            result[field] = user_UUID

        elif field in null_uuid_fields:
            result[field] = NULL_UUID

        elif field == "Status":
            result[field] = "Niet-Actief"

        elif field == "Begin_Geldigheid":
            result[field] = "1992-11-23T10:00:00"

        elif field == "Eind_Geldigheid":
            result[field] = "2033-11-23T10:00:00"

        elif ftype == str:
            result[field] = default_str

        elif ftype == datetime:
            result[field] = default_date

        elif ftype == int:
            result[field] = default_int

    return result


def add_modifiable_object(schema, model, db, data=None):
    """
    Generate a db model instance and return it. Useful for specific
    test setups.
    """
    if not db:
        raise Exception(
            "No Session found. Should be provided as argument or injected by fixtures"
        )

    if not data:
        request_data = generate_data(
            obj_schema=schema,
            default_str="automated test",
        )
    else:
        request_data = data

    obj_data = schema(**request_data).dict()

    request_time = datetime.now()
    uuid = uuid4()

    obj_data["UUID"] = uuid
    obj_data["Created_By_UUID"] = NULL_UUID
    obj_data["Modified_By_UUID"] = NULL_UUID
    obj_data["Created_Date"] = request_time
    obj_data["Modified_Date"] = request_time

    try:
        instance = model(**obj_data)
        db.add(instance)
        db.commit()

        db_obj = db.query(model).filter(model.UUID == uuid).one()

        return db_obj
    except Exception:
        db.rollback()
        raise SetupMethodException
