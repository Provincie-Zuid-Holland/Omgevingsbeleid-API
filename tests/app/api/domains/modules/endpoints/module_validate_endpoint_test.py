from fastapi.testclient import TestClient

from tests.conftest import Context


def test_validates_the_module(admin: TestClient, ctx: Context):
    response = admin.get("/modules/1/validate")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "OK"
    assert len(body["errors"]) == 0


def test_validates_the_module_with_error(admin: TestClient, ctx: Context):
    response = admin.get("/modules/7/validate")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "Failed"
    assert len(body["errors"]) == 1
    assert body["errors"][0]["rule"] == "required_object_fields_rule"
    assert body["errors"][0]["object"] == {
        "code": "beleidsdoel-7",
        "object_id": 7,
        "object_type": "beleidsdoel",
        "title": "",
    }
