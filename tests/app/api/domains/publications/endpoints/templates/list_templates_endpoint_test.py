from fastapi.testclient import TestClient

from tests.assert_helpers import get_uuids_from_spec
from tests.conftest import Context
from tests.fixtures.internal.spec.publications import PublicationTemplateSpec


def test_lists_the_templates_newest_first(admin: TestClient, ctx: Context):
    response = admin.get("/publication-templates")

    assert response.status_code == 200
    assert [r["id"] for r in response.json().get("results")] == get_uuids_from_spec(
        ctx,
        PublicationTemplateSpec,
        [
            "publication_template_visie_2",
            "publication_template_programma_2",
            "publication_template_visie_1",
            "publication_template_programma_1",
        ],
    )


def test_lists_the_templates_newest_first_filter_is_active(admin: TestClient, ctx: Context):
    response = admin.get("/publication-templates?is_active=1")

    assert response.status_code == 200
    assert [r["id"] for r in response.json().get("results")] == get_uuids_from_spec(
        ctx,
        PublicationTemplateSpec,
        [
            "publication_template_visie_2",
            "publication_template_programma_2",
        ],
    )


def test_lists_the_templates_newest_first_filter_document_type_programma(admin: TestClient, ctx: Context):
    response = admin.get("/publication-templates?document_type=programma")

    assert response.status_code == 200
    assert [r["id"] for r in response.json().get("results")] == get_uuids_from_spec(
        ctx,
        PublicationTemplateSpec,
        [
            "publication_template_programma_2",
            "publication_template_programma_1",
        ],
    )
