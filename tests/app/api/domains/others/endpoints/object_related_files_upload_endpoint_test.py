import pytest
from fastapi.testclient import TestClient
from pytest import FixtureRequest


def _pdf(include_author: bool = False) -> tuple[str, bytes, str]:
    return (
        "upload.pdf",
        (
            b"%PDF-1.4\n"
            b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
            b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
            b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] >>\nendobj\n"
            b"4 0 obj\n<< /Author (Jane Doe) >>\nendobj\n"
            b"xref\n0 5\n"
            b"0000000000 65535 f \n"
            b"0000000009 00000 n \n"
            b"0000000058 00000 n \n"
            b"0000000115 00000 n \n"
            b"0000000186 00000 n \n"
            b"trailer\n<< /Size 5 /Root 1 0 R"
            + (b" /Info 4 0 R" if include_author else b"")
            + b" >>\nstartxref\n226\n%%EOF\n"
        ),
        "application/pdf",
    )


def test_uploads_a_file_and_it_appears_first_in_the_list(admin: TestClient):
    response = admin.post(
        "/beleidsdoel/1/object-related-files",
        data={"title": "New upload", "ignore_report": "true"},
        files={"uploaded_file": _pdf()},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["title"] == "New upload"
    assert body["code"] == "beleidsdoel-1"

    listed = admin.get("/beleidsdoel/1/object-related-files").json()
    assert listed[0]["id"] == body["id"]


def test_unknown_lineage_returns_404(admin: TestClient):
    response = admin.post(
        "/beleidsdoel/999999/object-related-files",
        data={"title": "New upload", "ignore_report": "true"},
        files={"uploaded_file": _pdf()},
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
        files={"uploaded_file": _pdf()},
    )

    assert response.status_code == expected_status, response.text
    if expected_detail is not None:
        assert response.json()["detail"] == expected_detail


def test_uploads_a_file_and_request_pdf_report_returns_error(admin: TestClient):
    response = admin.post(
        "/beleidsdoel/1/object-related-files",
        data={"title": "New upload", "ignore_report": "false"},
        files={"uploaded_file": _pdf(include_author=True)},
    )

    assert response.status_code == 434, response.text
    body = response.json()
    assert len(body["detail"]) == 1
    assert body["detail"][0]["key"] == "/Author"
    assert body["detail"][0]["value"] == "Jane Doe"


def test_uploads_a_file_and_request_pdf_report(admin: TestClient):
    response = admin.post(
        "/beleidsdoel/1/object-related-files",
        data={"title": "New upload", "ignore_report": "false"},
        files={"uploaded_file": _pdf(include_author=False)},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["title"] == "New upload"
    assert body["code"] == "beleidsdoel-1"

    listed = admin.get("/beleidsdoel/1/object-related-files").json()
    assert listed[0]["id"] == body["id"]
