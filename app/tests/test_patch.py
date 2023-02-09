from fastapi.testclient import TestClient
from app.models.base import RelatieStatus
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
            schema=schemas.BeleidskeuzeCreate, model=models.Beleidskeuze, db=db
        )
        bk2 = add_modifiable_object(
            schema=schemas.BeleidskeuzeCreate, model=models.Beleidskeuze, db=db
        )

        br_data = schemas.BeleidsrelatieCreate(
            Omschrijving="test beleidsrelatie",
            Status=RelatieStatus.AKKOORD.value,
            Begin_Geldigheid="1992-11-23T10:00:00",
            Eind_Geldigheid="2033-11-23T10:00:00",
            Van_Beleidskeuze_UUID=str(bk1.UUID),
            Naar_Beleidskeuze_UUID=str(bk2.UUID),
        ).dict()

        base_obj = add_modifiable_object(
            schema=schemas.BeleidsrelatieCreate,
            model=models.Beleidsrelatie,
            db=db,
            data=br_data,
        )

        # Act
        patch_data = {"Omschrijving": "patched"}
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
            json_obj["Omschrijving"] == "patched"
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
        base_obj = add_modifiable_object(schemas.MaatregelCreate, models.Maatregel, db)

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

    def test_endpoint_patch_gebiedsprogrammas(
        self, client: TestClient, admin_headers, db
    ):
        # Arrange
        maatregel: Maatregel = add_modifiable_object(
            schema=schemas.MaatregelCreate, model=models.Maatregel, db=db
        )

        gebiedsprog_data = generate_data(obj_schema=schemas.GebiedsprogrammaCreate)

        base_obj = add_modifiable_object(
            schema=schemas.GebiedsprogrammaCreate,
            model=models.Gebiedsprogramma,
            db=db,
            data=gebiedsprog_data,
        )

        # Act
        patch_data = {"Titel": "patched"}
        response = client.patch(
            url=f"v0.1/gebiedsprogrammas/{base_obj.ID}",
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

    # def test_non_copy_field(self, client: TestClient, admin_headers):
    #     # create beleidskeuze lineage
    #     test_data = generate_data(schemas.BeleidskeuzeCreate)
    #     response = client.post(
    #         "v0.1/beleidskeuzes", headers=admin_headers, json=test_data
    #     )
    #     assert (
    #         response.status_code == 200
    #     ), f"Status code for CREATE was {response.status_code}, should be 200. Body content: {response.json}"

    #     first_uuid = response.json()["UUID"]
    #     ep = f"v0.1/beleidskeuzes/{response.json()['ID']}"
    #     # Patch a new aanpassing_op field
    #     response = client.patch(
    #         ep,
    #         headers=admin_headers,
    #         json={"Titel": "Patched", "Aanpassing_Op": first_uuid},
    #     )
    #     assert (
    #         response.status_code == 200
    #     ), f"Status code for POST on {ep} was {response.status_code}, should be 200. Body content: {response.json}"
    #     assert (
    #         response.json()["Aanpassing_Op"] == first_uuid
    #     ), "Aanpassing_Op not saved!"

    #     # Patch a different field, aanpassing_op should be null
    #     response = client.patch(
    #         ep, headers=admin_headers, json={"Titel": "Patched twice"}
    #     )
    #     assert (
    #         response.status_code == 200
    #     ), f"Status code for POST on {ep} was {response.status_code}, should be 200. Body content: {response.json}"
    #     assert response.json()["Aanpassing_Op"] == None, "Aanpassing_Op was copied!"
