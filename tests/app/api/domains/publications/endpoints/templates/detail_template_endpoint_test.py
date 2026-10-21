import pytest
from fastapi.testclient import TestClient

from tests.conftest import Context
from tests.fixtures.internal.spec.publications import PublicationTemplateSpec
from tests.fixtures.internal.types import Ref


@pytest.mark.parametrize("template_key", ["publication_template_visie_2", "publication_template_programma_2"])
def test_returns_the_requested_template(beheerder: TestClient, ctx: Context, template_key: str):
    expected: PublicationTemplateSpec = ctx.f.find(Ref(PublicationTemplateSpec, template_key)).spec

    response = beheerder.get(f"/publication-templates/{expected.id}")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == str(expected.id)
    assert body["title"] == expected.title
    assert body["description"] == expected.description
    assert (body["is_active"] == 1) == expected.is_active
    assert body["document_type"] == expected.document_type
    assert body["object_types"] == expected.object_types
    assert body["text_template"] == expected.text_template
    assert body["object_templates"] == expected.object_templates
    assert body["object_field_map"] == expected.object_field_map


def test_raises_404_when_template_does_not_exist(beheerder: TestClient, ctx: Context):
    unknown_id = "00000000-0000-0000-0000-000000000000"

    response = beheerder.get(f"/publication-templates/{unknown_id}")

    assert response.status_code == 404, response.text
