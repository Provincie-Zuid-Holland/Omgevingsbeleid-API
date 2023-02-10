from fastapi.testclient import TestClient
from app.db.base_class import MAX_DATETIME, MIN_DATETIME, NULL_UUID
from app.models.base import Status

from app.schemas.beleidskeuze import Beleidskeuze, BeleidskeuzeCreate
from app.schemas.beleidsrelatie import BeleidsrelatieCreate
import pytest


@pytest.mark.usefixtures("fixture_data")
class TestBeleidskeuzes:
    """
    Test Beleidskeuze CRUD and its relationships
    """

    def test_crud_beleidskeuzes(self, client: TestClient, admin_headers, db):
        # Create
        request_data = BeleidskeuzeCreate(
            Begin_Geldigheid=MIN_DATETIME,
            Eind_Geldigheid=MAX_DATETIME,
            Eigenaar_1_UUID=NULL_UUID,
            Eigenaar_2_UUID=NULL_UUID,
            Portefeuillehouder_1_UUID=NULL_UUID,
            Portefeuillehouder_2_UUID=NULL_UUID,
            Opdrachtgever_UUID=NULL_UUID,
            Status=Status.VIGEREND,
            Titel="Created BK",
            Omschrijving_Keuze="Nam libero leo, tempus in pretium vel, rhoncus in mi.",
            Omschrijving_Werking="Duis neque nulla, egestas aliquet nisi ut, dapibus pellentesque neque.",
            Aanleiding="Created BK",
            Afweging="Created BK",
            Provinciaal_Belang="Created BK",
            Weblink="www.beleid.beslissing.nl",
            Besluitnummer="42",
            Tags="Wetenschap, Test",
        )

        response = client.post(
            url=f"v0.1/beleidskeuzes",
            headers=admin_headers,
            data=request_data.json(),
        )
        assert response.status_code == 200, f"Status code was {response.status_code}"
        created_bk = Beleidskeuze(**response.json())

        # Read
        response = client.get(
            url=f"v0.1/beleidskeuzes/{created_bk.ID}",
            headers=admin_headers,
        )
        assert response.status_code == 200, f"Status code was {response.status_code}"
        assert len(response.json()) == 1, f"Expected 1 item for this ID"
        read_bk = Beleidskeuze(**response.json()[0])

        # Patch
        patch_data = {"Titel": "patched title"}
        response = client.patch(
            url=f"v0.1/beleidskeuzes/{read_bk.ID}",
            headers=admin_headers,
            json=patch_data,
        )
        assert response.status_code == 200, f"Status code was {response.status_code}"

        # Read
        response = client.get(
            url=f"v0.1/beleidskeuzes/{created_bk.ID}",
            headers=admin_headers,
        )
        assert response.status_code == 200, f"Status code was {response.status_code}"
        assert len(response.json()) == 2, f"Expected 2 item for this ID"

        patched_bk = Beleidskeuze(**response.json()[0])

        assert patched_bk.UUID != created_bk.UUID
        assert patched_bk.ID == created_bk.ID
        assert patched_bk.Titel == "patched title"

    def test_patch_having_beleidsrelatie(self, client: TestClient, admin_headers, db):
        # Create two Beleidskeuzes
        request_data_1 = BeleidskeuzeCreate(
            Begin_Geldigheid=MIN_DATETIME,
            Eind_Geldigheid=MAX_DATETIME,
            Status=Status.VIGEREND,
            Titel="BK1",
        )

        request_data_2 = BeleidskeuzeCreate(
            Begin_Geldigheid=MIN_DATETIME,
            Eind_Geldigheid=MAX_DATETIME,
            Status=Status.VIGEREND,
            Titel="BK2",
        )

        response_1 = client.post(
            url=f"v0.1/beleidskeuzes",
            headers=admin_headers,
            data=request_data_1.json(),
        )
        response_2 = client.post(
            url=f"v0.1/beleidskeuzes",
            headers=admin_headers,
            data=request_data_2.json(),
        )
        assert response_1.status_code == 200
        assert response_2.status_code == 200
        created_bk_1 = Beleidskeuze(**response_1.json())
        created_bk_2 = Beleidskeuze(**response_2.json())

        # Create relatie
        relatie_request = BeleidsrelatieCreate(
            Van_Beleidskeuze_UUID=str(created_bk_1.UUID),
            Naar_Beleidskeuze_UUID=str(created_bk_2.UUID),
        )
        relatie_response = client.post(
            url=f"v0.1/beleidsrelaties",
            headers=admin_headers,
            data=relatie_request.json(),
        )
        assert response_1.status_code == 200

        # Patch
        patch_data = {"Titel": "patched title"}
        response = client.patch(
            url=f"v0.1/beleidskeuzes/{created_bk_2.ID}",
            headers=admin_headers,
            json=patch_data,
        )
        assert response.status_code == 200, f"Status code was {response.status_code}"
