from flask_restful import Api as RestfulApi
from flask import request
from functools import wraps
from flask_jwt_extended import verify_jwt_in_request

from Api.settings import current_version
import Api.datamodel
import Api.Endpoints.endpoint
import Api.Models
from Api.Models import gebruikers, verordeningsstructuur, beleidskeuzes, maatregelen, onderverdeling
from Api.Auth.views import login, password_reset, tokenstat
from Api.Spec.spec import specView
from Api.Endpoints.search import search_view
from Api.Endpoints.edits import editView
from Api.Endpoints.geo_search import geo_search_view
from Api.Endpoints.graph import graphView


def jwt_required_not_GET(fn):
    """
    Only requires a JWT on a non GET request
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if request.method != "GET":
            verify_jwt_in_request()
            return fn(*args, **kwargs)
        else:
            return fn(*args, **kwargs)

    return wrapper


def create_api(app):
    api = RestfulApi(
        prefix=f"/v{current_version}",
        decorators=[
            jwt_required_not_GET,
        ],
    )

    # ROUTING RULES
    for schema in Api.datamodel.endpoints:
        api.add_resource(
            schema.Meta.lineage_endpoint_cls,
            f"/{schema.Meta.slug}/<int:id>",
            endpoint=f"{schema.Meta.slug.capitalize()}_Lineage",
            resource_class_args=(schema,),
        )

        api.add_resource(
            schema.Meta.fulllist_endpoint_cls,
            f"/{schema.Meta.slug}",
            endpoint=f"{schema.Meta.slug.capitalize()}_List",
            resource_class_args=(schema,),
        )

        api.add_resource(
            schema.Meta.validlist_endpoint_cls,
            f"/valid/{schema.Meta.slug}",
            endpoint=f"{schema.Meta.slug.capitalize()}_Validlist",
            resource_class_args=(schema,),
        )

        api.add_resource(
            schema.Meta.validlineage_endpoint_cls,
            f"/valid/{schema.Meta.slug}/<int:id>",
            endpoint=f"{schema.Meta.slug.capitalize()}_Validlineage",
            resource_class_args=(schema,),
        )

        api.add_resource(
            schema.Meta.singleversion_endpoint_cls,
            f"/version/{schema.Meta.slug}/<string:uuid>",
            endpoint=f"{schema.Meta.slug.capitalize()}_Version",
            resource_class_args=(schema,),
        )

        api.add_resource(
            schema.Meta.changes_endpoint_cls,
            f"/changes/{schema.Meta.slug}/<string:old_uuid>/<string:new_uuid>",
            endpoint=f"{schema.Meta.slug.capitalize()}_Changes",
            resource_class_args=(schema,),
        )

    app.add_url_rule(f"/v{current_version}/login", "login", login, methods=["POST"])

    app.add_url_rule(
        f"/v{current_version}/password-reset",
        "password-reset",
        password_reset,
        methods=["POST"],
    )

    app.add_url_rule(
        f"/v{current_version}/tokeninfo", "tokenstat", tokenstat, methods=["GET"]
    )
    api.add_resource(
        gebruikers.Gebruiker, "/gebruikers", "/gebruikers/<string:gebruiker_uuid>"
    )
    api.add_resource(
        verordeningsstructuur.Verordening_Structuur,
        "/verordeningstructuur",
        "/verordeningstructuur/<int:verordeningstructuur_id>",
        "/verordeningstructuur/version/<uuid:verordeningstructuur_uuid>",
    )
    app.add_url_rule(f"/v{current_version}/spec", "spec", specView, methods=["GET"])

    app.add_url_rule(f"/v{current_version}/search", "search", search_view, methods=["GET"])

    api.add_resource(
        editView,
        f"/edits",
        endpoint="edits",
        resource_class_args=(
            [beleidskeuzes.Beleidskeuzes_Schema, maatregelen.Maatregelen_Schema],
        ),
    )

    app.add_url_rule(f"/v{current_version}/search/geo", "geo-search", geo_search_view, methods=["GET", "POST"])

    app.add_url_rule(f"/v{current_version}/graph", "graph", graphView, methods=["GET"])

    app.add_url_rule(
        f"/v{current_version}/ts_defs",
        "ts_defs",
        Api.datamodel.generate_typescript_defs,
        methods=["GET"],
    )

    return api
