from fastapi.testclient import TestClient
import pytest


@pytest.mark.usefixtures("fixture_data")
class TestAuth:
    ADMIN_EMAIL = "admin@test.com"
    USER_PASSWORD = "password"

    def test_login(self, client: TestClient):
        request_data = {
            "username": self.ADMIN_EMAIL,
            "password": self.USER_PASSWORD,
            "grant_type": "",
            "client_id": "",
            "scope": "",
            "client_secret": "",
        }
        response = client.post("v0.1/login/access-token", data=request_data)

        assert response.status_code == 200, f"Status code was {response.status_code}"
        data = response.json()
        assert "access_token" in data

    def test_incorrect_credentials(self, client: TestClient):
        request_data = {
            "username": self.ADMIN_EMAIL,
            "password": "wrongpw",
            "grant_type": "",
            "client_id": "",
            "scope": "",
            "client_secret": "",
        }

        response = client.post("v0.1/login/access-token", data=request_data)

        assert response.status_code == 401, f"Status code was {response.status_code}"

    def test_authenticated_endpoint(self, client: TestClient, admin_headers):
        response = client.get(url="v0.1/ambities", headers=admin_headers)
        assert response.status_code == 200, f"Status code was {response.status_code}"

#    def test_authenticated_graph_endpoint(self, client: TestClient, admin_headers):
#        response = client.get(url="v0.1/graph", headers=admin_headers)
#        assert response.status_code == 200, f"Status code was {response.status_code}"

    def test_unauthenticated(self, client: TestClient):
        create_request = {
            "Titel": "test object",
            "Omschrijving": "test object",
            "Weblink": "test object",
            "Begin_Geldigheid": "2012-10-11T18:31:21.548Z",
            "Eind_Geldigheid": "2012-10-11T18:31:21.548Z",
        }

        responses = [
#            client.get("v0.1/graph"),
            client.get("v0.1/ambities"),
            client.get("v0.1/changes/ambities/test/test"),
            client.post("v0.1/ambities", data={}),
        ]
        for response in responses:
            assert (
                response.status_code == 401
            ), f"Status code was {response.status_code}"
