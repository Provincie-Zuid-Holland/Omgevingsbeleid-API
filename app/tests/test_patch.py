from typing import Any, List

from fastapi.testclient import TestClient
import pytest

from app import models, schemas
from app.tests.utils.mock_data import add_modifiable_object, generate_data


@pytest.mark.usefixtures("fixture_data")
class TestPatch:
    """
    Test endpoint patching
    """

    def test_endpoint_patch_ambitie(self, client: TestClient, admin_headers, db):
        # Arrange
        ambitie = add_modifiable_object(schemas.AmbitieCreate, models.Ambitie, db)

        # Act
        patch_data = {"Titel": "patched"}
        response = client.patch(
            url=f"v0.1/ambities/{ambitie.ID}", headers=admin_headers, json=patch_data
        )
        assert response.status_code == 200, f"Status code was {response.status_code}"

        # Assert
        json_obj = response.json()
        assert json_obj["UUID"] != ambitie.UUID, "Excepted new UUID after patch"
        assert json_obj["ID"] == ambitie.ID
        assert (
            json_obj["Titel"] == "patched"
        ), "Expected Title field updated after patch"

    def test_endpoint_patch_belangen(self, client: TestClient, admin_headers, db):
        # Arrange
        base_obj = add_modifiable_object(schemas.BelangCreate, models.Belang, db)

        # Act
        patch_data = {"Titel": "patched"}
        response = client.patch(
            url=f"v0.1/belangen/{base_obj.ID}", headers=admin_headers, json=patch_data
        )
        assert response.status_code == 200, f"Status code was {response.status_code}"

        # Assert
        json_obj = response.json()
        assert json_obj["UUID"] != base_obj.UUID, "Excepted new UUID after patch"
        assert json_obj["ID"] == base_obj.ID
        assert (
            json_obj["Titel"] == "patched"
        ), "Expected Title field updated after patch"

    def test_endpoint_patch_beleidsprestatie(
        self, client: TestClient, admin_headers, db
    ):
        # Arrange
        base_obj = add_modifiable_object(
            schemas.BeleidsprestatieCreate, models.Beleidsprestatie, db
        )

        # Act
        patch_data = {"Titel": "patched"}
        response = client.patch(
            url=f"v0.1/beleidsprestaties/{base_obj.ID}",
            headers=admin_headers,
            json=patch_data,
        )
        assert response.status_code == 200, f"Status code was {response.status_code}"

        # Assert
        json_obj = response.json()
        assert json_obj["UUID"] != base_obj.UUID, "Excepted new UUID after patch"
        assert json_obj["ID"] == base_obj.ID
        assert (
            json_obj["Titel"] == "patched"
        ), "Expected Title field updated after patch"

    def test_endpoint_patch_beleidsrelatie(self, client: TestClient, admin_headers, db):
        # Arrange
        bk1 = add_modifiable_object(
            schemas.BeleidskeuzeCreate, models.Beleidskeuze, db
        )
        bk2 = add_modifiable_object(
            schemas.BeleidskeuzeCreate, models.Beleidskeuze, db
        )

        br_data = generate_data(
            obj_schema=schemas.BeleidsrelatieCreate,
            default_str="automated test",
        )
        br_data["Van_Beleidskeuze_UUID"] = str(bk1.UUID)
        br_data["Naar_Beleidskeuze_UUID"] = str(bk2.UUID)

        base_obj = add_modifiable_object(
            schema=schemas.BeleidsrelatieCreate,
            model=models.Beleidsrelatie,
            db=db,
            data=br_data,
        )

        # Act
        patch_data = {"Titel": "patched"}
        response = client.patch(
            url=f"v0.1/beleidsrelaties/{base_obj.ID}",
            headers=admin_headers,
            json=patch_data,
        )
        assert response.status_code == 200, f"Status code was {response.status_code}"

        # Assert
        json_obj = response.json()
        assert json_obj["UUID"] != base_obj.UUID, "Excepted new UUID after patch"
        assert json_obj["ID"] == base_obj.ID
        assert (
            json_obj["Titel"] == "patched"
        ), "Expected Title field updated after patch"

    def test_endpoint_patch_beleidsregel(self, client: TestClient, admin_headers, db):
        # Arrange
        base_obj = add_modifiable_object(
            schemas.BeleidsregelCreate, models.Beleidsregel, db
        )

        # Act
        patch_data = {"Titel": "patched"}
        response = client.patch(
            url=f"v0.1/beleidsregels/{base_obj.ID}",
            headers=admin_headers,
            json=patch_data,
        )
        assert response.status_code == 200, f"Status code was {response.status_code}"

        # Assert
        json_obj = response.json()
        assert json_obj["UUID"] != base_obj.UUID, "Excepted new UUID after patch"
        assert json_obj["ID"] == base_obj.ID
        assert (
            json_obj["Titel"] == "patched"
        ), "Expected Title field updated after patch"

    def test_endpoint_patch_beleidsdoel(self, client: TestClient, admin_headers, db):
        # Arrange
        base_obj = add_modifiable_object(
            schemas.BeleidsdoelCreate, models.Beleidsdoel, db
        )

        # Act
        patch_data = {"Titel": "patched"}
        response = client.patch(
            url=f"v0.1/beleidsdoelen/{base_obj.ID}",
            headers=admin_headers,
            json=patch_data,
        )
        assert response.status_code == 200, f"Status code was {response.status_code}"

        # Assert
        json_obj = response.json()
        assert json_obj["UUID"] != base_obj.UUID, "Excepted new UUID after patch"
        assert json_obj["ID"] == base_obj.ID
        assert (
            json_obj["Titel"] == "patched"
        ), "Expected Title field updated after patch"

    def test_endpoint_patch_maatregel(self, client: TestClient, admin_headers, db):
        # Arrange
        base_obj = add_modifiable_object(
            schemas.MaatregelCreate, models.Maatregel, db
        )

        # Act
        patch_data = {"Titel": "patched"}
        response = client.patch(
            url=f"v0.1/maatregelen/{base_obj.ID}",
            headers=admin_headers,
            json=patch_data,
        )
        assert response.status_code == 200, f"Status code was {response.status_code}"

        # Assert
        json_obj = response.json()
        assert json_obj["UUID"] != base_obj.UUID, "Excepted new UUID after patch"
        assert json_obj["ID"] == base_obj.ID
        assert (
            json_obj["Titel"] == "patched"
        ), "Expected Title field updated after patch"

    def test_endpoint_patch_thema(self, client: TestClient, admin_headers, db):
        # Arrange
        base_obj = add_modifiable_object(schemas.ThemaCreate, models.Thema, db)

        # Act
        patch_data = {"Titel": "patched"}
        response = client.patch(
            url=f"v0.1/themas/{base_obj.ID}", headers=admin_headers, json=patch_data
        )
        assert response.status_code == 200, f"Status code was {response.status_code}"

        # Assert
        json_obj = response.json()
        assert json_obj["UUID"] != base_obj.UUID, "Excepted new UUID after patch"
        assert json_obj["ID"] == base_obj.ID
        assert (
            json_obj["Titel"] == "patched"
        ), "Expected Title field updated after patch"
