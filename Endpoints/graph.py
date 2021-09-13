# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

from flask import Flask, jsonify, request
from datamodel import endpoints
from globals import row_to_dict, db_connection_settings
import pyodbc
from flask_jwt_extended import jwt_required
from Endpoints.references import UUID_List_Reference, ID_List_Reference
from Endpoints.data_manager import DataManager


def graphView():
    nodes = []
    links = []
    uuid_linker_tables = []
    id_linker_tables = []

    # Collect all objects that are valid right now (they function as source)
    for ep in endpoints:
        if not ep.Meta.graph_conf:
            continue
        else:
            title_field = ep.Meta.graph_conf
            uuid_linker_tables += [
                ref
                for _, ref in ep.Meta.references.items()
                if type(ref) == UUID_List_Reference
            ]
            id_linker_tables += [
                ref
                for _, ref in ep.Meta.references.items()
                if type(ref) == ID_List_Reference
            ]

            manager = DataManager(ep)
            node_list = [
                {"UUID": obj["UUID"], "Titel": obj[title_field]}
                for obj in manager.get_all(valid_only=True)
            ]

        if ep.Meta.status_conf:
            query = f"""SELECT UUID, Titel, '{ep.Meta.slug}' as Type FROM
                        (SELECT UUID, {title_field} as Titel, Row_number() OVER (partition BY [ID]
                        ORDER BY [Modified_date] DESC) [RowNumber]
                        FROM {ep.Meta.table}
                        WHERE {ep.Meta.status_conf[0]} = '{ep.Meta.status_conf[1]}' AND UUID != '00000000-0000-0000-0000-000000000000') T 
                    WHERE rownumber = 1"""
        else:
            query = f"""SELECT UUID, Titel, '{ep.Meta.slug}' as Type FROM
                        (SELECT UUID, {title_field} as Titel, Row_number() OVER (partition BY [ID]
                        ORDER BY [Modified_date] DESC) [RowNumber]
                        FROM {ep.Meta.table}
                        WHERE UUID != '00000000-0000-0000-0000-000000000000') T 
                    WHERE rownumber = 1"""

        with pyodbc.connect(db_connection_settings) as connection:
            cursor = connection.cursor()
            nodes = nodes + list(map(row_to_dict, cursor.execute(query)))

    # Store the UUIDs
    seen_uuids = [node["UUID"] for node in nodes]
    bbs_uuid_list = ", ".join(
        [f"'{node['UUID']}'" for node in nodes if node["Type"] == "beleidskeuzes"]
    )

    # Gather all the direct UUID links
    for ref in uuid_linker_tables:
        if ref.schema.Meta.graph_conf:
            title_field = ref.schema.Meta.graph_conf
        else:
            continue

        target_uuids = []
        query = f"""SELECT Beleidskeuze_UUID as source, {ref.their_col} as target, 'Koppeling' as type from {ref.link_tablename} WHERE Beleidskeuze_UUID IN ({bbs_uuid_list})"""

        with pyodbc.connect(db_connection_settings) as connection:
            cursor = connection.cursor()
            for link in map(row_to_dict, cursor.execute(query)):
                links.append(link)
                if not link["target"] in seen_uuids:
                    target_uuids.append(link["target"])

        # Add the missing targets
        if target_uuids:
            target_uuid_list = ", ".join([f"'{uuid}'" for uuid in target_uuids])
            query = f"""SELECT UUID, {title_field}, '{ref.schema.Meta.slug}' as Type FROM {ref.their_tablename} WHERE UUID IN ({target_uuid_list})"""
            with pyodbc.connect(db_connection_settings) as connection:
                cursor = connection.cursor()
                for node in map(row_to_dict, cursor.execute(query)):
                    nodes.append(node)

    # Gather all the direct ID links
    for ref in id_linker_tables:
        query = f"""SELECT Beleidskeuze_UUID as source,
                b.UUID as target,
                'Koppeling' as type
            FROM {ref.link_tablename}
            
            LEFT JOIN {ref.their_tablename} a ON a.UUID = {ref.their_col}
            
            JOIN (SELECT * FROM
			    (SELECT *, Row_number() OVER (partition BY [ID]
			        ORDER BY [Modified_date] DESC) [RowNumber]
			        FROM {ref.their_tablename}
			    WHERE UUID != '00000000-0000-0000-0000-000000000000') T 
            WHERE rownumber = 1) b ON b.ID = a.ID
            WHERE Beleidskeuze_UUID IN ({bbs_uuid_list})
            """
        # print(query)
        with pyodbc.connect(db_connection_settings) as connection:
            cursor = connection.cursor()
            for link in map(row_to_dict, cursor.execute(query)):
                if link["target"] in seen_uuids:
                    links.append(link)

    query = f"""SELECT Van_Beleidskeuze as source, Naar_Beleidskeuze as target, 'Relatie' as type from Beleidsrelaties WHERE Van_Beleidskeuze IN ({bbs_uuid_list}) AND Status = 'Akkoord' """
    with pyodbc.connect(db_connection_settings) as connection:
        cursor = connection.cursor()
        for link in map(row_to_dict, cursor.execute(query)):
            if link["target"] in seen_uuids:
                links.append(link)

    return {"nodes": nodes, "links": links}
