from flask import Flask, jsonify, request
from datamodel import dimensies_and_feiten
import pyodbc
from globals import db_connection_settings
# Any objects that shouldn't be searched
SEARCH_EXCLUDED = ["beleidsrelaties"]

def splitlist(value):
    value = value.replace(' ', '')
    return value.split(',')


def search_query(tablename, searchfields, limit=5):
    """
    Generates a query to use T-SQL Full text search given a tablename and fields.
    """
    if len(searchfields) > 2:
        fieldnames_inner = ','.join([searchfields[0], 'CONCAT(' + ', '.join(searchfields[1:]) + ') AS Omschrijving'])
        fieldnames = ','.join([searchfields[0], 'Omschrijving'])
        query = f"""SELECT UUID, {fieldnames}, '{tablename}' as Type, KEY_TBL.RANK FROM ( SELECT UUID, {fieldnames_inner}, ROW_NUMBER() OVER (PARTITION BY [ID] ORDER BY [Modified_Date] DESC) AS RowNumber FROM dbo.{tablename}) As t INNER JOIN CONTAINSTABLE({tablename}, *, ?, {limit}) as KEY_TBL ON t.UUID = KEY_TBL.[KEY] WHERE RowNumber = 1"""
    else:
        fieldnames = ','.join(searchfields)
        query = f"""SELECT UUID, {fieldnames}, '{tablename}' as Type, KEY_TBL.RANK FROM ( SELECT UUID, {fieldnames}, ROW_NUMBER() OVER (PARTITION BY [ID] ORDER BY [Modified_Date] DESC) AS RowNumber FROM dbo.{tablename}) As t INNER JOIN CONTAINSTABLE({tablename}, *, ?, {limit}) as KEY_TBL ON t.UUID = KEY_TBL.[KEY] WHERE RowNumber = 1"""
    return query.strip()


def search():
    query = request.args.get('query', default=None, type=str)
    type_exclude = request.args.get('exclude', default=None, type=splitlist)
    type_only = request.args.get('only', default=None, type=splitlist)
    limit = request.args.get('limit', default=5, type=int)
    print(limit)
    if type_exclude and type_only:
        return jsonify({"message": "Using exclude and only together is not allowed"}), 403
    if not query:
        return jsonify({"message": "Missing or invalid URL parameter 'query'"}), 400
    else:
        d_and_f = [dim for dim in dimensies_and_feiten() if dim['slug'] not in SEARCH_EXCLUDED]
        indices_possible = ', '.join([dim['slug'] for dim in d_and_f])
        indices = [dim['slug'] for dim in d_and_f]
        if type_exclude:
            for t in type_exclude:
                try:
                    indices.remove(t)
                except ValueError:
                    return jsonify({"message": f"Invalid type to exclude '{t}', possible options are: {indices_possible}'"}), 400
        elif type_only:
            for t in type_only:
                try:
                    indices.index(t)
                except ValueError:
                    return jsonify({"message": f"Invalid type to include '{t}', possible options are: {indices_possible}'"}), 400
            indices = type_only
        queries = []
        for table in d_and_f:
            if table['slug'] in indices:
                queries.append(search_query(table['tablename'], table['schema'].fields_with_props('search_field'), limit=limit))
        final_query = " UNION ".join(queries) + " ORDER BY RANK DESC"
        results = []
        with pyodbc.connect(db_connection_settings) as cnx:
            cur = cnx.cursor()
            if len(query.split()) > 1:
                query = ' AND '.join(query.split())
            cur.execute(final_query, *([query] * len(queries)))
            results = [dict(zip([t[0] for t in row.cursor_description], row)) for row in cur.fetchall()]
        return jsonify(results)