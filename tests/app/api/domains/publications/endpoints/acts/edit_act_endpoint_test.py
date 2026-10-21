import uuid

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


def test_edits_the_publication_act(admin: TestClient, ctx: Context):
    act_visie = ctx.f.find(Ref(PublicationActSpec, "publication_act_visie"))
    title: str = "Edited title"
    subjects: list[str] = ["bodem", "water"]
    response = admin.post(
        f"/publication-acts/{act_visie.spec.uuid}", json={"title": title, "meta_data": {"subjects": subjects}}
    )

    assert response.status_code == 200, response.text

    act_edited = _act(ctx.session, act_visie.spec.uuid)
    assert act_edited
    assert act_edited.title == title
    assert act_edited.meta_data["subjects"] == subjects


def test_edits_the_publication_act_no_updates(admin: TestClient, ctx: Context):
    act_visie = ctx.f.find(Ref(PublicationActSpec, "publication_act_visie"))
    response = admin.post(f"/publication-acts/{act_visie.spec.uuid}", json={})

    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "Nothing to update"
