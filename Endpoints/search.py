# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

from flask import Flask, jsonify, request
from datamodel import endpoints
from globals import row_to_dict, db_connection_settings
import pyodbc


def splitlist(value):
    """
    Function that splits list of query arguments into python lists
    """
    value = value.replace(' ', '')
    return value.split(',')


def searchquery(tablename, slug, title, description):
    return f'''
    SELECT {title} as Titel, {description} as Omschrijving, RANK as RANK, UUID as UUID, '{slug}' as Type  FROM CONTAINSTABLE({tablename}, *, ?) CT
    INNER JOIN (
	    SELECT * FROM 
	        (SELECT *, Row_Number() OVER (partition BY [ID] ORDER BY [Modified_Date] DESC) [RowNumber] FROM {tablename} WHERE UUID != '00000000-0000-0000-0000-000000000000') A
	    WHERE [RowNumber] = 1 ) B
    ON CT.[KEY] = B.UUID
    WHERE RANK > 0
    ORDER BY RANK DESC 
    '''


def searchView():
    """
    A view that accepts search queries to find object based on a fuzzy text match
    """
    query = request.args.get('query', default=None, type=str)
    type_exclude = request.args.get('exclude', default=None, type=splitlist)
    type_only = request.args.get('only', default=None, type=splitlist)
    limit = request.args.get('limit', default=10, type=int)

    if not query:
        return jsonify({'message': 'No search query provided.'}), 400
    if type_exclude and type_only:
        return jsonify({"message": "Using exclude and only together is not allowed"}), 403

    searchables = [ep for ep in endpoints if ep.Meta.searchable]

    if type_only:
        searchables = [ep for ep in searchables if ep.Meta.slug in type_only]
    elif type_exclude:
        searchables = [
            ep for ep in searchables if ep.Meta.slug not in type_exclude]

    if not searchables:
        return {'Message': 'No objects to search after applying filters'}, 400

    search_results = []
    query = f'"{query}*"'
    with pyodbc.connect(db_connection_settings, autocommit=False) as connection:
        cursor = connection.cursor()
        for ep in searchables:
            # We ignore any double
            title_field = ep.fields_with_props('search_title')[0]
            description_field = ep.fields_with_props('search_description')[0]
            if not title_field or not description_field:
                raise Exception('Faulty search config')

            search_query = searchquery(ep.Meta.table, ep.Meta.slug,
                                       title_field, description_field)
    
            results = list(
                map(row_to_dict, cursor.execute(search_query, query)))
    
            search_results = search_results + results
    
    # Sort the results
    search_results = sorted(
        search_results, key=lambda r: r['RANK'], reverse=True)

    return jsonify(search_results[:limit])
