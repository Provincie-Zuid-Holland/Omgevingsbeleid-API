from flask import Flask, jsonify, request

from Api.Endpoints.data_manager import DataManager
from Api.Endpoints.search import start_search, ArgException, search_view_generic
from Api.datamodel import endpoints


def geo_search_view():
    return search_view_generic(lambda ep, query: ep.Meta.manager(ep).geo_search(query))