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
import pytest
import pyodbc
from application import app
from datamodel import endpoints
from Tests.test_data import generate_data, reference_rich_beleidskeuze
from globals import DB_CONNECTION_SETTINGS, min_datetime, max_datetime
from Endpoints.references import (
    ID_List_Reference,
    UUID_List_Reference,
    ID_List_Reference,
)
import random
from flask import jsonify
import string
from passlib.hash import bcrypt


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


@pytest.fixture
def test_user():
    username = "test_user"
    email = "test@user.com"
    password = "".join(
        random.SystemRandom().choice(
            string.ascii_lowercase + string.ascii_uppercase + string.digits
        )
        for _ in range(50)
    )
    hashed = bcrypt.hash(password)
    with pyodbc.connect(DB_CONNECTION_SETTINGS, autocommit=False) as con:
        cur = con.cursor()
        cur.execute(
            f"""INSERT INTO Gebruikers (Gebruikersnaam, Wachtwoord, Rol, Email) VALUES (?, ?, ?, ?)""",
            username,
            hashed,
            "testing",
            email,
        )
        cur.commit()
        cur.execute(
            f"""SELECT UUID FROM Gebruikers WHERE Email=? AND Gebruikersnaam=?""",
            email,
            username,
        )
        user_uuid = cur.fetchone()
    return {
        "uuid": user_uuid[0],
        "username": username,
        "email": email,
        "password": password,
    }


@pytest.fixture(autouse=True)
def cleanup(auth, test_user):
    """
    Ensures the database is cleaned up after running tests
    """
    yield
    test_uuid = auth[0]
    with pyodbc.connect(DB_CONNECTION_SETTINGS) as cn:
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
        cur.execute(f"DELETE FROM Gebruikers WHERE UUID = ?", test_user["uuid"])


@pytest.mark.parametrize(
    "endpoint", endpoints, ids=(map(lambda ep: ep.Meta.slug, endpoints))
)
def test_valid_auth(client, auth, endpoint):
    # Try to acces the list view without auth
    list_ep = f"v0.1/{endpoint.Meta.slug}"
    response = client.get(list_ep)
    assert response.status_code == 401

    # Try to acces the list view with auth
    list_ep = f"v0.1/{endpoint.Meta.slug}"
    response = client.get(list_ep, headers={"Authorization": f"Bearer {auth[1]}"})
    assert response.status_code == 200

    # Try to acces the valid view without auth
    list_ep = f"v0.1/valid/{endpoint.Meta.slug}"
    response = client.get(list_ep)
    assert response.status_code == 200

    # Try to acces the valid view with auth
    list_ep = f"v0.1/{endpoint.Meta.slug}"
    response = client.get(list_ep, headers={"Authorization": f"Bearer {auth[1]}"})
    assert response.status_code == 200


# def test_password_reset(client, test_user):
#     # Try to login
#     login_res = client.post(
#         f"v0.1/login",
#         json={"identifier": test_user["email"], "password": test_user["password"]},
#     )

#     assert (
#         login_res.status_code == 200
#     ), f"Not logged in, response: {login_res.get_json()}"

#     token = login_res.get_json()["access_token"]
#     new_password = "12345Abcdegf!"
#     incorrect_password = "aa"
#     # Should fail on incorrect new_password

#     # Should fail on incorrect password
#     reset_password_res = client.post(
#         f"v0.1/password-reset",
#         headers={"Authorization": f"Bearer {token}"},
#         json={"password": "blabla", "new_password": incorrect_password},
#     )
#     assert reset_password_res.status_code != 200

#     # Should work with correct password
#     reset_password_res = client.post(
#         f"v0.1/password-reset",
#         headers={"Authorization": f"Bearer {token}"},
#         json={"password": test_user["password"], "new_password": new_password},
#     )
#     assert (
#         reset_password_res.status_code == 200
#     ), f"Password not reset, response: {reset_password_res.get_json()}"

#     # Check if reset came trough
#     login_res = client.post(
#         f"v0.1/login", json={"identifier": test_user["email"], "password": new_password}
#     )
#     assert (
#         login_res.status_code == 200
#     ), f"Not logged in, response: {login_res.get_json()}"
