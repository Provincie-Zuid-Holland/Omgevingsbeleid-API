from typing import Generic, List, Optional, TypeVar, Union

from pydantic import BaseModel

from app.api.domains.objects.services.add_relations import AddRelationsService, AddRelationsServiceFactory
from app.api.domains.objects.services.column_image_inserter import (
    ColumnImageInserter,
    ColumnImageInserterFactory,
    GetImagesConfig,
)
from app.api.domains.objects.services.html_images_inserter import (
    HtmlImagesInserter,
    HtmlImagesInserterFactory,
    InsertHtmlImagesConfig,
)
from app.api.domains.werkingsgebieden.services.join_werkingsgebieden import (
    JoinWerkingsgebiedenService,
    JoinWerkingsgebiedenServiceFactory,
)
from app.api.events.retrieved_module_objects_event import RetrievedModuleObjectsEvent
from app.api.events.retrieved_objects_event import RetrievedObjectsEvent
from app.core.services.event.types import Listener
from app.core.types import DynamicObjectModel, Model


class AddRelationsToObjectsListener(Listener[RetrievedObjectsEvent]):
    def __init__(self, relations_factory: AddRelationsServiceFactory):
        self._relations_factory: AddRelationsServiceFactory = relations_factory

    def handle_event(self, event: RetrievedObjectsEvent) -> Optional[RetrievedObjectsEvent]:
        add_service: AddRelationsService = self._relations_factory.create_service(
            event.payload.rows,
            event.context.response_model,
        )

        result_rows: List[BaseModel] = add_service.add_relations()
        event.payload.rows = result_rows

        return event


class JoinWerkingsgebeidenToObjectsListener(Listener[RetrievedObjectsEvent]):
    def __init__(self, service_factory: JoinWerkingsgebiedenServiceFactory):
        self._service_factory: JoinWerkingsgebiedenServiceFactory = service_factory

    def handle_event(self, event: RetrievedObjectsEvent) -> Optional[RetrievedObjectsEvent]:
        join_service: JoinWerkingsgebiedenService = self._service_factory.create_service(
            event.payload.rows,
            event.context.response_model,
        )

        result_rows: List[BaseModel] = join_service.join_werkingsgebieden()
        event.payload.rows = result_rows

        return event


EventRMO = TypeVar("EventRMO", bound=Union[RetrievedObjectsEvent, RetrievedModuleObjectsEvent])


class InsertHtmlImagesListenerBase(Listener[EventRMO], Generic[EventRMO]):
    def __init__(self, service_factory: HtmlImagesInserterFactory):
        self._service_factory: HtmlImagesInserterFactory = service_factory

    def handle_event(self, event: EventRMO) -> Optional[EventRMO]:
        config: Optional[InsertHtmlImagesConfig] = self._collect_config(event.context.response_model)
        if not config or not config.fields:
            return event

        inserter: HtmlImagesInserter = self._service_factory.create_service(event.payload.rows, config)
        event.payload.rows = inserter.process()

        return event

    def _collect_config(self, request_model: Model) -> Optional[InsertHtmlImagesConfig]:
        if not isinstance(request_model, DynamicObjectModel):
            return None
        if not "insert_assets" in request_model.service_config:
            return None

        config_dict: dict = request_model.service_config.get("insert_assets", {})
        fields: List[str] = []
        for field in config_dict.get("fields", []):
            if not isinstance(field, str):
                raise RuntimeError("Invalid insert_assets config, expect `fields` to be a list of strings")
            fields.append(field)
        if not fields:
            return None

        config: InsertHtmlImagesConfig = InsertHtmlImagesConfig(
            fields=set(fields),
        )
        return config


class InsertHtmlImagesForObjectListener(InsertHtmlImagesListenerBase[RetrievedObjectsEvent]):
    pass


class GetColumnImagesListenerBase(Listener[EventRMO], Generic[EventRMO]):
    def __init__(self, service_factory: ColumnImageInserterFactory):
        self._service_factory: ColumnImageInserterFactory = service_factory

    def handle_event(self, event: EventRMO) -> Optional[EventRMO]:
        config: Optional[GetImagesConfig] = self._collect_config(event.context.response_model)
        if not config:
            return event
        if not config.fields:
            return event

        inserter: ColumnImageInserter = self._service_factory.create_service(
            event.payload.rows,
            config,
        )
        result_rows = inserter.process()

        event.payload.rows = result_rows
        return event

    def _collect_config(self, request_model: Model) -> Optional[GetImagesConfig]:
        if not isinstance(request_model, DynamicObjectModel):
            return None
        if not "get_image" in request_model.service_config:
            return None

        config_dict: dict = request_model.service_config.get("get_image", {})
        fields: List[str] = []
        for field in config_dict.get("fields", []):
            if not isinstance(field, str):
                raise RuntimeError("Invalid get_image config, expect `fields` to be a list of strings")
            fields.append(field)
        if not fields:
            return None

        config: GetImagesConfig = GetImagesConfig(
            fields=set(fields),
        )
        return config


class GetColumnImagesForObjectListener(GetColumnImagesListenerBase[RetrievedObjectsEvent]):
    pass
