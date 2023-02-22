from fastapi.testclient import TestClient
import pytest


@pytest.mark.usefixtures("fixture_data")
class TestVerordeningStructuur:
    # TEMP
    def test_read_endpoint_health(self, client: TestClient):
        response = client.get(f"v0.1/verordeningstructuur")
        assert response.status_code == 200, f"Status code was {response.status_code}"

        response = client.get(f"v0.1/verordeningstructuur/1")
        assert response.status_code != 500
