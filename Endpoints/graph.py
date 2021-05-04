# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

from flask import Flask, jsonify, request
from datamodel import endpoints, linker_tables
from globals import row_to_dict, db_connection_settings
import pyodbc
from flask_jwt_extended import jwt_required

@jwt_required
def graphView():
    nodes = []
    links = []

    for ep in endpoints:
        if title_field := ep.fields_with_props('search_title'):
            title_field = title_field[0]
            if ep.Meta.status_conf:
                query = f'''SELECT UUID, Titel, '{ep.Meta.slug}' as Type FROM
                            (SELECT UUID, {title_field} as Titel, Row_number() OVER (partition BY [ID]
                            ORDER BY [Modified_date] DESC) [RowNumber]
                            FROM {ep.Meta.table}
                            WHERE {ep.Meta.status_conf[0]} = '{ep.Meta.status_conf[1]}' AND UUID != '00000000-0000-0000-0000-000000000000') T 
                        WHERE rownumber = 1'''
            else:
                query = f'''SELECT UUID, Titel, '{ep.Meta.slug}' as Type FROM
                            (SELECT UUID, {title_field} as Titel, Row_number() OVER (partition BY [ID]
                            ORDER BY [Modified_date] DESC) [RowNumber]
                            FROM {ep.Meta.table}
                            WHERE UUID != '00000000-0000-0000-0000-000000000000') T 
                        WHERE rownumber = 1'''
            with pyodbc.connect(db_connection_settings) as connection:
                cursor = connection.cursor()                
                nodes = nodes + list(map(row_to_dict, cursor.execute(query)))
    
    seen_uuids = [node['UUID'] for node in nodes]
    bbs_uuid_list = ', '.join([f"'{node['UUID']}'" for node in nodes if node['Type'] == 'beleidskeuzes'])


    for table, link in linker_tables:
        query =  f'''SELECT Beleidskeuze_UUID as source, {link} as target, 'Koppeling' as type from {table} WHERE Beleidskeuze_UUID IN ({bbs_uuid_list})'''
        with pyodbc.connect(db_connection_settings) as connection:
                cursor = connection.cursor()                
                for link in map(row_to_dict, cursor.execute(query)):
                    if link['target'] in seen_uuids:
                        links.append(link)
    
    query =  f'''SELECT Van_Beleidskeuze as source, Naar_Beleidskeuze as target, 'Relatie' as type from Beleidsrelaties WHERE Van_Beleidskeuze IN ({bbs_uuid_list})'''
    with pyodbc.connect(db_connection_settings) as connection:
        cursor = connection.cursor()                
        for link in map(row_to_dict, cursor.execute(query)):
            if link['target'] in seen_uuids:
                links.append(link)

    return {'nodes': nodes, 'links': links}
