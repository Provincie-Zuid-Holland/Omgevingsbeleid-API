# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

from flask import Flask, jsonify, request
from datamodel import endpoints
from globals import row_to_dict, db_connection_settings
import pyodbc
from flask_jwt_extended import jwt_required
from Endpoints.references import UUID_List_Reference

@jwt_required
def graphView():
    nodes = []
    links = []
    linker_tables = []

    # Collect all objects that are valid right now
    for ep in endpoints:
        if ep.Meta.graph_conf:
            title_field = ep.Meta.graph_conf
            linker_tables += [(ref.link_tablename, ref.their_col) for _, ref in ep.Meta.references.items() if isinstance(ref, UUID_List_Reference)]
        else:
            continue
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
    
    # Store the UUIDs
    seen_uuids = [node['UUID'] for node in nodes]
    bbs_uuid_list = ', '.join([f"'{node['UUID']}'" for node in nodes if node['Type'] == 'beleidskeuzes'])

    print(linker_tables)
    # Gather all the direct links
    for table, link in linker_tables:
        query =  f'''SELECT Beleidskeuze_UUID as source, {link} as target, 'Koppeling' as type from {table} WHERE Beleidskeuze_UUID IN ({bbs_uuid_list})'''
        with pyodbc.connect(db_connection_settings) as connection:
                cursor = connection.cursor()                
                for link in map(row_to_dict, cursor.execute(query)):
                    if link['target'] in seen_uuids:
                        links.append(link)
    
    query =  f'''SELECT Van_Beleidskeuze as source, Naar_Beleidskeuze as target, 'Relatie' as type from Beleidsrelaties WHERE Van_Beleidskeuze IN ({bbs_uuid_list}) AND Status = 'Akkoord' '''
    with pyodbc.connect(db_connection_settings) as connection:
        cursor = connection.cursor()                
        for link in map(row_to_dict, cursor.execute(query)):
            if link['target'] in seen_uuids:
                links.append(link)

    return {'nodes': nodes, 'links': links}