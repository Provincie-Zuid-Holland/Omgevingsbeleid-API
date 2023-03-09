import logging
import sys

from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
import sqlalchemy.exc
import uvicorn

from app.core.settings import settings
from app.dynamic.dynamic_app import DynamicAppBuilder
from app.extensions.html_assets.html_assets_extension import HtmlAssetsExtension
from app.extensions.lineage_resolvers.lineageresolvers_extension import (
    LineageResolversExtension,
)
from app.extensions.modules_pdf_export.modules_pdf_export_extension import (
    ModulesPdfExportExtension,
)
from app.extensions.modules_xml_export.modules_xml_export_extension import (
    ModulesXMLExportExtension,
)
from app.extensions.search.search_extension import SearchExtension
from app.extensions.users.users_extension import UsersExtension
from app.extensions.users.users_extension import UsersExtension
from app.extensions.auth.auth_extension import AuthExtension
from app.extensions.extended_users.extended_user_extension import ExtendedUserExtension
from app.extensions.relations.relations_extension import RelationsExtension
from app.extensions.werkingsgebieden.werkingsgebieden_extension import (
    WerkingsgebiedenExtension,
)
from app.extensions.modules.modules_extension import ModulesExtension
from app.extensions.acknowledged_relations.acknowledged_relations_extension import (
    AcknowledgedRelationsExtension,
)

app_builder = DynamicAppBuilder(settings.MAIN_CONFIG_FILE)

app_builder.register_extension(LineageResolversExtension())
app_builder.register_extension(UsersExtension())
app_builder.register_extension(AuthExtension())
app_builder.register_extension(ExtendedUserExtension())
app_builder.register_extension(RelationsExtension())
app_builder.register_extension(WerkingsgebiedenExtension())
app_builder.register_extension(SearchExtension())
# app_builder.register_extension(GeoSearchExtension())
app_builder.register_extension(ModulesExtension())
app_builder.register_extension(AcknowledgedRelationsExtension())
app_builder.register_extension(ModulesPdfExportExtension())
app_builder.register_extension(ModulesXMLExportExtension())
app_builder.register_extension(HtmlAssetsExtension())

# Register the dynamic objects
app_builder.register_objects(settings.OBJECT_CONFIG_PATH)

# We can generate the data after all objects are registered
# this is because objects can have references to eachother
dynamic_app = app_builder.build()
app: FastAPI = dynamic_app.run()


"""

    @TODO: all fastapi functions below should be moved to extensions etc

"""


@app.exception_handler(sqlalchemy.exc.IntegrityError)
async def http_exception_handler(request, exc):
    return JSONResponse(
        {
            "msg": "Foreign key error",
            "__debug__exception": str(exc),
        },
        status_code=400,
    )


def set_operator_id_from_unique_id(app: FastAPI) -> None:
    """
    The prefix of the operator_id is currently the function name of the route,
    which is undesirable for the Frontend as it results in cluttered auto-generated names.
    As a temporary solution, we are generating the operation_id from the unique_id and
    eliminating the function name. However, this approach is not sustainable if
    we transition to an open-source platform.

    @todo: we should use the generate_unique_id_function in adding the endpoint instead
    """
    for route in app.routes:
        if isinstance(route, APIRoute):
            route.operation_id = route.unique_id.replace("fastapi_handler_", "", 1)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=settings.PROJECT_NAME,
        version=settings.PROJECT_VERSION,
        description=settings.PROJECT_DESC,
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {"url": settings.OPENAPI_LOGO}
    app.openapi_schema = openapi_schema
    return app.openapi_schema


set_operator_id_from_unique_id(app)
app.openapi = custom_openapi


# Logging
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Allow starting app from main file
    # primarily to setup extra DebugPy instance
    host = sys.argv[1]
    port = int(sys.argv[2])

    # dap_port = int(sys.argv[3])
    # logger.info("---Initializing Debug application and DAP server---")
    # logger.info("Socket serving debug Application: ", host, port)
    # logger.info("DAP server listening on socket: ", host, dap_port)
    # debugpy.listen((host, dap_port))

    uvicorn.run(app, host=host, port=port)
