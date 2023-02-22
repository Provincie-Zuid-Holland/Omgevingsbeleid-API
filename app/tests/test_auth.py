from fastapi.testclient import TestClient
from app import schemas
from app.crud.crud_ambitie import CRUDAmbitie
from app.db.base_class import MAX_DATETIME, MIN_DATETIME
from app.models.ambitie import Ambitie
from app.models.gebruiker import Gebruiker
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

    def test_authenticated_graph_endpoint(self, client: TestClient, admin_headers):
        response = client.get(url="v0.1/graph", headers=admin_headers)
        assert response.status_code == 200, f"Status code was {response.status_code}"

    def test_unauthenticated(self, client: TestClient):
        responses = [
            client.get("v0.1/ambities"),
            client.post("v0.1/ambities", data={}),
        ]
        for response in responses:
            assert (
                response.status_code == 401
            ), f"Status code was {response.status_code}"

    # Ownership access tests
    def test_ownership_forbidden(self, client: TestClient, ba_auth_headers, db):
        # Get an existing user UUID
        original_owner = (
            db.query(Gebruiker).filter(Gebruiker.Email == "fred@test.com").one()
        )

        amb_schema = schemas.AmbitieCreate(
            Titel="auto test",
            Begin_Geldigheid=MIN_DATETIME,
            Eind_Geldigheid=MAX_DATETIME,
        )

        crud = CRUDAmbitie(Ambitie, db=db)
        ambitie = crud.create(obj_in=amb_schema, by_uuid=original_owner.UUID)

        # Act
        patch_data = {"Titel": "patched"}
        response = client.patch(
            url=f"v0.1/ambities/{ambitie.ID}", headers=ba_auth_headers, json=patch_data
        )

        # Expect 403 forbidden since patching a different users entitiy
        assert response.status_code == 403

    def test_ownership_self(self, client: TestClient, ba_auth_headers, db):
        # Get this users uuid
        original_owner = (
            db.query(Gebruiker).filter(Gebruiker.Email == "alex@test.com").one()
        )

        amb_schema = schemas.AmbitieCreate(
            Titel="auto test",
            Begin_Geldigheid=MIN_DATETIME,
            Eind_Geldigheid=MAX_DATETIME,
        )

        crud = CRUDAmbitie(Ambitie, db=db)
        ambitie = crud.create(obj_in=amb_schema, by_uuid=original_owner.UUID)

        # Act
        patch_data = {"Titel": "patched"}
        response = client.patch(
            url=f"v0.1/ambities/{ambitie.ID}", headers=ba_auth_headers, json=patch_data
        )

        assert response.status_code == 200

    # Beheerder can patch others entities
    def test_ownership_beheerder(self, client: TestClient, admin_headers, db):
        # Get this users uuid
        original_owner = (
            db.query(Gebruiker).filter(Gebruiker.Email == "alex@test.com").one()
        )

        amb_schema = schemas.AmbitieCreate(
            Titel="auto test",
            Begin_Geldigheid=MIN_DATETIME,
            Eind_Geldigheid=MAX_DATETIME,
        )

        crud = CRUDAmbitie(Ambitie, db=db)
        ambitie = crud.create(obj_in=amb_schema, by_uuid=original_owner.UUID)

        # Act
        patch_data = {"Titel": "patched"}
        response = client.patch(
            url=f"v0.1/ambities/{ambitie.ID}", headers=admin_headers, json=patch_data
        )

        assert response.status_code == 200
