from fastapi.testclient import TestClient
import pytest

from app.core.config import settings
from app.schemas.beleidskeuze import BeleidskeuzeCreate
from app.tests.utils.mock_data import generate_data


@pytest.mark.usefixtures("fixture_data")
class TestModules:
    """
    Ensure beleidsmodule endpoints CRUD as expected
    """

    def test_modules_create(self, client: TestClient, admin_headers):
        begin_date = str(settings.MIN_DATETIME)
        end_date = str(settings.MIN_DATETIME)
        request_data = {
            "Titel": "Auto Test module",
            "Begin_Geldigheid": begin_date,
            "Eind_Geldigheid": end_date,
            "Besluit_Datum": end_date,
        }

        response = client.post(
            "v0.1/beleidsmodules", headers=admin_headers, json=request_data
        )
        assert response.status_code == 200, f"Response: {response.json()}"

    def test_modules_OK_authenticated(self, client: TestClient, admin_headers):
        response = client.get("v0.1/beleidsmodules", headers=admin_headers)
        assert response.status_code == 200, f"Response: {response.json()}"
        assert len(response.json()) != 0
        assert "Maatregelen" in response.json()[0]

    def test_modules_valid_unauthenticated(self, client: TestClient):
        response = client.get("v0.1/valid/beleidsmodules")
        assert response.status_code == 200, f"Response: {response.json()}"

    def test_module_UUID(self, client: TestClient, admin_headers):
        # Create beleidskeuze (add objects)
        test_bk = generate_data(BeleidskeuzeCreate)
        response = client.post(
            "v0.1/beleidskeuzes", headers=admin_headers, json=test_bk
        )
        new_uuid = response.json()["UUID"]
        new_id = response.json()["ID"]

        # Create Module
        begin_date = str(settings.MIN_DATETIME)
        end_date = str(settings.MIN_DATETIME)
        request_data = {
            "Titel": "Auto Test module",
            "Begin_Geldigheid": begin_date,
            "Eind_Geldigheid": end_date,
            "Besluit_Datum": end_date,
            "Beleidskeuzes": [
                {"UUID": new_uuid, "Koppeling_Omschrijving": "auto test koppeling"}
            ],
        }

        response = client.post(
            "v0.1/beleidsmodules", headers=admin_headers, json=request_data
        )
        assert response.status_code == 200, f"Response: {response.json()}"
        module_uuid = response.json()["UUID"]
        module_id = response.json()["ID"]

        # Check reverse
        response = client.get(f"v0.1/beleidskeuzes/{new_id}", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()[0]["Ref_Beleidsmodules"][0]["UUID"] == module_uuid

        # Add new version to bk
        response = client.patch(
            f"v0.1/beleidskeuzes/{new_id}",
            headers=admin_headers,
            json={"Titel": "Nieuwe Titel"},
        )

        # Check reverse again
        response = client.get(f"v0.1/beleidskeuzes/{new_id}", headers=admin_headers)
        assert response.status_code == 200

        response_modules = response.json()[0]["Ref_Beleidsmodules"]
        assert response_modules[0]["ID"] == module_id
        assert response_modules[0]["UUID"] == module_uuid
