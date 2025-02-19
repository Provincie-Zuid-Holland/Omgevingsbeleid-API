from typing import Dict, List

from sqlalchemy import Select, String
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm.session import Session, object_session

from app.dynamic.config.models import Column, ComputedField, ExtensionModel
from app.dynamic.converter import Converter
from app.dynamic.db.tables import ObjectStaticsTable
from app.dynamic.endpoints.endpoint import EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.event_listeners import EventListeners
from app.dynamic.extension import Extension
from app.dynamic.generate_table import generate_table
from app.dynamic.models_resolver import ModelsResolver

import app.extensions.modules.endpoints as endpoints
from app.extensions.modules.db.module_objects_tables import ModuleObjectsTable
from app.extensions.modules.listeners import WerkingsgebiedRelatedObjectsListener
from app.extensions.modules.models.models import (
    PublicModuleObjectRevision,
    WerkingsgebiedRelatedObjects,
)
from app.extensions.modules.db.public_revisions import build_object_public_revisions_property


class ModulesExtension(Extension):
    def register_tables(self, event_dispatcher: EventDispatcher, columns: Dict[str, Column]):
        generate_table(
            event_dispatcher,
            ModuleObjectsTable,
            "ModuleObjectsTable",
            columns,
            static=False,
        )
        setattr(ObjectStaticsTable, "Cached_Title", mapped_column("Cached_Title", String(255), nullable=True))

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
    #     models_resolver.add(
    #         ExtensionModel(
    #             id="werkingsgebied_related_objects",
    #             name="WerkingsgebiedRelatedObjects",
    #             pydantic_model=WerkingsgebiedRelatedObjects,
    #         )
    #     )

    def register_computed_fields(self) -> List[ComputedField]:
        public_revisions_property = build_object_public_revisions_property()
        public_revisions_field = ComputedField(
            id="public_revisions",
            model_id="public_module_object_revision",
            attribute_name="Public_Revisions",
            action=public_revisions_property,
            is_optional=True,
            is_list=True,
        )
        return [public_revisions_field]

    # def register_listeners(
    #     self,
    #     main_config: dict,
    #     event_listeners: EventListeners,
    #     converter: Converter,
    #     models_resolver: ModelsResolver,
    # ):
    #     event_listeners.register(WerkingsgebiedRelatedObjectsListener())
