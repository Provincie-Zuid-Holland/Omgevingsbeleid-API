from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from freezegun import freeze_time
from sqlalchemy.orm.session import Session

from app.db.base_class import NULL_UUID
from app.tests.utils.data_loader import FixtureLoader
import pytest


@pytest.mark.usefixtures("fixture_data")
class TestValidSelection:
    """
    Functional endpoint tests to verify expected results
    when requesting 'Valid' objects.
    """

    @freeze_time("2022-10-10")
    def test_generic_valid_view(self, client: TestClient, db: Session):
        """
        Insert valid objects and ensure generic valid filters
        are applied correctly. Ambitie used as example.
        """
        # Arrange
        valid = {
            "UUID": uuid4(),
            "ID": 999,
            "Titel": "valid test ambitie",
            "Omschrijving": "dit is een valid ambitie",
            "Begin_Geldigheid": "2020-10-10T09:57:05.054Z",
            "Eind_Geldigheid": "2030-10-10T09:57:05.054Z",
        }
        invalid = {
            "UUID": uuid4(),
            "ID": 998,
            "Titel": "verlopen valid test ambitie",
            "Omschrijving": "verlopen valid ambitie",
            "Begin_Geldigheid": "2020-10-10T09:57:05.054Z",
            "Eind_Geldigheid": "2021-09-09T09:57:05.054Z",  # Expired
        }

        for amb in [valid, invalid]:
            fl = FixtureLoader(db)
            fl._ambitie("amb:water", **amb)
            db.commit()

        # Act
        response = client.get("v0.1/valid/ambities?limit=-1")
        assert response.status_code == 200, f"Status code was {response.status_code}"

        # Assert
        data = response.json()

        response_uuids = [UUID(amb["UUID"]) for amb in data]

        assert (
            valid["UUID"] in response_uuids
        ), f"Expected valid {valid['UUID']} to be in response"
        assert (
            str(invalid["UUID"]) not in response_uuids
        ), f"Expected invalid {valid['UUID']} not in response"

    def test_no_null_records(self, client: TestClient):
        response = client.get("v0.1/valid/ambities?limit=-1")
        assert response.status_code == 200, f"Status code was {response.status_code}"
        data = response.json()

        for item in data:
            assert item["UUID"] != NULL_UUID

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
