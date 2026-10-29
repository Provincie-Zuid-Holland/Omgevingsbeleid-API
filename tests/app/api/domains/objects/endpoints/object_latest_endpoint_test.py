import httpx2
import pytest

from tests.conftest import Context
from tests.fixtures.internal.spec.objects import BeleidsdoelSpec, BeleidskeuzeSpec, MaatregelSpec
from tests.fixtures.internal.types import Ref


@pytest.mark.parametrize(
    "prefix, ref",
    [
        pytest.param("/beleidsdoelen", Ref(BeleidsdoelSpec, "beleidsdoel_1_latest_valid"), id="beleidsdoel-1"),
        pytest.param("/beleidsdoelen", Ref(BeleidsdoelSpec, "beleidsdoel_2_latest_valid"), id="beleidsdoel-2"),
        pytest.param("/beleidskeuzes", Ref(BeleidskeuzeSpec, "beleidskeuze_1_latest_valid"), id="beleidskeuze-1"),
        pytest.param("/maatregelen", Ref(MaatregelSpec, "maatregel_1_latest_valid"), id="maatregel-1"),
    ],
)
async def test_object_latest_returns_most_recent_version(
    client: httpx2.AsyncClient, ctx: Context, prefix: str, ref: Ref
):
    expected = ctx.f.find(ref).spec

    response = await client.get(f"{prefix}/latest/{expected.object_id}")
    assert response.status_code == 200, response.text

    body = response.json()
    assert body["id"] == str(expected.id)
    assert body["next_version"] is None


@pytest.mark.parametrize("prefix", ["/beleidsdoelen", "/beleidskeuzes", "/maatregelen"])
async def test_object_latest_unknown_lineage_returns_404(client: httpx2.AsyncClient, prefix: str):
    response = await client.get(f"{prefix}/latest/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "lineage_id does not exist"


async def test_object_latest_is_scoped_to_object_type(client: httpx2.AsyncClient):
    assert (await client.get("/maatregelen/latest/1")).status_code == 200
    assert (await client.get("/beleidsdoelen/latest/999999")).status_code == 404
