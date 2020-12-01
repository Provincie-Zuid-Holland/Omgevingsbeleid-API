import os
import tempfile

import pytest

from application import app
from datamodel import dimensies_and_feiten

@pytest.fixture
def client():
    return app.test_client()

def test_endpoints(client):
    for ep in dimensies_and_feiten():
        list_ep = f"v0.1/{ep.slug}"
        response = client.get(list_ep)
        if response.status_code != 200:
            print(response.data)
        assert response.status_code == 200, f"Status code for {list_ep} was {response.status_code}, should be 200."


