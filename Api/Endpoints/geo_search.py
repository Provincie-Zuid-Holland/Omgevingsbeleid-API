from flask import jsonify, request

from Api.Endpoints.data_manager import DataManager
from Api.Endpoints.search import start_search, ArgException
from Api.datamodel import endpoints


def geo_search_view():
    """
    Find all objects linked to geo areas specified in query
    """
    try:
        query, type_exclude, type_only, limit, offset = start_search(request.args)
    except ArgException as e:
        return {"message": str(e)}, 403

    searchables = [ep for ep in endpoints if ep.Meta.geo_searchable]

    if type_only:
        searchables = [ep for ep in searchables if ep.Meta.slug in type_only]
    elif type_exclude:
        searchables = [ep for ep in searchables if ep.Meta.slug not in type_exclude]

    if not searchables:
        return {"Message": "No objects to search after applying filters"}, 400

    search_results = []

    for ep in searchables:
        manager = DataManager(ep)
        try:
            results = manager.geo_search(query)
            if results:
                search_results = search_results + results
        except ValueError as e:
            return {"Message": "Unable to parse UUID"}, 400

    return jsonify(search_results[offset:limit])
