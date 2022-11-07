
from fastapi.testclient import TestClient
import pytest
from app.schemas import AmbitieCreate, BelangCreate, BeleidskeuzeCreate
from app.tests.utils.mock_data import generate_data


@pytest.mark.usefixtures("fixture_data")
class TestGraphService:
    """
    Functional endpoint tests to verify expected results
    of graph service requests.
    """

    def test_graph_normal(self, client: TestClient, admin_headers):
        # Create Ambitie
        test_amb = generate_data(AmbitieCreate)
        test_amb["Eind_Geldigheid"] = "2992-11-23T10:00:00"
        amb_resp = client.post("v0.1/ambities", headers=admin_headers, json=test_amb)
        amb_UUID = amb_resp.json()["UUID"]

        # Create Belang
        test_belang = generate_data(BelangCreate)
        test_belang["Eind_Geldigheid"] = "2992-11-23T10:00:00"
        belang_resp = client.post(
            "v0.1/belangen", headers=admin_headers, json=test_belang
        )
        belang_UUID = belang_resp.json()["UUID"]

        # Create Belang that is not valid anymore
        test_belang = generate_data(BelangCreate)
        test_belang["Eind_Geldigheid"] = "1992-11-23T10:00:00"
        belang_resp = client.post(
            "v0.1/belangen", headers=admin_headers, json=test_belang
        )
        invalid_belang_UUID = belang_resp.json()["UUID"]

        # Create beleidskeuze (add objects)
        test_bk = generate_data(BeleidskeuzeCreate)
        test_bk["Eind_Geldigheid"] = "2992-11-23T10:00:00"
        test_bk["Ambities"] = [{"UUID": amb_UUID, "Koppeling_Omschrijving": ""}]
        test_bk["Belangen"] = [
            {"UUID": belang_UUID, "Koppeling_Omschrijving": ""},
            {"UUID": invalid_belang_UUID, "Koppeling_Omschrijving": ""},
        ]
        test_bk["Status"] = "Vigerend"
        response = client.post(
            "v0.1/beleidskeuzes", headers=admin_headers, json=test_bk
        )
        bk_uuid = response.json()["UUID"]

        # Assert
        response = client.get("v0.1/graph", headers=admin_headers)
        graph_links = response.json()["links"]
        graph_nodes = response.json()["nodes"]
        found_links = []

        for link in graph_links:
            if link["source"] == bk_uuid:
                found_links.append(link["target"])

        assert not invalid_belang_UUID in found_links, "Invalid belang retrieved"
        assert len(found_links) == 2, "Not all links retrieved"
        assert belang_UUID in found_links, "Belang not retrieved"
        assert amb_UUID in found_links, "Ambitie not retrieved"
        assert set([amb_UUID, belang_UUID]) == set(
            found_links
        ), "Unexpected result for links"

    def test_leden_excluded_from_graph(
        self, client: TestClient, admin_headers, fixture_data
    ):
        _link_to3 = {
            "source": fixture_data._instances["keu:6"].UUID,
            "target": fixture_data._instances["ver:3"].UUID,
            "type": "Koppeling",
        }

        _link_to2 = {
            "source": fixture_data._instances["keu:6"].UUID,
            "target": fixture_data._instances["ver:2"].UUID,
            "type": "Koppeling",
        }

        response = client.get(url="v0.1/graph", headers=admin_headers)

        node_uuids = map(lambda node: node["UUID"], response.json()["nodes"])
        links = response.json()["links"]
        # This is the source beleidskeuze
        assert fixture_data._instances["keu:6"].UUID in node_uuids

        # This one should show up (it has Type==Artikel)
        assert fixture_data._instances["ver:3"].UUID in node_uuids
        assert _link_to3 in links

        # This one should not show up (it has Type==Lid)
        assert fixture_data._instances["ver:2"].UUID not in node_uuids
        assert _link_to2 not in links
