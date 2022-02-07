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


class ArgException(Exception):
    pass


def start_search(args):
    """
    A view that accepts search queries to find object based on a fuzzy text match
    """
    query = args.get("query", default=None, type=str)
    type_exclude = args.get("exclude", default=None, type=splitlist)
    type_only = args.get("only", default=None, type=splitlist)
    limit = args.get("limit", default=10, type=int)
    offset = args.get("offset", default=0, type=int)

    if not query:
        raise ArgException("No search query provided.")

    if type_exclude and type_only:
        raise ArgException("Using exclude and only together is not allowed")

    if limit <= 0:
        raise ArgException("Limit must be a positive integer and not equal to zero")

    if offset < 0:
        raise ArgException("Offset must be a positive integer or zero")

    return (query, type_exclude, type_only, limit, offset)


def search_view():
    """
    A view that accepts search queries to find object based on a fuzzy text match
    """
    try:
        query, type_exclude, type_only, limit, offset = start_search(request.args)
    except ArgException as e:
        return {"message": str(e)}, 403

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

    return jsonify(search_results[offset:(offset+ limit)])