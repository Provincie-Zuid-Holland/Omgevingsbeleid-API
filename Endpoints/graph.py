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
            valid_objects = manager.get_all(valid_only=True) 
            nodes.append([
                {'UUID': obj['UUID'], 'Titel': obj[title_field], 'Type':ep.Meta.slug}
                for obj in valid_objects
            ])
            

    
    return {"nodes": nodes, "links": links}
