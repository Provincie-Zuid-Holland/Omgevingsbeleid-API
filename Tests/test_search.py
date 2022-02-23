# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

import pytest
from werkzeug.test import Client
from application import app
from globals import null_uuid

@pytest.fixture
def client():
    """
    Provides access to the flask test_client
    """
    return app.test_client()


def test_fieldset(client):
    res = client.get("v0.1/search?query=water")
    assert res.status_code == 200
    assert list(res.get_json()['results'][0].keys()) == [
        "Omschrijving",
        "RANK",
        "Titel",
        "Type",
        "UUID",
    ]


def test_keywords(client):
    response = client.get("v0.1/search?query=energie")
    assert response.status_code == 200

    response = client.get("v0.1/search?query=energie en lopen")
    assert response.status_code == 200

def test_search_total(client):
    response = client.get("v0.1/search?query=water")
    assert response.status_code == 200
    assert 'total' in response.get_json()
    assert 'results' in response.get_json()

def test_geo_search_total(client):
    response = client.get(f"v0.1/search/geo?query={null_uuid}")
    assert response.status_code == 200
    assert 'total' in response.get_json()
    assert 'results' in response.get_json()

def test_search_limit_offset(client):

    response = client.get("v0.1/search?query=water")
    assert response.status_code == 200
    assert len(response.get_json()['results']) == 10

    response = client.get("v0.1/search?query=water&limit=100")
    assert response.status_code == 200
    assert len(response.get_json()['results']) > 10

    response = client.get("v0.1/search?query=water&limit=3")
    assert response.status_code == 200
    assert len(response.get_json()['results']) == 3

    response = client.get("v0.1/search?query=water&limit=20&offset=5")
    assert response.status_code == 200
    assert len(response.get_json()['results']) == 20

    response = client.get("v0.1/search?query=water&limit=20&offset=-5")
    assert response.status_code == 403

    response = client.get("v0.1/search?query=water&limit=-1")
    assert response.status_code == 403
