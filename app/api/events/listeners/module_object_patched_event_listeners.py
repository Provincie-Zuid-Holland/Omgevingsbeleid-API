from typing import List, Optional, Set

from sqlalchemy.orm import Session

from app.api.domains.werkingsgebieden.services.change_area_processor import (
    AreaProcessorConfig,
    AreaProcessorService,
    AreaProcessorServiceFactory,
)
from app.api.events.module_object_patched_event import ModuleObjectPatchedEvent
from app.core.services.event.types import Listener
from app.core.types import DynamicObjectModel, Model


class ChangeAreaListener(Listener[ModuleObjectPatchedEvent]):
    def __init__(self, service_factory: AreaProcessorServiceFactory):
        self._service_factory: AreaProcessorServiceFactory = service_factory

    def handle_event(self, session: Session, event: ModuleObjectPatchedEvent) -> Optional[ModuleObjectPatchedEvent]:
        config: Optional[AreaProcessorConfig] = self._collect_config(event.context.request_model)
        if not config:
            return event

        area_processor: AreaProcessorService = self._service_factory.create_service(session, config)
        new_record = area_processor.process(
            event.context.old_record,
            event.payload.new_record,
        )

        event.payload.new_record = new_record
        return event

    def _collect_config(self, event: ModuleObjectPatchedEvent) -> Optional[AreaProcessorConfig]:
        request_model: Model = event.context.request_model
        if not isinstance(request_model, DynamicObjectModel):
            return None
        if not "change_area" in request_model.service_config:
            return None

        config_dict: dict = request_model.service_config.get("change_area", {})
        fields: List[str] = []
        for field in config_dict.get("fields", []):
            if not isinstance(field, str):
                raise RuntimeError("Invalid change_area config, expect `fields` to be a list of strings")
            fields.append(field)
        if not fields:
            return None

        changed_fields: Set[str] = set(event.context.changes.keys())
        interested_fields: Set[str] = set.intersection(fields, changed_fields)
        if not interested_fields:
            return None

        config = AreaProcessorConfig(fields=set(fields))
        return config
