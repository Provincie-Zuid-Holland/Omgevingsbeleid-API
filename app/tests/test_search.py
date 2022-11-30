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

    def test_search_success(self, client: TestClient, admin_headers):
        # Create Ambitie
        test_amb = generate_data(AmbitieCreate)
        test_amb["Eind_Geldigheid"] = "2992-11-23T10:00:00"
        amb_resp = client.post("v0.1/ambities", headers=admin_headers, json=test_amb)
        amb_UUID = amb_resp.json()["UUID"]

        # Assert
        response = client.get("v0.1/graph", headers=admin_headers)
        count = response.json()["count"]
        results = response.json()["results"]

        assert len(count) != 0, "Excepted results found"
#        assert amb_UUID in results, "Ambitie not retrieved"

