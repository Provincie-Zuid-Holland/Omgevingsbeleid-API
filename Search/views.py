from flask import Flask, jsonify, request
from datamodel import dimensies_and_feiten
import pyodbc
from globals import db_connection_settings, null_uuid
from uuid import UUID
# Any objects that shouldn't be searched
SEARCH_EXCLUDED = ["beleidsrelaties"]
GEO_SEARCH_INCLUDED = ['maatregelen', 'verordeningen', 'beleidsbeslissingen']


def splitlist(value):
    value = value.replace(' ', '')
    return value.split(',')


def search_query(tablename, searchfields, limit=5):
    """
    Generates a query to use T-SQL Full text search given a tablename and fields.
    """

    if tablename == 'Verordeningen':
        fieldnames = ', '.join(searchfields[1:]) + ' AS Omschrijving'
        query = f"""SELECT UUID, {searchfields[0]}, Omschrijving , '{tablename}' as Type, KEY_TBL.RANK FROM ( SELECT UUID, {searchfields[0]}, {fieldnames}, ROW_NUMBER() OVER (PARTITION BY [ID] ORDER BY [Modified_Date] DESC) AS RowNumber FROM dbo.{tablename} WHERE Type = 'Artikel') As t INNER JOIN CONTAINSTABLE({tablename}, *, ?, {limit}) as KEY_TBL ON t.UUID = KEY_TBL.[KEY] WHERE RowNumber = 1"""
        return query.strip()
    if tablename == 'Beleidsbeslissingen':
        fieldnames_inner = ','.join(
            [searchfields[0], 'CONCAT(' + ', '.join(searchfields[1:]) + ') AS Omschrijving'])
        fieldnames = ','.join([searchfields[0], 'Omschrijving'])
        query = f"""SELECT UUID, {fieldnames}, '{tablename}' as Type, KEY_TBL.RANK FROM ( SELECT UUID, {fieldnames_inner}, Status, ROW_NUMBER() OVER (PARTITION BY [ID] ORDER BY [Modified_Date] DESC) AS RowNumber FROM dbo.{tablename} WHERE Status='Vigerend') As t INNER JOIN CONTAINSTABLE({tablename}, *, ?, {limit}) as KEY_TBL ON t.UUID = KEY_TBL.[KEY] WHERE RowNumber = 1 AND Status = 'Vigerend'"""
        return query.strip()
    else:
        fieldnames = ','.join(searchfields)
        query = f"""SELECT UUID, {fieldnames}, '{tablename}' as Type, KEY_TBL.RANK FROM ( SELECT UUID, {fieldnames}, ROW_NUMBER() OVER (PARTITION BY [ID] ORDER BY [Modified_Date] DESC) AS RowNumber FROM dbo.{tablename}) As t INNER JOIN CONTAINSTABLE({tablename}, *, ?, {limit}) as KEY_TBL ON t.UUID = KEY_TBL.[KEY] WHERE RowNumber = 1"""
        return query.strip()


def search():
    query = request.args.get('query', default=None, type=str)
    type_exclude = request.args.get('exclude', default=None, type=splitlist)
    type_only = request.args.get('only', default=None, type=splitlist)
    limit = request.args.get('limit', default=5, type=int)
    if type_exclude and type_only:
        return jsonify({"message": "Using exclude and only together is not allowed"}), 403
    if not query:
        return jsonify({"message": "Missing or invalid URL parameter 'query'"}), 400
    else:
        d_and_f = [dim for dim in dimensies_and_feiten() if dim['slug']
                   not in SEARCH_EXCLUDED]
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
                    queries.append(search_query(
                        table['tablename'], table['schema'].fields_with_props('search_field'), limit=limit))
        final_query = " UNION ".join(queries) + " ORDER BY RANK DESC"
        results = []
        with pyodbc.connect(db_connection_settings) as cnx:
            cur = cnx.cursor()
            if len(query.split()) > 1:
                query = ' AND '.join(query.split())
            cur.execute(final_query, *([query] * len(queries)))
            results = [dict(zip([t[0] for t in row.cursor_description], row))
                       for row in cur.fetchall()]
            for result in results:
                for field in result:
                    try:
                        result[field] = result[field].replace('\r', '\n')
                    except:
                        continue

        return jsonify(results)


def geo_search_query(tablename, actuele_tablename, searchfields, geofield, uuids):
    """
    Generates a query to use T-SQL Full text search given a tablename and fields.
    """
    if len(searchfields) > 2:
        fieldnames = ','.join(
            [searchfields[0], 'CONCAT(' + ', '.join(searchfields[1:]) + ') AS Omschrijving'])
    else:
        fieldnames = ','.join(searchfields)
    marks = ', '.join(["?"] * len(uuids))
    query = f"""SELECT UUID, {fieldnames}, {geofield} as Gebied, '{tablename}' as Type, 100 as RANK FROM {actuele_tablename} WHERE {geofield} in ( {marks} ) """
    return query.strip()


def fact_search_query(tablename, actuele_tablename, fact_tablename, searchfields, geofield, uuids):
    if len(searchfields) > 2:
        fieldnames = ','.join([searchfields[0], 'CONCAT(' + ', '.join(
            map(lambda sf: f'BB.{sf}', searchfields[1:])) + ') AS Omschrijving'])
    marks = ', '.join(["?"] * len(uuids))
    query = f"""SELECT BB.UUID, {fieldnames}, OB.fk_WerkingsGebieden As Gebied, '{tablename}' as Type, 100 as RANK from {actuele_tablename} BB
        RIGHT JOIN (SELECT fk_{tablename}, fk_WerkingsGebieden FROM {fact_tablename} WHERE fk_WerkingsGebieden IN ( {marks} )) OB on OB.fk_{tablename} = BB.UUID WHERE BB.UUID != '{null_uuid}'"""
    return query.strip()


def geo_search():
    query = request.args.get('query', default=None, type=str)
    try:
        geo_uuids = list(
            map(lambda uuid: UUID(uuid.strip()), query.split(',')))
        d_and_f = [dim for dim in dimensies_and_feiten() if dim['slug']
                   in GEO_SEARCH_INCLUDED]
        queries = []
        params = []
        for table in d_and_f:
            # Dimensions
            if not (table['schema'].fields_with_props('geo_field')[0] in table['schema'].fields_with_props('linker')):
                queries.append(geo_search_query(table['tablename'],
                                                table['latest_tablename'],
                                                table['schema'].fields_with_props(
                                                    'search_field'),
                                                table['schema'].fields_with_props('geo_field')[
                    0],
                    geo_uuids))
                params = params + geo_uuids
            # Facts
            else:
                queries.append(fact_search_query(table['tablename'],
                                                 table['latest_tablename'],
                                                 table['schema'].Meta.fact_tn,
                                                 table['schema'].fields_with_props(
                                                     'search_field'),
                                                 "fk_" +
                                                 table['schema'].fields_with_props('geo_field')[
                    0],
                    geo_uuids))
                params = params + geo_uuids
        final_query = " UNION ".join(queries)
        results = []
        # return jsonify([final_query, params])
        with pyodbc.connect(db_connection_settings) as cnx:
            cur = cnx.cursor()
            cur.execute(final_query, params)
            results = [dict(zip([t[0] for t in row.cursor_description], row))
                       for row in cur.fetchall()]
        return jsonify(results)
    except ValueError:
        return jsonify({"message": "'query parameter is not a list of UUIDs"}), 400
