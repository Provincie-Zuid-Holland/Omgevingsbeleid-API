from fastapi.testclient import TestClient
import pytest


@pytest.mark.usefixtures("fixture_data")
class TestModules:
    """
    Ensure beleidsmodule endpoints CRUD as expected
    """

    def test_modules_create(self, client: TestClient, admin_headers):
        response = client.post(
            "v0.1/beleidsmodules", headers=admin_headers, json={"Titel": "Test"}
        )
        assert response.status_code == 201, f"Response: {response.json()}"

    def test_modules_OK(self, client: TestClient, admin_headers):
        response = client.get("v0.1/beleidsmodules", headers=admin_headers)
        assert response.status_code == 200, f"Response: {response.json()}"
        assert len(response.json()) != 0
        assert "Maatregelen" in response.json()[0]

    def test_modules_valid(self, client: TestClient):
        response = client.get("v0.1/valid/beleidsmodules")
        assert response.status_code == 200, f"Response: {response.json()}"
