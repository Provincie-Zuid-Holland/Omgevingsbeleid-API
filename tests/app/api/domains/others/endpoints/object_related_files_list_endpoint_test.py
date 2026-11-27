import httpx2

from app.api.domains.others.types import ObjectRelatedFileResponse
from tests.assert_helpers import get_uuids_from_spec
from tests.conftest import Context
from tests.fixtures.internal.spec.object_related_file_spec import ObjectRelatedFileSpec
from tests.fixtures.internal.types import Ref


async def test_lists_the_files_of_the_requested_lineage_newest_first(client: httpx2.AsyncClient, ctx: Context):
    response = await client.get("/beleidsdoel/1/object-related-files")

    assert response.status_code == 200
    assert [r["id"] for r in response.json()] == get_uuids_from_spec(
        ctx, ObjectRelatedFileSpec, ["bd1_file2", "bd1_file1"]
    )


async def test_files_of_another_lineage_are_listed_separately(client: httpx2.AsyncClient, ctx: Context):
    results = (await client.get("/beleidsdoel/2/object-related-files")).json()

    assert [r["id"] for r in results] == get_uuids_from_spec(ctx, ObjectRelatedFileSpec, ["bd2_file1"])


async def test_lineage_without_files_returns_an_empty_list(client: httpx2.AsyncClient):
    response = await client.get("/beleidsdoel/3/object-related-files")

    assert response.status_code == 200
    assert response.json() == []


async def test_unknown_lineage_returns_404(client: httpx2.AsyncClient):
    response = await client.get("/beleidsdoel/999999/object-related-files")

    assert response.status_code == 404
    assert response.json()["detail"] == "Object niet gevonden"


async def test_results_match_the_response_model_shape(client: httpx2.AsyncClient, ctx: Context):
    expected: ObjectRelatedFileSpec = ctx.f.find(Ref(ObjectRelatedFileSpec, "bd1_file1")).spec

    results = {r["id"]: r for r in (await client.get("/beleidsdoel/1/object-related-files")).json()}
    result = results[str(expected.id)]

    assert set(result.keys()) == set(ObjectRelatedFileResponse.model_fields)
    assert result["code"] == expected.code
    assert result["title"] == expected.title
