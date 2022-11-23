from fastapi.testclient import TestClient
import pytest


@pytest.mark.usefixtures("fixture_data")
class TestApi:
    """
    Test endpoint options/params
    """

    def test_resource_not_found(self, client: TestClient):
        filter = "ID:9999999"
        response = client.get(
            url=f"v0.1/valid/beleidskeuzes?all_filters={filter}",
        )
        assert response.status_code == 404, "This endpoint should return 404"

    def test_limit(self, client: TestClient):
        response = client.get("v0.1/valid/beleidskeuzes?limit=1")
        assert response.status_code == 200, f"Status code was {response.status_code}"
        data = response.json()

        assert len(data) == 1, f"Expecting only 1 result"

    def test_offset(self, client: TestClient):
        base_response = client.get("v0.1/valid/beleidskeuzes?limit=3&offset=0")
        assert (
            base_response.status_code == 200
        ), f"Status code was {base_response.status_code}"
        base_data = base_response.json()

        offset_response = client.get("v0.1/valid/beleidskeuzes?limit=3&offset=2")
        assert (
            offset_response.status_code == 200
        ), f"Status code was {offset_response.status_code}"
        offset_data = offset_response.json()

        # should shift 2 spots
        assert offset_data[0]["UUID"] == base_data[2]["UUID"]

    def test_filter_all_OK(self, client: TestClient):
        # Only tests success response
        filter = "Afweging:beleidskeuze1011"
        response = client.get(f"v0.1/valid/beleidskeuzes?all_filters={filter}")
        assert response.status_code == 200, f"Status code was {response.status_code}"
        data = response.json()

    def test_filter_any_OK(self, client: TestClient):
        # Only tests success response
        filter = "Afweging:beleidskeuze1011"
        response = client.get(f"v0.1/valid/beleidskeuzes?any_filters={filter}")
        assert response.status_code == 200, f"Status code was {response.status_code}"
        data = response.json()

    def test_filter_status(self, client: TestClient, admin_headers):
        filter = "Status:Uitgecheckt"
        response = client.get(
            url=f"v0.1/beleidskeuzes?all_filters={filter}", headers=admin_headers
        )
        data = response.json()

        assert response.status_code == 200, f"Status code was {response.status_code}"
        assert len(data) > 0, "Should have at least one record"
        for json_obj in response.json():
            assert json_obj["Status"] == "Uitgecheckt", "Filter not filtering"

    def test_filter_multiple(self, client: TestClient, admin_headers):
        filter = "Status:Uitgecheckt,ID:999"
        response = client.get(
            url=f"v0.1/beleidskeuzes?all_filters={filter}", headers=admin_headers
        )
        data = response.json()

        assert response.status_code == 200, f"Status code was {response.status_code}"
        assert len(data) == 0, "Should not have results"

    def test_filter_invalid_field(self, client: TestClient, admin_headers):
        filter = "WrongField:Nope"
        response = client.get(
            url=f"v0.1/beleidskeuzes?all_filters={filter}", headers=admin_headers
        )
        assert response.status_code == 400, f"Status code was {response.status_code}"
