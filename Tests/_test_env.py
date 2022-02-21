# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

"""
Tests that perform checks on the database and application envirnoment.
"""

import os
import tempfile
from typing import DefaultDict

import pytest

from application import app
from datamodel import endpoints
from globals import DB_CONNECTION_SETTINGS, null_uuid, row_to_dict
import pyodbc


@pytest.fixture
def client():
    return app.test_client()


def test_nills(client):
    """Check wether all the tables in the datamodel contain a Nill UUID"""
    with pyodbc.connect(DB_CONNECTION_SETTINGS) as connections:
        cur = connections.cursor()
        for ep in endpoints:
            query = f"SELECT UUID FROM {ep.Meta.table} WHERE UUID = ?"
            cur.execute(query, null_uuid)
            results = cur.fetchall()
            assert len(results) == 1, f"No Nill UUID object in table {ep.slug}"


# def test_search_index(client):
#     """Check wether all the tables are properly configured for search"""
#     with pyodbc.connect(DB_CONNECTION_SETTINGS) as connections:
#         cur = connections.cursor()
#         query = f'''SELECT DISTINCT OBJECT_NAME(fic.object_id) AS table_name, c.name AS column_name
#                     FROM sys.fulltext_index_columns AS fic INNER JOIN
#                     sys.columns AS c ON c.object_id = fic.object_id AND c.column_id = fic.column_id'''
#         cur.execute(query)
#         fieldmap = DefaultDict(list)
#         for table, field in cur.fetchall():
#             fieldmap[table].append(field)
#         for ep in endpoints:
#             search_fields = ep.fields_with_props('search_title') + ep.fields_with_props('search_description')
#             assert set(fieldmap[ep.Meta.table]) == set(search_fields), f"Search configuration not matching database state for {ep.Meta.slug}"
