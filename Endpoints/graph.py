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
    valid_uuids = []

    # Collect all objects that are valid right now (they function as source)
    for ep in endpoints:
        if not ep.Meta.graph_conf:
            continue
        else:
            title_field = ep.Meta.graph_conf
            manager = DataManager(ep)
            valid_objects = manager.get_all(valid_only=True)
            nodes += [
                {
                    "UUID": obj["UUID"],
                    "Titel": obj[title_field],
                    "Type": ep.Meta.slug,
                }
                for obj in valid_objects
            ]

            valid_uuids += [obj["UUID"] for obj in valid_objects]

            for obj in valid_objects:
                for ref_field, ref in ep.Meta.references.items():
                    if obj.get(ref_field):
                        if type(ref) == UUID_List_Reference:
                            for link in obj.get(ref_field):
                                links.append(
                                    {
                                        "source": obj["UUID"],
                                        "target": link["Object"]["UUID"],
                                        "type": "Koppeling",
                                    }
                                )
    valid_links = []
    for link in links:
        if link["target"] in valid_uuids:
            valid_links.append(link)

    return {"nodes": nodes, "links": valid_links}
