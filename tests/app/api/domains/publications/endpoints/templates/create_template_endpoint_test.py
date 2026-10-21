import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.tables.publications import PublicationTemplateTable


def _payload(**overrides) -> dict:
    payload = {
        "title": "New template name",
        "description": "New template description",
        "is_active": "1",
        "document_type": "omgevingsvisie",
        "object_types": ["visie_algemeen", "ambitie"],
        "text_template": """<div>Template contents</div>""",
        "object_templates": {
            "visie_algemeen": "<h1>{{ o.title }}</h1>",
            "ambitie": "<h1>Ambitie {{ o.description }}</h1>",
        },
        "object_field_map": {
            "visie_algemeen": ["title"],
            "ambitie": ["description"],
        },
    }
    payload.update(overrides)
    return payload


def test_creates_a_template_and_it_is_persisted_in_db(admin: TestClient, session: Session):
    payload: dict[str, str] = _payload()
    response = admin.post(
        "/publication-templates",
        json=payload,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    created_uuid = uuid.UUID(body["id"])

    # The publication template is persisted
    row: PublicationTemplateTable | None = session.get(PublicationTemplateTable, created_uuid)
    assert row is not None
    assert row.title == payload.get("title")
    assert row.description == payload.get("description")
    assert row.is_active == (payload.get("is_active") == "1")
    assert row.document_type == payload.get("document_type")
    assert row.object_types == payload.get("object_types")
    assert row.text_template == payload.get("text_template")
    assert row.object_templates == payload.get("object_templates")
    assert row.object_field_map == payload.get("object_field_map")
