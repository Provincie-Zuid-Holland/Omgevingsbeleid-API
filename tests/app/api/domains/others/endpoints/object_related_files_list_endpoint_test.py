from typing import List

from fastapi.testclient import TestClient

from app.api.domains.others.types import ObjectRelatedFileResponse
from tests.conftest import Context
from tests.fixtures.internal.spec.object_related_file_spec import ObjectRelatedFileSpec
from tests.fixtures.internal.types import Ref


def _uuids(ctx: Context, keys: List[str]) -> List[str]:
    return [str(ctx.f.primary_key_uuid(Ref(ObjectRelatedFileSpec, key))) for key in keys]


def test_lists_the_files_of_the_requested_lineage_newest_first(client: TestClient, ctx: Context):
    response = client.get("/beleidsdoel/1/object-related-files")

    assert response.status_code == 200
    assert [r["UUID"] for r in response.json()] == _uuids(ctx, ["bd1_file2", "bd1_file1"])


def test_files_of_another_lineage_are_listed_separately(client: TestClient, ctx: Context):
    results = client.get("/beleidsdoel/2/object-related-files").json()

    assert [r["UUID"] for r in results] == _uuids(ctx, ["bd2_file1"])


def test_lineage_without_files_returns_an_empty_list(client: TestClient):
    response = client.get("/beleidsdoel/3/object-related-files")

    assert response.status_code == 200
    assert response.json() == []


def test_unknown_lineage_returns_404(client: TestClient):
    response = client.get("/beleidsdoel/999999/object-related-files")

    assert response.status_code == 404
    assert response.json()["detail"] == "Object niet gevonden"


def test_results_match_the_response_model_shape(client: TestClient, ctx: Context):
    expected: ObjectRelatedFileSpec = ctx.f.find(Ref(ObjectRelatedFileSpec, "bd1_file1")).spec

    results = {r["UUID"]: r for r in client.get("/beleidsdoel/1/object-related-files").json()}
    result = results[str(expected.UUID)]

    assert set(result.keys()) == set(ObjectRelatedFileResponse.model_fields)
    assert result["Code"] == expected.Code
    assert result["Title"] == expected.Title
