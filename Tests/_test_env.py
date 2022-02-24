# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

"""
Tests that perform checks on the database and application envirnoment.
"""

from typing import DefaultDict
import pytest
import pyodbc

from Api.datamodel import endpoints
from Api.settings import null_uuid



def test_search_index(client):
    """Check wether all the tables are properly configured for search"""
    with pyodbc.connect(DB_CONNECTION_SETTINGS) as connections:
        cur = connections.cursor()
        query = f'''SELECT DISTINCT OBJECT_NAME(fic.object_id) AS table_name, c.name AS column_name
                    FROM sys.fulltext_index_columns AS fic INNER JOIN
                    sys.columns AS c ON c.object_id = fic.object_id AND c.column_id = fic.column_id'''
        cur.execute(query)
        fieldmap = DefaultDict(list)
        for table, field in cur.fetchall():
            fieldmap[table].append(field)
        for ep in endpoints:
            search_fields = ep.fields_with_props('search_title') + ep.fields_with_props('search_description')
            assert set(fieldmap[ep.Meta.table]) == set(search_fields), f"Search configuration not matching database state for {ep.Meta.slug}"
