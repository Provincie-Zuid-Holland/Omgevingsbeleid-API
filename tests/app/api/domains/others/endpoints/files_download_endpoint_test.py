import uuid

import pytest
from fastapi.testclient import TestClient

from tests.conftest import Context
from tests.fixtures.internal.spec.storage_file_spec import StorageFileSpec
from tests.fixtures.internal.types import Ref


@pytest.mark.parametrize("client_fixture", ["admin", "ambtenaar"])
@pytest.mark.parametrize("file_key", ["file_1", "file_2", "file_3"])
def test_downloads_the_requested_storage_file(
    request: pytest.FixtureRequest, ctx: Context, client_fixture: str, file_key: str
):
    client: TestClient = request.getfixturevalue(client_fixture)
    expected: StorageFileSpec = ctx.f.find(Ref(StorageFileSpec, file_key)).spec

    response = client.get(f"/storage-files/{expected.UUID}/download")

    assert response.status_code == 200, response.text
    assert response.content == expected.Binary
    assert response.headers["Content-Type"] == expected.Content_Type
    assert response.headers["Content-Disposition"] == f"attachment; filename={expected.Filename}"
    assert response.headers["Content-Length"] == str(expected.Size)
    assert response.headers["Access-Control-Expose-Headers"] == "Content-Disposition"


def test_unknown_uuid_returns_404(admin: TestClient):
    response = admin.get("/storage-files/00000000-0000-0000-0000-00000000dead/download")

    assert response.status_code == 404
    assert response.json()["detail"] == "Storage file niet gevonden"


def test_unauthenticated_returns_401(client: TestClient, ctx: Context):
    document_uuid: uuid.UUID = ctx.f.primary_key_uuid(Ref(StorageFileSpec, "file_1"))

    response = client.get(f"/storage-files/{document_uuid}/download")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
