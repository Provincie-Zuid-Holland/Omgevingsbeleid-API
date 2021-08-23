# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

from datetime import timezone
from Models import (
    beleidskeuzes,
    ambities,
    maatregelen,
    belangen,
    beleidsprestaties,
    beleidsmodule,
)
import os
import tempfile
import json
import pytest
import pyodbc
from application import app
from datamodel import endpoints
from Tests.test_data import generate_data, reference_rich_beleidskeuze
from globals import db_connection_settings, min_datetime, max_datetime
from Endpoints.references import (
    ID_List_Reference,
    UUID_List_Reference,
    ID_List_Reference,
)
import copy
from flask import jsonify
import datetime


@pytest.fixture
def client():
    """
    Provides access to the flask test_client
    """
    return app.test_client()


@pytest.fixture
def auth(client):
    """
    Provides a valid auth token
    """
    test_id = os.getenv("TEST_MAIL")
    test_pw = os.getenv("TEST_PASS")
    resp = client.post("/v0.1/login", json={"identifier": test_id, "password": test_pw})
    if not resp.status_code == 200:
        pytest.fail(f"Unable to authenticate with API: {resp.get_json()}")
    return (resp.get_json()["identifier"]["UUID"], resp.get_json()["access_token"])


@pytest.fixture(autouse=True)
def cleanup(auth):
    """
    Ensures the database is cleaned up after running tests
    """
    yield
    test_uuid = auth[0]
    with pyodbc.connect(db_connection_settings) as cn:
        cur = cn.cursor()
        for table in endpoints:
            new_uuids = list(
                cur.execute(
                    f"SELECT UUID FROM {table.Meta.table} WHERE Created_By = ?",
                    test_uuid,
                )
            )
            for field, ref in table.Meta.references.items():
                # Remove all references first
                if type(ref) == UUID_List_Reference or type(ref) == ID_List_Reference:
                    for new_uuid in list(new_uuids):
                        cur.execute(
                            f"DELETE FROM {ref.link_tablename} WHERE {ref.my_col} = ?",
                            new_uuid[0],
                        )
            cur.execute(
                f"DELETE FROM {table.Meta.table} WHERE Created_By = ?", test_uuid
            )

@pytest.mark.parametrize(
    "endpoint", endpoints, ids=(map(lambda ep: ep.Meta.slug, endpoints))
)
def test_valid_auth(client, auth, endpoint):
    # Try to acces the list view without auth
    list_ep = f"v0.1/{endpoint.Meta.slug}"
    response = client.get(list_ep) 
    assert(response.status_code == 401)

    # Try to acces the list view with auth
    list_ep = f"v0.1/{endpoint.Meta.slug}"
    response = client.get(list_ep, headers={"Authorization": f"Bearer {auth[1]}"}) 
    assert(response.status_code == 200)

    # Try to acces the valid view without auth
    list_ep = f"v0.1/valid/{endpoint.Meta.slug}"
    response = client.get(list_ep) 
    assert(response.status_code == 200)
    
    # Try to acces the valid view with auth
    list_ep = f"v0.1/{endpoint.Meta.slug}"
    response = client.get(list_ep, headers={"Authorization": f"Bearer {auth[1]}"}) 
    assert(response.status_code == 200)