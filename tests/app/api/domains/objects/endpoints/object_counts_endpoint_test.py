import httpx2

from tests.conftest import Context


async def test_returns_object_valid_count_for_logged_in_ambtenaar(ambtenaar: httpx2.AsyncClient, ctx: Context):
    response = await ambtenaar.get("/objects/valid/count")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body == [
        {"count": 2, "object_type": "beleidsdoel"},
        {"count": 4, "object_type": "beleidskeuze"},
        {"count": 3, "object_type": "gebied"},
        {"count": 1, "object_type": "gebiedengroep"},
        {"count": 3, "object_type": "gebiedsaanwijzing"},
        {"count": 5, "object_type": "maatregel"},
        {"count": 1, "object_type": "verplicht_programma"},
    ]


async def test_returns_object_valid_count_for_logged_in_admin(admin: httpx2.AsyncClient, ctx: Context):
    response = await admin.get("/objects/valid/count")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body == []
