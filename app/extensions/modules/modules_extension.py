from typing import Dict, List

import app.extensions.modules.endpoints as endpoints
from app.dynamic.config.models import Column
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.extension import Extension
from app.dynamic.generate_table import generate_table
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.modules.db.module_objects_tables import ModuleObjectsTable
from app.extensions.modules.db.table_extensions import extend_with_attributes


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
        event_dispatcher: EventDispatcher,
        converter: Converter,
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
