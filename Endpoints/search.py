# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

from Endpoints.data_manager import DataManager
from flask import Flask, jsonify, request
from datamodel import endpoints
from globals import row_to_dict, db_connection_settings
import pyodbc


def splitlist(value):
    """
    Function that splits list of query arguments into python lists
    """
    value = value.replace(" ", "")
    return value.split(",")


def start_search(args):
    """
    A view that accepts search queries to find object based on a fuzzy text match
    """
    query = args.get("query", default=None, type=str)
    type_exclude = args.get("exclude", default=None, type=splitlist)
    type_only = args.get("only", default=None, type=splitlist)
    limit = args.get("limit", default=10, type=int)

    if not query:
        return jsonify({"message": "No search query provided."}), 400

    if type_exclude and type_only:
        return (
            jsonify({"message": "Using exclude and only together is not allowed"}),
            403,
        )
    return (query, type_exclude, type_only, limit)


def search_view():
    """
    A view that accepts search queries to find object based on a fuzzy text match
    """
    query, type_exclude, type_only, limit = start_search(request.args)

    searchables = [ep for ep in endpoints if ep.Meta.searchable]

    if type_only:
        searchables = [ep for ep in searchables if ep.Meta.slug in type_only]
    elif type_exclude:
        searchables = [ep for ep in searchables if ep.Meta.slug not in type_exclude]

    if not searchables:
        return {"Message": "No objects to search after applying filters"}, 400

    search_results = []

    for ep in searchables:
        manager = DataManager(ep)
        results = manager.search(query)
        if results:
            search_results = search_results + results

    # Sort the results
    search_results = sorted(search_results, key=lambda r: r["RANK"], reverse=True)

    return jsonify(search_results[:limit])
