import uuid

import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    "prefix, object_type, lineage_id, expected_title",
    [
        pytest.param("/beleidsdoelen", "beleidsdoel", 1, "Beleidsdoel 1 from march", id="beleidsdoel"),
        pytest.param("/beleidsdoelen", "beleidsdoel", 2, "Beleidsdoel 2 from march", id="beleidsdoel"),
        pytest.param("/beleidskeuzes", "beleidskeuze", 1, "Beleidskeuze 1 from march", id="beleidskeuze"),
        pytest.param("/maatregelen", "maatregel", 1, "Maatregel 1 from march", id="maatregel"),
    ],
)
def test_object_latest_returns_most_recent_version(
    client: TestClient, prefix: str, object_type: str, lineage_id: int, expected_title: str
):
    response = client.get(f"{prefix}/latest/{lineage_id}")
    assert response.status_code == 200, response.text

    body = response.json()
    assert body["Object_ID"] == lineage_id
    assert body["Code"] == f"{object_type}-{lineage_id}"
    assert body["Title"] == expected_title
    assert body["Modified_Date"].startswith("2025-03-01")
    assert body["Start_Validity"].startswith("2025-03-01")
    assert body["End_Validity"] is None
    uuid.UUID(body["UUID"])
    assert body["Next_Version"] is None


@pytest.mark.parametrize("prefix", ["/beleidsdoelen", "/beleidskeuzes", "/maatregelen"])
def test_object_latest_unknown_lineage_returns_404(client: TestClient, prefix: str):
    response = client.get(f"{prefix}/latest/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "lineage_id does not exist"


def test_object_latest_is_scoped_to_object_type(client: TestClient):
    # maatregel has lineage 6; beleidsdoel only has 1-3.
    assert client.get("/maatregelen/latest/6").status_code == 200
    assert client.get("/beleidsdoelen/latest/6").status_code == 404
