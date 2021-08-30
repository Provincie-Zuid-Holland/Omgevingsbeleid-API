# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

import pytest
from werkzeug.test import Client
from application import app

@pytest.fixture
def client():
    """
    Provides access to the flask test_client
    """
    return app.test_client()

def test_fieldset(client):
    res = client.get("v0.1/search?query=water")
    assert(res.status_code == 200)
    assert(list(res.get_json()[0].keys()) == ['Omschrijving','RANK', 'Titel', 'Type', 'UUID'])


def test_keywords(client):
    response = client.get("v0.1/search?query=energie")
    assert response.status_code == 200

    response = client.get("v0.1/search?query=energie en lopen")
    assert response.status_code == 200