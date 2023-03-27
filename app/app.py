from app.core.settings import settings
from app.dynamic.dynamic_app import DynamicAppBuilder
from app.extensions.database_migration.database_migration_extension import (
    DatabaseMigrationExtension,
)
from app.extensions.html_assets.html_assets_extension import HtmlAssetsExtension
from app.extensions.lineage_resolvers.lineageresolvers_extension import (
    LineageResolversExtension,
)
from app.extensions.mssql_search.mssql_search_extension import MssqlSearchExtension
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
# app_builder.register_extension(SearchExtension())
app_builder.register_extension(MssqlSearchExtension())
# app_builder.register_extension(GeoSearchExtension())
app_builder.register_extension(ModulesExtension())
app_builder.register_extension(AcknowledgedRelationsExtension())
app_builder.register_extension(HtmlAssetsExtension())
# app_builder.register_extension(ModulesPdfExportExtension())
# app_builder.register_extension(ModulesXMLExportExtension())
app_builder.register_extension(DatabaseMigrationExtension())

# Register the dynamic objects
app_builder.register_objects(settings.OBJECT_CONFIG_PATH)

# We can generate the data after all objects are registered
# this is because objects can have references to eachother
dynamic_app = app_builder.build()
