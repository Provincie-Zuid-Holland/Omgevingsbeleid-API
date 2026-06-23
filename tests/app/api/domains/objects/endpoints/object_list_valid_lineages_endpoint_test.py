import pytest
from fastapi.testclient import TestClient

from tests.conftest import Context
from tests.fixtures.internal.spec.objects import BeleidsdoelSpec, BeleidskeuzeSpec, MaatregelSpec
from tests.fixtures.internal.types import Ref


@pytest.mark.parametrize(
    "prefix, ref",
    [
        pytest.param("/beleidsdoelen", Ref(BeleidsdoelSpec, "beleidsdoel_1_latest_valid"), id="beleidsdoel"),
        pytest.param("/beleidskeuzes", Ref(BeleidskeuzeSpec, "beleidskeuze_1_latest_valid"), id="beleidskeuze"),
        pytest.param("/maatregelen", Ref(MaatregelSpec, "maatregel_1_latest_valid"), id="maatregel"),
    ],
)
def test_lineage_resolves_to_latest_valid_version(client: TestClient, ctx: Context, prefix: str, ref: Ref):
    expected = ctx.f.find(ref).spec

    results = {r["Code"]: r for r in client.get(f"{prefix}/valid").json()["results"]}

    assert results[expected.Code]["UUID"] == str(expected.UUID)
