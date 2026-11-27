import json

import httpx2

from tests.conftest import Context
from tests.fixtures.internal.spec.publications import (
    PublicationActSpec,
)
from tests.fixtures.internal.types import Ref


async def test_details_the_publication_act(admin: httpx2.AsyncClient, ctx: Context):
    act_visie = ctx.f.find(Ref(PublicationActSpec, "publication_act_visie"))
    response = await admin.get(f"/publication-acts/{act_visie.spec.id}")

    assert response.status_code == 200, response.text
    body = json.loads(response.text)
    assert body["title"] == "Omgevingsvisie Zuid-Holland"
    assert body["document_type"] == "omgevingsvisie"
    assert body["work_other"] == "omgevingsvisie-1"
    assert body["environment"]["title"] == "Productie"
