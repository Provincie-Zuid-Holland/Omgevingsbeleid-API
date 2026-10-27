import httpx2

from tests.conftest import Context


async def test_validates_the_module(admin: httpx2.AsyncClient, ctx: Context):
    response = await admin.get("/modules/1/validate")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "OK"
    assert len(body["errors"]) == 0


async def test_validates_the_module_with_error(admin: httpx2.AsyncClient, ctx: Context):
    response = await admin.get("/modules/7/validate")
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
