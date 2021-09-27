from flask import Flask, jsonify, request
from Endpoints.data_manager import DataManager
from Endpoints.search import start_search
from datamodel import endpoints

def geo_search_view():
    """
    Find all objects linked to geo areas specified in query
    """
    query, type_exclude, type_only, limit = start_search(request.args)

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
        results = manager.geo_search(query)
        if results:
            search_results = search_results + results

    return jsonify(search_results[:limit])