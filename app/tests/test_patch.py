from datetime import datetime
from typing import Any, List
from uuid import uuid4
from devtools import debug
from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session

from app import models, schemas
from app.db.base_class import NULL_UUID
from app.tests.utils.exceptions import SetupMethodException
from app.tests.utils.mock_data import generate_data


@pytest.mark.usefixtures("fixture_data")
class TestPatch:
    """
    Test endpoint patching
    """

    ENTITIES = [
        models.Ambitie,
        models.Belang,
        models.Beleidskeuze,
    ]

    def _add_modifiable_object(self, schema, model, db, data=None):
        if not db:
            raise Exception(
                "No Session found. Should be provided as argument or injected by fixtures"
            )

        if not data:
            request_data = generate_data(
                obj_schema=schema,
                default_str="automated test",
            )
        else:
            request_data = data

        obj_data = schema(**request_data).dict()

        request_time = datetime.now()
        uuid = uuid4()

        obj_data["UUID"] = uuid
        obj_data["Created_By_UUID"] = NULL_UUID
        obj_data["Modified_By_UUID"] = NULL_UUID
        obj_data["Created_Date"] = request_time
        obj_data["Modified_Date"] = request_time

        # if str(model.__table__).lower() == "beleidsrelaties":
        #    obj_data.pop("Van_Beleidskeuze")
        #    obj_data.pop("Naar_Beleidskeuze")

        try:
            instance = model(**obj_data)
            db.add(instance)
            db.commit()

            db_obj = db.query(model).filter(model.UUID == uuid).one()

            return db_obj
        except Exception:
            raise SetupMethodException

    def test_endpoint_patch_ambitie(self, client: TestClient, admin_headers, db):
        # Arrange
        ambitie = self._add_modifiable_object(schemas.AmbitieCreate, models.Ambitie, db)

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
        base_obj = self._add_modifiable_object(schemas.BelangCreate, models.Belang, db)

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
        base_obj = self._add_modifiable_object(
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

#    def test_endpoint_patch_beleidsrelatie(self, client: TestClient, admin_headers, db):
#        # Arrange
#        bk1 = self._add_modifiable_object(
#            schemas.BeleidskeuzeCreate, models.Beleidskeuze, db
#        )
#        bk2 = self._add_modifiable_object(
#            schemas.BeleidskeuzeCreate, models.Beleidskeuze, db
#        )
#
#        br_data = generate_data(
#            obj_schema=schemas.BeleidsrelatieCreate,
#            default_str="automated test",
#        )
#        br_data["Van_Beleidskeuze_UUID"] = str(bk1.UUID)
#        br_data["Naar_Beleidskeuze_UUID"] = str(bk2.UUID)
#
#        base_obj = self._add_modifiable_object(
#            schema=schemas.BeleidsrelatieCreate,
#            model=models.Beleidsrelatie,
#            db=db,
#            data=br_data,
#        )
#
#        # Act
#        patch_data = {"Titel": "patched"}
#        response = client.patch(
#            url=f"v0.1/beleidsrelaties/{base_obj.ID}",
#            headers=admin_headers,
#            json=patch_data,
#        )
#        assert response.status_code == 200, f"Status code was {response.status_code}"
#
#        # Assert
#        json_obj = response.json()
#        assert json_obj["UUID"] != base_obj.UUID, "Excepted new UUID after patch"
#        assert json_obj["ID"] == base_obj.ID
#        assert (
#            json_obj["Titel"] == "patched"
#        ), "Expected Title field updated after patch"
#
    def test_endpoint_patch_beleidsregel(self, client: TestClient, admin_headers, db):
        # Arrange
        base_obj = self._add_modifiable_object(
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
        base_obj = self._add_modifiable_object(
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
        base_obj = self._add_modifiable_object(
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
        base_obj = self._add_modifiable_object(schemas.ThemaCreate, models.Thema, db)

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
