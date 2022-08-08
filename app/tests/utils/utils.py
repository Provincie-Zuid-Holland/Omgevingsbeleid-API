from typing import Dict

from fastapi.testclient import TestClient

from app.core.config import settings


def get_admin_headers(client: TestClient) -> Dict[str, str]:
    login_data = {
        "username": "admin@test.com",
        "password": "password",
    }
    r = client.post(f"{settings.API_V01_STR}/login/access-token", data=login_data)
    tokens = r.json()
    a_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {a_token}"}
    return headers


def get_fred_headers(client: TestClient) -> Dict[str, str]:
    login_data = {
        "username": "fred@test.com",
        "password": "password",
    }
    r = client.post(f"{settings.API_V01_STR}/login/access-token", data=login_data)
    tokens = r.json()
    a_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {a_token}"}
    return headers
