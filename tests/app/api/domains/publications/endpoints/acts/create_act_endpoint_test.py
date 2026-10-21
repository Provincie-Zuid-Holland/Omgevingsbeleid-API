import uuid

from fastapi.testclient import TestClient
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.tables.publications import PublicationActTable
from tests.conftest import Context
from tests.fixtures.internal.spec.publications import (
    PublicationEnvironmentSpec,
)
from tests.fixtures.internal.types import Ref


def _latest_act(session: Session) -> PublicationActTable | None:
    return session.scalar(select(PublicationActTable).order_by(desc(PublicationActTable.modified_date)))


def _payload(
    title: str, environment_id: uuid.UUID, package_type: str = "validation", document_type: str = "omgevingsvisie"
) -> dict[str, str]:
    return {
        "title": title,
        "package_type": package_type,
        "document_type": document_type,
        "environment_id": str(environment_id),
    }


def test_creates_the_publication_act(admin: TestClient, ctx: Context):
    env_prod: uuid.UUID = ctx.f.primary_key_uuid(Ref(PublicationEnvironmentSpec, "publication_environment_prod"))
    response = admin.post("/publication-acts", json=_payload("New act", env_prod))

    assert response.status_code == 200, response.text

    act_latest = _latest_act(ctx.session)
    assert act_latest
    assert str(act_latest.uuid) == response.json()["uuid"]
    assert act_latest.work_other == "omgevingsvisie-3"


def test_creates_the_publication_act_unknown_environment(admin: TestClient, ctx: Context):
    response = admin.post(
        "/publication-acts", json=_payload("New act", uuid.UUID("00000000-0000-0000-0000-000000000000"))
    )

    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "Publication Environment niet gevonden"


def test_creates_the_publication_act_inactive_environment(admin: TestClient, ctx: Context):
    env_inactive: uuid.UUID = ctx.f.primary_key_uuid(
        Ref(PublicationEnvironmentSpec, "publication_environment_inactive")
    )
    response = admin.post("/publication-acts", json=_payload("New act", env_inactive))

    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "Publication Environment is in actief"
