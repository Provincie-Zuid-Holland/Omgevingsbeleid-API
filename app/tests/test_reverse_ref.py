from fastapi.testclient import TestClient
import pytest
from app.core.config import settings

from app.schemas import AmbitieCreate, BeleidskeuzeCreate
from app.tests.utils.mock_data import generate_data


@pytest.mark.usefixtures("fixture_data")
class TestReverseReferences:
    def test_reverse_lookup(self, client: TestClient, admin_headers):
        """
        Test reverse lookups work and show the correct inlined objects
        """
        # Create Ambitie
        ambitie_data = generate_data(AmbitieCreate)
        ambitie_data["Eind_Geldigheid"] = str(settings.MAX_DATETIME)

        response = client.post(
            "v0.1/ambities",
            headers=admin_headers,
            json=ambitie_data,
        )
        assert (
            response.status_code == 200
        ), f"Status code for POST was {response.status_code}, should be 200. Body content: {response.json}"
        assert (
            response.json()["Ref_Beleidskeuzes"] == []
        ), f"Reverse lookup not empty on post. Body content: {response.json}"

        ambitie_id = response.json()["ID"]
        ambitie_uuid = response.json()["UUID"]

        # Create a new Beleidskeuze
        beleidskeuze_data = generate_data(BeleidskeuzeCreate)
        beleidskeuze_data["Status"] = "Vigerend"
        beleidskeuze_data["Eind_Geldigheid"] = str(settings.MAX_DATETIME)
        # set relation with ambitie
        beleidskeuze_data["Ambities"] = [
            {
                "UUID": ambitie_uuid,
                "Koppeling_Omschrijving": "Automated test koppeling",
            }
        ]

        response = client.post(
            "v0.1/beleidskeuzes", headers=admin_headers, json=beleidskeuze_data
        )
        assert (
            response.status_code == 200
        ), f"Status code for POST was {response.status_code}, should be 200. Body content: {response.json}"
        assert (
            response.json()["Ambities"][0]["Object"]["UUID"] == ambitie_uuid
        ), f"Nested objects are not on object. Body content: {response.json}"

        beleidskeuze_id = response.json()["ID"]
        beleidskeuze_uuid = response.json()["UUID"]

        # Get the ambitie
        response = client.get(
            f"v0.1/ambities/{ambitie_id}",
            headers=admin_headers,
        )
        assert (
            response.status_code == 200
        ), f"Status code for GET was {response.status_code}, should be 200. Body content: {response.json}"
        assert (
            len(response.json()[0]["Ref_Beleidskeuzes"]) == 1
        ), f"Wrong amount of objects in reverse lookup field. Lookup field: {response.json()[0]['Ref_Beleidskeuzes']}"
        assert (
            response.json()[0]["Ref_Beleidskeuzes"][0]["UUID"] == beleidskeuze_uuid
        ), f"Nested objects are not on object. Body content: {response.json}"

        # Add a new version to the lineage
        response = client.patch(
            f"v0.1/beleidskeuzes/{beleidskeuze_id}",
            headers=admin_headers,
            json={"Titel": "New Title"},
        )
        assert (
            response.status_code == 200
        ), f"Status code for POST was {response.status_code}, should be 200. Body content: {response.json}"
        assert (
            response.json()["Ambities"][0]["Object"]["UUID"] == ambitie_uuid
        ), f"Nested objects are not on object. Body content: {response.json}"
        beleidskeuze_latest_id = response.json()["ID"]
        beleidskeuze_latest_uuid = response.json()["UUID"]

        # Get the ambitie
        response = client.get(f"v0.1/ambities/{ambitie_id}", headers=admin_headers)
        assert (
            response.status_code == 200
        ), f"Status code for GET was {response.status_code}, should be 200. Body content: {response.json}"
        assert (
            len(response.json()[0]["Ref_Beleidskeuzes"]) == 1
        ), f"Too many objects in reverse lookup field. Lookup field: {response.json()[0]['Ref_Beleidskeuzes']}"
        assert (
            response.json()[0]["Ref_Beleidskeuzes"][0]["UUID"]
            == beleidskeuze_latest_uuid
        ), f"Nested objects are on object. Body content: {response.json}"
