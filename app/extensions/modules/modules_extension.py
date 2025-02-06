from typing import Dict, List

from app.dynamic.converter import Converter
import app.extensions.modules.endpoints as endpoints
from app.dynamic.config.models import Column, ExtensionModel
from app.dynamic.endpoints.endpoint import EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.event_listeners import EventListeners
from app.dynamic.extension import Extension
from app.dynamic.generate_table import generate_table
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.modules.db.module_objects_tables import ModuleObjectsTable
from app.extensions.modules.db.table_extensions import extend_with_attributes
from app.extensions.modules.listeners import WerkingsgebiedRelatedObjectsListener
from app.extensions.modules.models.models import GenericModuleObjectShort, PublicModuleObjectRevision


class ModulesExtension(Extension):
    def register_tables(self, event_dispatcher: EventDispatcher, columns: Dict[str, Column]):
        generate_table(
            event_dispatcher,
            ModuleObjectsTable,
            "ModuleObjectsTable",
            columns,
            static=False,
        )
        # Additional orm properties for sqlalchemy
        extend_with_attributes()

    def register_endpoint_resolvers(
        self,
        event_listeners: EventListeners,
        models_resolver: ModelsResolver,
    ) -> List[EndpointResolver]:
        return [
            endpoints.CreateModuleEndpointResolver(),
            endpoints.ListModulesEndpointResolver(),
            endpoints.ModuleOverviewEndpointResolver(),
            endpoints.EditModuleEndpointResolver(),
            endpoints.ActivateModuleEndpointResolver(),
            endpoints.ModuleListStatusesEndpointResolver(),
            endpoints.ModulePatchStatusEndpointResolver(),
            endpoints.ModuleAddNewObjectEndpointResolver(),
            endpoints.ModuleAddExistingObjectEndpointResolver(),
            endpoints.ModuleGetObjectContextEndpointResolver(),
            endpoints.ModuleEditObjectContextEndpointResolver(),
            endpoints.ModuleRemoveObjectEndpointResolver(),
            endpoints.ModulePatchObjectEndpointResolver(),
            endpoints.ModuleSnapshotEndpointResolver(),
            endpoints.CloseModuleEndpointResolver(),
            endpoints.CompleteModuleEndpointResolver(),
            endpoints.ModuleListLineageTreeEndpointResolver(),
            endpoints.ModuleObjectLatestEndpointResolver(),
            endpoints.ModuleObjectVersionEndpointResolver(),
            endpoints.ListActiveModuleObjectsEndpointResolver(),
            endpoints.ListModuleObjectsEndpointResolver(),
            endpoints.PublicListModulesEndpointResolver(),
            endpoints.PublicModuleOverviewEndpointResolver(),
        ]

    def register_models(self, models_resolver: ModelsResolver):
        models_resolver.add(
            ExtensionModel(
                id="public_module_object_revision",
                name="PublicModuleObjectRevision",
                pydantic_model=PublicModuleObjectRevision,
            )
        )
        models_resolver.add(
            ExtensionModel(
                id="generic_module_object_short",
                name="GenericModuleObjectShort",
                pydantic_model=GenericModuleObjectShort,
            )
        )

    def register_listeners(
        self,
        main_config: dict,
        event_listeners: EventListeners,
        converter: Converter,
        models_resolver: ModelsResolver,
    ):
        event_listeners.register(WerkingsgebiedRelatedObjectsListener())
