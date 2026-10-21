import pytest
from fastapi.testclient import TestClient

from tests.conftest import Context
from tests.fixtures.internal.spec.publications import (
    PublicationEnvironmentSpec,
)
from tests.fixtures.internal.types import Ref, Spec


def _get_ref(ctx: Context, spec: type[Spec], key: str) -> str:
    return str(ctx.f.primary_key_uuid(Ref(spec, key)))


def test_lists_the_publication_acts(admin: TestClient, ctx: Context):
    env_prod = _get_ref(ctx, PublicationEnvironmentSpec, "publication_environment_prod")
    env_pre = _get_ref(ctx, PublicationEnvironmentSpec, "publication_environment_pre")
    response = admin.get("/publication-acts")

    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["results"]) == 3
    assert {str(e) for e in {env_prod, env_pre}} == {r["environment_id"] for r in body["results"]}
    assert {"omgevingsvisie", "programma"} == {r["document_type"] for r in body["results"]}
    assert {"omgevingsvisie-1", "omgevingsvisie-2", "programma-1"} == {r["work_other"] for r in body["results"]}


@pytest.mark.parametrize(
    "query, expected_work_other_keys",
    [
        pytest.param("is_active=false", ["omgevingsvisie-2"], id="is-active-false"),
        pytest.param(
            "document_type=omgevingsvisie", ["omgevingsvisie-1", "omgevingsvisie-2"], id="document-type-omgevingsvisie"
        ),
        pytest.param("document_type=programma", ["programma-1"], id="document-type-programma"),
    ],
)
def test_filters(
    admin: TestClient,
    ctx: Context,
    query: str,
    expected_work_other_keys: list[str],
):
    response = admin.get(f"/publication-acts?{query}")
    body = response.json()

    assert response.status_code == 200, response.text
    assert expected_work_other_keys == [r["work_other"] for r in body["results"]]
    assert response.json()["total"] == len(expected_work_other_keys)


def test_environment_filter(admin: TestClient, ctx: Context):
    env_prod = _get_ref(ctx, PublicationEnvironmentSpec, "publication_environment_prod")
    response = admin.get(f"/publication-acts?environment_id={env_prod}")

    assert response.status_code == 200, response.text
    body = response.json()
    assert {str(env_prod)} == {r["environment_id"] for r in body["results"]}
    assert len(body["results"]) == 2
