from fastapi.testclient import TestClient


def test_lists_only_open_modules_with_a_public_latest_status(client: TestClient):
    # Module 1 is Ter Inzage and module 8 is Vastgesteld.
    # Module 3 is closed and the others have a non-public latest status.
    response = client.get("/revisions")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] == 2
    assert [m["module_id"] for m in body["results"]] == [8, 1]
