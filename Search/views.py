from flask import Flask, jsonify, request
from datamodel import dimensies_and_feiten
from elasticsearch_dsl import Index, Keyword, Mapping, Nested, TermsFacet, connections, Search
from elasticsearch import Elasticsearch


def splitlist(value):
    value = value.replace(' ', '')
    return value.split(',')


def search():
    query = request.args.get('query', default=None, type=str)
    type_exclude = request.args.get('exclude', default=None, type=splitlist)
    type_only = request.args.get('only', default=None, type=splitlist)
    if type_exclude and type_only:
        return jsonify({"message": "Using exclude and only together is not allowed"}), 403
    if not query:
        return jsonify({"message": "Missing or invalid URL parameter 'query'"}), 400
    else:
        indices_possible = ', '.join([dim['slug'] for dim in dimensies_and_feiten()])
        indices = [dim['slug'] for dim in dimensies_and_feiten()]
        if type_exclude:
            for t in type_exclude:
                try:
                    indices.remove(t)
                except ValueError:
                    return jsonify({"message": f"Invalid type to exclude '{t}', possible options are: {indices_possible}'"}), 400
        elif type_only:
            for t in type_only:
                try:
                    indices.index(t)
                except ValueError:
                    return jsonify({"message": f"Invalid type to include '{t}', possible options are: {indices_possible}'"}), 400
            indices = type_only

        s = Search(index=indices)
        s = s.highlight('*', pre_tags=['<em class="search-highlight">'], post_tags=['</em>'])
        sq = s.query("multi_match", fields='*', query=query, fuzziness='AUTO', analyzer='dutch')
        res = sq.execute()
    return jsonify([{**hit.to_dict(), **{key : value for key, value in hit.meta.to_dict().items() if key not in ['id', 'doc_type']}} for hit in res])
