import json

from fastapi.testclient import TestClient

from tests.conftest import Context
from tests.fixtures.internal.spec.publications import (
    PublicationActSpec,
)
from tests.fixtures.internal.types import Ref


def test_details_the_publication_act(admin: TestClient, ctx: Context):
    act_visie = ctx.f.find(Ref(PublicationActSpec, "publication_act_visie"))
    response = admin.get(f"/publication-acts/{act_visie.spec.uuid}")

    assert response.status_code == 200, response.text
    body = json.loads(response.text)
    assert body["title"] == "Omgevingsvisie Zuid-Holland"
    assert body["document_type"] == "omgevingsvisie"
    assert body["work_other"] == "omgevingsvisie-1"
    assert body["environment"]["title"] == "Productie"
