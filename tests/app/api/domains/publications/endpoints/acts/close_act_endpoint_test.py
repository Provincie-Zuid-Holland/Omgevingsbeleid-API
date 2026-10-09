import uuid
from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.tables.publications import PublicationActTable
from tests.conftest import Context
from tests.fixtures.internal.spec.publications import (
    PublicationActSpec,
)
from tests.fixtures.internal.types import Ref


def _act(session: Session, act_uuid: uuid.UUID) -> PublicationActTable | None:
    return session.scalar(select(PublicationActTable).where(PublicationActTable.uuid == act_uuid))


def test_closes_the_publication_act(admin: TestClient, ctx: Context):
    act_visie = ctx.f.find(Ref(PublicationActSpec, "publication_act_visie"))
    response = admin.post(f"/publication-acts/{act_visie.spec.uuid}/close")

    assert response.status_code == 200, response.text
    assert response.json()["message"] == "OK"

    act_updated = _act(ctx.session, act_visie.spec.uuid)
    assert act_updated
    assert act_updated.is_active is False
    assert act_updated.modified_date.replace(tzinfo=UTC) == datetime(2026, 1, 1, tzinfo=UTC)
