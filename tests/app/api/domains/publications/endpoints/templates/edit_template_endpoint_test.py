from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.tables.publications import PublicationTemplateTable
from tests.conftest import Context
from tests.fixtures.internal.spec.publications import PublicationTemplateSpec
from tests.fixtures.internal.types import Ref


def _payload(**overrides) -> dict:
    payload = {
        "title": "Edited template name",
        "description": "Edited template description",
        "is_active": "0",
        "document_type": "programma",
        "object_types": ["type-1", "type-2"],
        "text_template": """<div>Edited text template</div>""",
        "object_templates": {
            "type-1": "<h1>{{ o.field_1 }}</h1>",
            "type-2": "<h1>Ambitie {{ o.field_2 }}</h1>",
        },
        "object_field_map": {
            "type-1": ["field_1"],
            "type-2": ["field_2"],
        },
    }
    payload.update(overrides)
    return payload


def test_edit_a_template_and_changes_are_persisted_in_db(beheerder: TestClient, session: Session, ctx: Context):
    original: PublicationTemplateSpec = ctx.f.find(Ref(PublicationTemplateSpec, "publication_template_visie_2")).spec
    payload: dict[str, str] = _payload()
    response = beheerder.post(
        f"/publication-templates/{original.id}",
        json=payload,
    )

    assert response.status_code == 200, response.text

    # The template changes are persisted
    row: PublicationTemplateTable | None = session.get(PublicationTemplateTable, original.id)
    assert row is not None
    assert row.title == payload.get("title")
    assert row.description == payload.get("description")
    assert row.is_active == (payload.get("is_active") == "1")
    assert row.document_type == payload.get("document_type")
    assert row.object_types == payload.get("object_types")
    assert row.text_template == payload.get("text_template")
    assert row.object_templates == payload.get("object_templates")
    assert row.object_field_map == payload.get("object_field_map")


def test_edit_a_template_no_updates_exception(beheerder: TestClient, ctx: Context):
    original: PublicationTemplateSpec = ctx.f.find(Ref(PublicationTemplateSpec, "publication_template_visie_2")).spec
    response = beheerder.post(
        f"/publication-templates/{original.id}",
        json={},
    )

    assert response.status_code == 400, response.text
    assert response.json().get("detail") == "Nothing to update"


def test_raises_404_when_template_does_not_exist(beheerder: TestClient, ctx: Context):
    unknown_uuid = "00000000-0000-0000-0000-000000000000"

    response = beheerder.post(f"/publication-templates/{unknown_uuid}")

    assert response.status_code == 404, response.text
