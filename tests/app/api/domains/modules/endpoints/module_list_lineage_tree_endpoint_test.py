from fastapi.testclient import TestClient

from tests.conftest import Context


def test_lists_all_versions_of_the_lineage_latest_first(admin: TestClient, ctx: Context):
    response = admin.get("/modules/1/object/beleidsdoel/1")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] == 3
    assert [r["title"] for r in body["results"]] == [
        "Changed the titel via Module 1 again!",
        "Changed the titel via Module 1",
        "Beleidsdoel 1 from march",
    ]
    assert {r["code"] for r in body["results"]} == {"beleidsdoel-1"}
