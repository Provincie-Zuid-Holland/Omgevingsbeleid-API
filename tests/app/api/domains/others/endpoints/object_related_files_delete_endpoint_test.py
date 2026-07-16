import uuid

import pytest
from fastapi.testclient import TestClient
from pytest import FixtureRequest

from tests.conftest import Context
from tests.fixtures.internal.spec.object_related_file_spec import ObjectRelatedFileSpec
from tests.fixtures.internal.types import Ref


def test_deletes_a_file_and_it_no_longer_appears_in_the_list(admin: TestClient, ctx: Context):
    file_uuid = ctx.f.primary_key_uuid(Ref(ObjectRelatedFileSpec, "bd1_file1"))

    response = admin.delete(
        "/beleidsdoel/1/object-related-files/delete", params={"related_file_uuid": str(file_uuid)}
    )

    assert response.status_code == 200, response.text
    assert response.json()["message"] == "OK"

    listed = admin.get("/beleidsdoel/1/object-related-files").json()
    assert str(file_uuid) not in [r["UUID"] for r in listed]


def test_unknown_uuid_returns_404(admin: TestClient):
    response = admin.delete(
        "/beleidsdoel/1/object-related-files/delete", params={"related_file_uuid": str(uuid.uuid4())}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Bestand niet gevonden"


@pytest.mark.parametrize(
    "client_fixture, expected_status, expected_detail",
    [
        pytest.param("client", 401, "Not authenticated", id="unauthenticated"),
        pytest.param("ambtenaar", 401, "Invalid user role", id="role-without-permission"),
        pytest.param("owner_1", 200, None, id="owner-via-whitelist"),
        pytest.param("admin", 200, None, id="role-with-permission"),
    ],
)
def test_delete_permission_matrix(
    request: FixtureRequest, ctx: Context, client_fixture: str, expected_status: int, expected_detail: str
):
    test_client: TestClient = request.getfixturevalue(client_fixture)
    file_uuid = ctx.f.primary_key_uuid(Ref(ObjectRelatedFileSpec, "bd1_file1"))

    response = test_client.delete(
        "/beleidsdoel/1/object-related-files/delete", params={"related_file_uuid": str(file_uuid)}
    )

    assert response.status_code == expected_status, response.text
    if expected_detail is not None:
        assert response.json()["detail"] == expected_detail
