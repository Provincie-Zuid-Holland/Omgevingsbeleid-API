import logging
import sys

from fastapi import FastAPI
from fastapi.responses import JSONResponse
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


@app.exception_handler(sqlalchemy.exc.IntegrityError)
async def http_exception_handler(request, exc):
    return JSONResponse(
        {
            "msg": "Foreign key error",
            "__debug__exception": str(exc),
        },
        status_code=400,
    )


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
