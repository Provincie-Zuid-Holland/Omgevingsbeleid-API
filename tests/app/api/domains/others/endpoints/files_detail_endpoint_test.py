import uuid

import pytest
from fastapi.testclient import TestClient

from app.api.domains.others.types import StorageFileBasic
from tests.conftest import Context
from tests.fixtures.internal.spec.storage_file_spec import StorageFileSpec
from tests.fixtures.internal.types import Ref


@pytest.mark.parametrize("client_fixture", ["admin", "ambtenaar"])
@pytest.mark.parametrize("file_key", ["file_1", "file_2", "file_3"])
def test_returns_the_requested_storage_file(
    request: pytest.FixtureRequest, ctx: Context, client_fixture: str, file_key: str
):
    client: TestClient = request.getfixturevalue(client_fixture)
    expected: StorageFileSpec = ctx.f.find(Ref(StorageFileSpec, file_key)).spec

    response = client.get(f"/storage-files/{expected.UUID}")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["UUID"] == str(expected.UUID)
    assert body["Checksum"] == expected.Checksum
    assert body["Filename"] == expected.Filename
    assert body["Content_Type"] == expected.Content_Type
    assert body["Size"] == expected.Size
    assert body["Created_By_UUID"] == str(expected.Created_By_UUID)


def test_response_matches_the_storage_file_model_shape(admin: TestClient, ctx: Context):
    document_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(StorageFileSpec, "file_1"))

    body: dict = admin.get(f"/storage-files/{document_uuid}").json()

    assert set(body.keys()) == set(StorageFileBasic.model_fields)


def test_unknown_uuid_returns_404(admin: TestClient):
    response = admin.get("/storage-files/00000000-0000-0000-0000-00000000dead")

    assert response.status_code == 404
    assert response.json()["detail"] == "Storage file niet gevonden"


def test_unauthenticated_returns_401(client: TestClient, ctx: Context):
    document_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(StorageFileSpec, "file_1"))

    response = client.get(f"/storage-files/{document_uuid}")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
