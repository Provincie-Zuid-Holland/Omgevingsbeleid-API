import pytest
from fastapi.testclient import TestClient
from pytest import FixtureRequest

_PDF_FILE = ("upload.pdf", b"%PDF-1.4 fake content", "application/pdf")


def test_uploads_a_file_and_it_appears_first_in_the_list(admin: TestClient):
    response = admin.post(
        "/beleidsdoel/1/object-related-files",
        data={"title": "New upload", "ignore_report": "true"},
        files={"uploaded_file": _PDF_FILE},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["Title"] == "New upload"
    assert body["Code"] == "beleidsdoel-1"

    listed = admin.get("/beleidsdoel/1/object-related-files").json()
    assert listed[0]["UUID"] == body["UUID"]


def test_unknown_lineage_returns_404(admin: TestClient):
    response = admin.post(
        "/beleidsdoel/999999/object-related-files",
        data={"title": "New upload", "ignore_report": "true"},
        files={"uploaded_file": _PDF_FILE},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Object niet gevonden"


def test_rejects_non_pdf_content_type(admin: TestClient):
    response = admin.post(
        "/beleidsdoel/1/object-related-files",
        data={"title": "New upload", "ignore_report": "true"},
        files={"uploaded_file": ("upload.txt", b"not a pdf", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported file type, expected a PDF."


@pytest.mark.parametrize(
    "client_fixture, expected_status, expected_detail",
    [
        pytest.param("client", 401, "Not authenticated", id="unauthenticated"),
        pytest.param("ambtenaar", 401, "Invalid user role", id="role-without-permission"),
        pytest.param("owner_1", 200, None, id="owner-via-whitelist"),
        pytest.param("admin", 200, None, id="role-with-permission"),
    ],
)
def test_upload_permission_matrix(
    request: FixtureRequest, client_fixture: str, expected_status: int, expected_detail: str
):
    test_client: TestClient = request.getfixturevalue(client_fixture)

    response = test_client.post(
        "/beleidsdoel/1/object-related-files",
        data={"title": "New upload", "ignore_report": "true"},
        files={"uploaded_file": _PDF_FILE},
    )

    assert response.status_code == expected_status, response.text
    if expected_detail is not None:
        assert response.json()["detail"] == expected_detail
