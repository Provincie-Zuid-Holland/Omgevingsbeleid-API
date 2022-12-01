from fastapi.testclient import TestClient
import pytest
from app.schemas import AmbitieCreate, BelangCreate, BeleidskeuzeCreate
from app.tests.utils.mock_data import generate_data


@pytest.mark.usefixtures("fixture_data")
class TestSearchService:
    """
    Functional endpoint tests to verify expected results
    of search requests and its parameters.
    """

    def test_search_matching_pattern(self, client: TestClient, admin_headers):
        # Arrange
        test_amb = generate_data(AmbitieCreate)
        test_amb["Titel"] = "Water water en nog eens water"
        test_amb["Eind_Geldigheid"] = "2992-11-23T10:00:00"
        amb_resp = client.post("v0.1/ambities", headers=admin_headers, json=test_amb)
        amb_UUID = amb_resp.json()["UUID"]

        search_query = "water"

        # Act
        response = client.get(f"v0.1/search?query={search_query}", headers=admin_headers)

        # Assert
        count = response.json()["total"]
        results = response.json()["results"]

        uuid_in_results = False
        for item in results:
            if item["UUID"] == amb_UUID:
                uuid_in_results = True


        assert count != 0, "Expected results to be found"
        assert uuid_in_results == True, f"Ambitie {amb_UUID} expected but not found in results"

    def test_search_non_matching_pattern(self, client: TestClient, admin_headers):
        # Arrange
        test_amb = generate_data(AmbitieCreate)
        test_amb["Titel"] = "Water water en nog eens water"
        test_amb["Eind_Geldigheid"] = "2992-11-23T10:00:00"
        amb_resp = client.post("v0.1/ambities", headers=admin_headers, json=test_amb)
        amb_UUID = amb_resp.json()["UUID"]

        search_query = "VUUR"

        # Act
        response = client.get(f"v0.1/search?query={search_query}", headers=admin_headers)

        # Assert
        count = response.json()["total"]
        results = response.json()["results"]

        uuid_in_results = False
        for item in results:
            if item["UUID"] == amb_UUID:
                uuid_in_results = True


        assert count == 0, "Expected no results to be found"
        assert uuid_in_results != True, f"Ambitie {amb_UUID} should not match"
