from flask_restful import Api as RestfulApi

from Api.settings import current_version
import Api.datamodel
import Api.Endpoints.endpoint
import Api.Models


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


api = RestfulApi(
    prefix=f"/v{current_version}",
    decorators=[
        jwt_required_not_GET,
    ],
)

# ROUTING RULES
for schema in Api.datamodel.endpoints:
    api.add_resource(
        Api.Endpoints.endpoint.Lineage,
        f"/{schema.Meta.slug}/<int:id>",
        endpoint=f"{schema.Meta.slug.capitalize()}_Lineage",
        resource_class_args=(schema,),
    )

    api.add_resource(
        Api.Endpoints.endpoint.FullList,
        f"/{schema.Meta.slug}",
        endpoint=f"{schema.Meta.slug.capitalize()}_List",
        resource_class_args=(schema,),
    )

    api.add_resource(
        Api.Endpoints.endpoint.ValidList,
        f"/valid/{schema.Meta.slug}",
        endpoint=f"{schema.Meta.slug.capitalize()}_Validlist",
        resource_class_args=(schema,),
    )

    api.add_resource(
        Api.Endpoints.endpoint.ValidLineage,
        f"/valid/{schema.Meta.slug}/<int:id>",
        endpoint=f"{schema.Meta.slug.capitalize()}_Validlineage",
        resource_class_args=(schema,),
    )

    api.add_resource(
        Api.Endpoints.endpoint.SingleVersion,
        f"/version/{schema.Meta.slug}/<string:uuid>",
        endpoint=f"{schema.Meta.slug.capitalize()}_Version",
        resource_class_args=(schema,),
    )

    api.add_resource(
        Api.Endpoints.endpoint.Changes,
        f"/changes/{schema.Meta.slug}/<string:old_uuid>/<string:new_uuid>",
        endpoint=f"{schema.Meta.slug.capitalize()}_Changes",
        resource_class_args=(schema,),
    )


api.add_url_rule(f"/v{current_version}/login", "login", login, methods=["POST"])

api.add_url_rule(
    f"/v{current_version}/password-reset",
    "password-reset",
    password_reset,
    methods=["POST"],
)

api.add_url_rule(
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
api.add_url_rule(f"/v{current_version}/spec", "spec", specView, methods=["GET"])

api.add_url_rule(f"/v{current_version}/search", "search", search_view, methods=["GET"])

api.add_resource(
    editView,
    f"/edits",
    endpoint="edits",
    resource_class_args=(
        [beleidskeuzes.Beleidskeuzes_Schema, maatregelen.Maatregelen_Schema],
    ),
)


api.add_url_rule(
    f"/v{current_version}/search/geo", "geo-search", geo_search_view, methods=["GET"]
)

api.add_url_rule(f"/v{current_version}/graph", "graph", graphView, methods=["GET"])

api.add_url_rule(
    f"/v{current_version}/ts_defs",
    "ts_defs",
    datamodel.generate_typescript_defs,
    methods=["GET"],
)
