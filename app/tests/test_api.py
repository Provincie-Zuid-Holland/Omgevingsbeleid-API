from fastapi.testclient import TestClient
import pytest
from requests import Response

from app import models, schemas


@pytest.mark.usefixtures("fixture_data")
class TestApi:
    """
    Functional endpoint tests
    """
    def test_beleidskeuze_valid_view_past_vigerend(self, client: TestClient):
        response = client.get(
            "v0.1/valid/beleidskeuzes?all_filters=Afweging:beleidskeuze1030"
        )
        assert response.status_code == 200, f"Status code was {response.status_code}"
        data = response.json()

        assert (
            len(data) == 0
        ), f"We are expecting nothing as the most recent Vigerend has its Eind_Geldigheid in the past"


    def test_beleidskeuze_valid_view_future_vigerend(self, client: TestClient):
        response = client.get(
            "v0.1/valid/beleidskeuzes?all_filters=Afweging:beleidskeuze1011"
        )
        assert response.status_code == 200, f"Status code was {response.status_code}"
        data = response.json()
        assert len(data) >= 1, f"Expecting at least 1 results"

        expected_uuids = set(
            [
                "FEC2E000-0011-0017-0000-000000000000",  # This is Vigerend and still in current date time range
            ]
        )
        found_uuids = set([r["UUID"] for r in data])
        assert expected_uuids.issubset(
            found_uuids
        ), f"Not all expected uuid where found"

        forbidden_uuids = set(
            [
                "FEC2E000-0011-0011-0000-000000000000",  # first version early status
                "FEC2E000-0011-0021-0000-000000000000",  # second version early status
                "FEC2E000-0011-0027-0000-000000000000",  # New version status Vigerend, but in the future
            ]
        )
        intersect = found_uuids & forbidden_uuids
        assert len(intersect) == 0, f"Some forbidden uuid where found"
