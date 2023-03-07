from typing import Dict, List
from app.dynamic.config.models import Column

from app.dynamic.extension import Extension
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import EndpointResolver
from app.extensions.modules.db.module_objects_table import (
    generate_dynamic_module_objects,
)
import app.extensions.modules.endpoints as endpoints


class ModulesExtension(Extension):
    def register_tables(self, columns: Dict[str, Column]):
        generate_dynamic_module_objects(columns)

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
        ]
