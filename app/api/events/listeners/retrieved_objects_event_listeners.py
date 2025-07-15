import uuid
from typing import Generic, List, Optional, TypeVar, Union

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.domains.modules.services.add_public_revisions_service import (
    AddPublicRevisionsConfig,
    AddPublicRevisionsService,
    AddPublicRevisionsServiceFactory,
)
from app.api.domains.modules.types import PublicModuleStatusCode
from app.api.domains.objects.services.add_next_object_version_service import (
    AddNextObjectVersionConfig,
    AddNextObjectVersionService,
    AddNextObjectVersionServiceFactory,
)
from app.api.domains.objects.services.add_relations_service import AddRelationsService, AddRelationsServiceFactory
from app.api.domains.objects.services.add_werkingsgebied_related_objects_service import (
    AddWerkingsgebiedRelatedObjectsConfig,
    AddWerkingsgebiedRelatedObjectsService,
    AddWerkingsgebiedRelatedObjectsServiceFactory,
)
from app.api.domains.objects.services.column_image_inserter import (
    ColumnImageInserter,
    ColumnImageInserterFactory,
    GetImagesConfig,
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

    def handle_event(self, session: Session, event: RetrievedObjectsEvent) -> Optional[RetrievedObjectsEvent]:
        add_service: AddRelationsService = self._relations_factory.create_service(
            session,
            event.payload.rows,
            event.context.response_model,
        )

        result_rows: List[BaseModel] = add_service.add_relations()
        event.payload.rows = result_rows

        return event


class JoinWerkingsgebiedenToObjectsListener(Listener[RetrievedObjectsEvent]):
    def __init__(self, service_factory: JoinWerkingsgebiedenServiceFactory):
        self._service_factory: JoinWerkingsgebiedenServiceFactory = service_factory

    def handle_event(self, session: Session, event: RetrievedObjectsEvent) -> Optional[RetrievedObjectsEvent]:
        join_service: JoinWerkingsgebiedenService = self._service_factory.create_service(
            session,
            event.payload.rows,
            event.context.response_model,
        )

        result_rows: List[BaseModel] = join_service.join_werkingsgebieden()
        event.payload.rows = result_rows

        return event


class AddPublicRevisionsToObjectsListener(Listener[RetrievedObjectsEvent]):
    def __init__(self, service_factory: AddPublicRevisionsServiceFactory):
        self._service_factory: AddPublicRevisionsServiceFactory = service_factory

    def handle_event(self, session: Session, event: RetrievedObjectsEvent) -> Optional[RetrievedObjectsEvent]:
        config: Optional[AddPublicRevisionsConfig] = self._collect_config(event)
        if not config:
            return event

        service: AddPublicRevisionsService = self._service_factory.create_service(
            session,
            config,
            event.payload.rows,
        )

        result_rows: List[BaseModel] = service.add_revisions()
        event.payload.rows = result_rows

        return event

    def _collect_config(self, event: RetrievedObjectsEvent) -> Optional[AddPublicRevisionsConfig]:
        if not isinstance(event.context.response_model, DynamicObjectModel):
            return None
        if "public_revisions" not in event.context.response_model.service_config:
            return None

        service_config: dict = event.context.response_model.service_config["public_revisions"]
        to_field: str = service_config["to_field"]

        object_codes: List[str] = list({getattr(r, "Code") for r in event.payload.rows})

        return AddPublicRevisionsConfig(
            to_field=to_field,
            object_codes=object_codes,
            allowed_status_list=PublicModuleStatusCode.values(),
        )


class AddNextObjectVersionToObjectsListener(Listener[RetrievedObjectsEvent]):
    def __init__(self, service_factory: AddNextObjectVersionServiceFactory):
        self._service_factory: AddNextObjectVersionServiceFactory = service_factory

    def handle_event(self, session: Session, event: RetrievedObjectsEvent) -> Optional[RetrievedObjectsEvent]:
        config: Optional[AddNextObjectVersionConfig] = self._collect_config(event)
        if not config:
            return event

        service: AddNextObjectVersionService = self._service_factory.create_service(
            session,
            config,
            event.payload.rows,
        )

        result_rows: List[BaseModel] = service.add_next_versions()
        event.payload.rows = result_rows

        return event

    def _collect_config(self, event: RetrievedObjectsEvent) -> Optional[AddNextObjectVersionConfig]:
        if not isinstance(event.context.response_model, DynamicObjectModel):
            return None
        if "next_object_version" not in event.context.response_model.service_config:
            return None

        service_config: dict = event.context.response_model.service_config["next_object_version"]
        to_field: str = service_config["to_field"]

        object_uuids: List[uuid.UUID] = list({getattr(r, "UUID") for r in event.payload.rows})

        return AddNextObjectVersionConfig(
            to_field=to_field,
            object_uuids=object_uuids,
        )


class AddWerkingsgebiedRelatedObjectsToObjectsListener(Listener[RetrievedObjectsEvent]):
    def __init__(self, service_factory: AddWerkingsgebiedRelatedObjectsServiceFactory):
        self._service_factory: AddWerkingsgebiedRelatedObjectsServiceFactory = service_factory

    def handle_event(self, session: Session, event: RetrievedObjectsEvent) -> Optional[RetrievedObjectsEvent]:
        config: Optional[AddWerkingsgebiedRelatedObjectsConfig] = self._collect_config(event)
        if not config:
            return event

        service: AddWerkingsgebiedRelatedObjectsService = self._service_factory.create_service(
            session,
            config,
            event.payload.rows,
        )

        result_rows: List[BaseModel] = service.add_related_objects()
        event.payload.rows = result_rows

        return event

    def _collect_config(self, event: RetrievedObjectsEvent) -> Optional[AddWerkingsgebiedRelatedObjectsConfig]:
        if not isinstance(event.context.response_model, DynamicObjectModel):
            return None
        if "werkingsgebied_related_objects" not in event.context.response_model.service_config:
            return None

        service_config: dict = event.context.response_model.service_config["werkingsgebied_related_objects"]
        to_field: str = service_config["to_field"]

        werkingsgebied_codes: List[str] = list({getattr(r, "Code") for r in event.payload.rows})

        return AddWerkingsgebiedRelatedObjectsConfig(
            to_field=to_field,
            werkingsgebied_codes=werkingsgebied_codes,
        )


EventRMO = TypeVar("EventRMO", bound=Union[RetrievedObjectsEvent, RetrievedModuleObjectsEvent])


class GetColumnImagesListenerBase(Listener[EventRMO], Generic[EventRMO]):
    def __init__(self, service_factory: ColumnImageInserterFactory):
        self._service_factory: ColumnImageInserterFactory = service_factory

    def handle_event(self, session: Session, event: EventRMO) -> Optional[EventRMO]:
        config: Optional[GetImagesConfig] = self._collect_config(event.context.response_model)
        if not config:
            return event
        if not config.fields:
            return event

        inserter: ColumnImageInserter = self._service_factory.create_service(
            session,
            event.payload.rows,
            config,
        )
        result_rows = inserter.process()

        event.payload.rows = result_rows
        return event

    def _collect_config(self, request_model: Model) -> Optional[GetImagesConfig]:
        if not isinstance(request_model, DynamicObjectModel):
            return None
        if "get_image" not in request_model.service_config:
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
