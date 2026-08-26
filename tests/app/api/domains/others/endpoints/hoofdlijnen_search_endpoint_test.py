from fastapi.testclient import TestClient

from app.api.domains.others.types import Hoofdlijn
from tests.conftest import Context
from tests.fixtures.internal.spec.hoofdlijn_spec import HoofdlijnSpec
from tests.fixtures.internal.types import Ref


def test_search_hoofdlijn(viewer: TestClient, ctx: Context):
    response = viewer.post("/hoofdlijnen/search?query=vin")

    assert response.status_code == 200, response.text
    
    response_body = response.json()

    assert len(response_body.get("results")) == 1
    actual: Hoofdlijn = Hoofdlijn.model_validate(response_body.get("results")[0])
    expected_spec: HoofdlijnSpec = ctx.f.find(Ref(HoofdlijnSpec, "hoofdlijn-2")).spec
    expected = Hoofdlijn.model_validate(expected_spec)
    assert actual == expected
