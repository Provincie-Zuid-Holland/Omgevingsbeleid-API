from typing import Dict

from fastapi.testclient import TestClient

from app.core.config import settings


def get_admin_headers(client: TestClient) -> Dict[str, str]:
    login_data = {
        "username": "admin@test.com",
        "password": "password",
    }
    r = client.post(f"{settings.API_V01_STR}/login/access-token", data=login_data)
    tokens = r.json()
    a_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {a_token}"}
    return headers


def get_fred_headers(client: TestClient) -> Dict[str, str]:
    login_data = {
        "username": "fred@test.com",
        "password": "password",
    }
    r = client.post(f"{settings.API_V01_STR}/login/access-token", data=login_data)
    tokens = r.json()
    a_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {a_token}"}
    return headers


reference_rich_beleidsdoel = {
    "Titel": "Beleidsbeslissing test Swen Initial",
    "Begin_Geldigheid": "2020-10-28T12:00:00",
    "Eind_Geldigheid": "2020-10-30T12:00:00",
    "Omschrijving": "Nam libero leo, tempus in pretium vel, rhoncus in mi.",
    "Weblink": "www.beleidsdoel.beslissing.nl",
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


# def generate_data(schema, user_UUID=settings.NULL_UUID, excluded_prop=None):
#     fields = schema(exclude=schema.fields_with_props([excluded_prop])).fields
#     result = {}
#     for field in fields:
#         validatee = False
#         if fields[field].validators:
#             validators = fields[field].validators
#             for validator in validators:
#                 if isinstance(validator, MM.validate.OneOf):
#                     result[field] = validator.choices[0]
#                     validatee = True

#         if validatee:
#             continue

#         if field == "Created_By" or field == "Modified_By":
#             result[field] = user_UUID

#         elif field == "Status":
#             result[field] = "Niet-Actief"

#         elif field == "Eind_Geldigheid":
#             result[field] = "2033-11-23T10:00:00"

#         elif type(fields[field]) == MM.fields.String:
#             result[field] = "Test String"

#         elif type(fields[field]) == MM.fields.UUID:
#             result[field] = null_uuid

#         elif type(fields[field]) == MM.fields.Integer:
#             result[field] = 42

#         elif type(fields[field]) == MM.fields.DateTime:
#             result[field] = "1992-11-23T10:00:00"

#         elif type(fields[field]) == MM.fields.Method:
#             result[field] = ""

#         elif type(fields[field]) == MM.fields.Nested:
#             result[field] = []

#         else:
#             raise NotImplementedError(
#                 f"Missing implementation for field {field} ({type(fields[field])}) with value {fields[field]}"
#             )
#     return result
