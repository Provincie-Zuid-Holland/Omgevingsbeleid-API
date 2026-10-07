from fastapi.testclient import TestClient

from tests.conftest import Context


def test_returns_object_static(ambtenaar: TestClient, ctx: Context):
    response = ambtenaar.get("/objects/valid/count")
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


def test_returns_object_static_admin(admin: TestClient, ctx: Context):
    response = admin.get("/objects/valid/count")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body == []
