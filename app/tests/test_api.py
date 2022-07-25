import pytest


@pytest.mark.usefixtures("fixture_data")
class TestApi:

    async def test_beleidskeuze_valid_view_past_vigerend(self, client):
        response = client.get("v0.1/valid/beleidskeuzes?all_filters=Afweging:beleidskeuze1030")
        assert response.status_code == 200, f"Status code was {response.status_code}"
        data = response.get_json()

        assert len(data) == 0, f"We are expecting nothing as the most recent Vigerend has its Eind_Geldigheid in the past"
