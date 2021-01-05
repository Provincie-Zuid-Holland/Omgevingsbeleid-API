# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

"""
Tests that perform checks on the database and application envirnoment.
"""

import os
import tempfile

import pytest

from application import app
from datamodel import endpoints
from globals import db_connection_settings, null_uuid
import pyodbc 

@pytest.fixture
def client():
    return app.test_client()

def test_nills(client):
    """Check wether all the tables in the datamodel contain a Nill UUID"""
    for ep in endpoints:
        print(ep)
        with pyodbc.connect(db_connection_settings) as connections:
            cur = connections.cursor()
            query = f"SELECT UUID FROM {ep.slug} WHERE UUID = ?"
            cur.execute(query, null_uuid)
            results = cur.fetchall()
            assert len(results) == 1, f"No Nill UUID object in table {ep.slug}"
