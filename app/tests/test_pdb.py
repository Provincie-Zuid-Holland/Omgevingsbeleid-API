from fastapi.testclient import TestClient
import pytest


@pytest.mark.usefixtures("fixture_data")
class TestPDB:
    """
    development test to open PDB in testing envs
    """

    def test_pdb(self, client: TestClient):
        filter_params = {"Afweging": "beleidskeuze1030"}
        response = client.get("v0.1/valid/beleidskeuzes?limit=-1")
        json = response.json()
        assert len(json) != 29
