import pytest
from fastapi.testclient import TestClient

from tests.conftest import Context
from tests.fixtures.internal.spec.publications import (
    PublicationActPackageSpec,
    PublicationAnnouncementPackageSpec,
    PublicationEnvironmentSpec,
)
from tests.fixtures.internal.types import Ref, Spec


def _get_ref(ctx: Context, spec: type[Spec], key: str) -> str:
    return str(ctx.f.primary_key_uuid(Ref(spec, key)))


def test_lists_the_unified_packages(admin: TestClient, ctx: Context):
    env_prod = _get_ref(ctx, PublicationEnvironmentSpec, "publication_environment_prod")
    env_pre = _get_ref(ctx, PublicationEnvironmentSpec, "publication_environment_pre")

    response = admin.get("/publication-packages")

    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["results"]) == 4
    assert {str(e) for e in {env_prod, env_pre}} == {r["environment_id"] for r in body["results"]}
    assert {"omgevingsvisie", "programma"} == {r["document_type"] for r in body["results"]}
    assert {1, 4} == {r["module_id"] for r in body["results"]}


@pytest.mark.parametrize(
    "query, expected_act_keys, expected_announcement_keys",
    [
        pytest.param(
            "publication_type=act",
            ["act_package_programma_validation", "act_package_visie_publication", "act_package_visie_validation"],
            [],
            id="publication_type-act",
        ),
        pytest.param(
            "publication_type=announcement",
            [],
            ["announcement_package_visie_publication"],
            id="publication_type-announcement",
        ),
        pytest.param(
            "module_id=4",
            ["act_package_programma_validation"],
            [],
            id="module_id",
        ),
        pytest.param(
            "report_status=valid",
            ["act_package_visie_publication", "act_package_visie_validation"],
            [],
            id="report_status",
        ),
        pytest.param(
            "package_type=publication",
            ["act_package_visie_publication"],
            ["announcement_package_visie_publication"],
            id="package_type",
        ),
        pytest.param(
            "document_type=omgevingsvisie",
            ["act_package_visie_publication", "act_package_visie_validation"],
            ["announcement_package_visie_publication"],
            id="document_type",
        ),
        pytest.param(
            "publication_type=act&package_type=validation&document_type=omgevingsvisie",
            ["act_package_visie_validation"],
            [],
            id="combined",
        ),
        pytest.param(
            "module_id=999999",
            [],
            [],
            id="no-match",
        ),
    ],
)
def test_filters(
    admin: TestClient,
    ctx: Context,
    query: str,
    expected_act_keys: list[str],
    expected_announcement_keys: list[str],
):
    response = admin.get(f"/publication-packages?{query}")

    assert response.status_code == 200, response.text
    expected = {_get_ref(ctx, PublicationActPackageSpec, k) for k in expected_act_keys} | {
        _get_ref(ctx, PublicationAnnouncementPackageSpec, k) for k in expected_announcement_keys
    }
    assert expected == {r["id"] for r in response.json()["results"]}
    assert response.json()["total"] == len(expected)


def test_environment_filter(admin: TestClient, ctx: Context):
    env_prod = _get_ref(ctx, PublicationEnvironmentSpec, "publication_environment_prod")
    response = admin.get(f"/publication-packages?environment_id={env_prod}")

    assert response.status_code == 200, response.text
    body = response.json()
    assert {str(env_prod)} == {r["environment_id"] for r in body["results"]}
