import uuid

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.domains.modules.services.add_public_revisions_service import (
    AddPublicRevisionsConfig,
    AddPublicRevisionsService,
    AddPublicRevisionsServiceFactory,
)
from app.api.domains.modules.types import PublicModuleStatusCode
from app.api.domains.objects.services import ResolveChildObjectsViaHierarchyServiceFactory
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
from app.api.domains.objects.services.join_documents_service import (
    JoinDocumentsConfig,
    JoinDocumentsService,
    JoinDocumentsServiceFactory,
)
from app.api.domains.objects.services.join_objects import (
    JoinObjectsConfig,
    JoinObjectsService,
    JoinObjectsServiceFactory,
)
from app.api.domains.objects.services.join_related_files_service import (
    JoinRelatedFilesConfig,
    JoinRelatedFilesService,
    JoinRelatedFilesServiceFactory,
)
from app.api.domains.objects.services.resolve_child_objects_via_hierarchy_service import (
    ResolveChildObjectsViaHierarchyConfig,
    ResolveChildObjectsViaHierarchyService,
)
from app.api.domains.werkingsgebieden.services import JoinGebiedsaanwijzingenServiceFactory
from app.api.domains.werkingsgebieden.services.join_gebiedengroepen import (
    JoinGebiedenGroepenConfig,
    JoinGebiedenGroepenService,
    JoinGebiedenGroepenServiceFactory,
)
from app.api.domains.werkingsgebieden.services.join_gebiedsaanwijzingen import (
    JoinGebiedsaanwijzingenConfig,
    JoinGebiedsaanwijzingenService,
)
from app.api.domains.werkingsgebieden.services.join_werkingsgebieden import (
    JoinWerkingsgebiedenService,
    JoinWerkingsgebiedenServiceFactory,
)
from app.api.events.retrieved_module_objects_event import RetrievedModuleObjectsEvent
from app.api.events.retrieved_objects_event import RetrievedObjectsEvent
from app.api.events.types import ApiListener
from app.core.types import DynamicObjectModel, Model


class AddRelationsToObjectsListener(ApiListener[RetrievedObjectsEvent]):
    def __init__(self, relations_factory: AddRelationsServiceFactory):
        self._relations_factory: AddRelationsServiceFactory = relations_factory

    def handle_event(self, session: Session, event: RetrievedObjectsEvent) -> RetrievedObjectsEvent | None:
        add_service: AddRelationsService = self._relations_factory.create_service(
            session,
            event.payload.rows,
            event.context.response_model,
        )

        result_rows: list[BaseModel] = add_service.add_relations()
        event.payload.rows = result_rows

        return event


class JoinWerkingsgebiedenToObjectsListener(ApiListener[RetrievedObjectsEvent]):
    def __init__(self, service_factory: JoinWerkingsgebiedenServiceFactory):
        self._service_factory: JoinWerkingsgebiedenServiceFactory = service_factory

    def handle_event(self, session: Session, event: RetrievedObjectsEvent) -> RetrievedObjectsEvent | None:
        join_service: JoinWerkingsgebiedenService = self._service_factory.create_service(
            session,
            event.payload.rows,
            event.context.response_model,
        )

        result_rows: list[BaseModel] = join_service.join_werkingsgebieden()
        event.payload.rows = result_rows

        return event


class AddPublicRevisionsToObjectsListener(ApiListener[RetrievedObjectsEvent]):
    def __init__(self, service_factory: AddPublicRevisionsServiceFactory):
        self._service_factory: AddPublicRevisionsServiceFactory = service_factory

    def handle_event(self, session: Session, event: RetrievedObjectsEvent) -> RetrievedObjectsEvent | None:
        config: AddPublicRevisionsConfig | None = self._collect_config(event)
        if not config:
            return event

        service: AddPublicRevisionsService = self._service_factory.create_service(
            session,
            config,
            event.payload.rows,
        )

        result_rows: list[BaseModel] = service.add_revisions()
        event.payload.rows = result_rows

        return event

    def _collect_config(self, event: RetrievedObjectsEvent) -> AddPublicRevisionsConfig | None:
        if not isinstance(event.context.response_model, DynamicObjectModel):
            return None
        if "public_revisions" not in event.context.response_model.service_config:
            return None

        service_config: dict = event.context.response_model.service_config["public_revisions"]
        to_field: str = service_config["to_field"]

        object_codes: list[str] = list({r.Code for r in event.payload.rows})

        return AddPublicRevisionsConfig(
            to_field=to_field,
            object_codes=object_codes,
            allowed_status_list=PublicModuleStatusCode.values(),
        )


class AddNextObjectVersionToObjectsListener(ApiListener[RetrievedObjectsEvent]):
    def __init__(self, service_factory: AddNextObjectVersionServiceFactory):
        self._service_factory: AddNextObjectVersionServiceFactory = service_factory

    def handle_event(self, session: Session, event: RetrievedObjectsEvent) -> RetrievedObjectsEvent | None:
        config: AddNextObjectVersionConfig | None = self._collect_config(event)
        if not config:
            return event

        service: AddNextObjectVersionService = self._service_factory.create_service(
            session,
            config,
            event.payload.rows,
        )

        result_rows: list[BaseModel] = service.add_next_versions()
        event.payload.rows = result_rows

        return event

    def _collect_config(self, event: RetrievedObjectsEvent) -> AddNextObjectVersionConfig | None:
        if not isinstance(event.context.response_model, DynamicObjectModel):
            return None
        if "next_object_version" not in event.context.response_model.service_config:
            return None

        service_config: dict = event.context.response_model.service_config["next_object_version"]
        to_field: str = service_config["to_field"]

        object_uuids: list[uuid.UUID] = list({r.UUID for r in event.payload.rows})

        return AddNextObjectVersionConfig(
            to_field=to_field,
            object_uuids=object_uuids,
        )


class AddWerkingsgebiedRelatedObjectsToObjectsListener(ApiListener[RetrievedObjectsEvent]):
    def __init__(self, service_factory: AddWerkingsgebiedRelatedObjectsServiceFactory):
        self._service_factory: AddWerkingsgebiedRelatedObjectsServiceFactory = service_factory

    def handle_event(self, session: Session, event: RetrievedObjectsEvent) -> RetrievedObjectsEvent | None:
        config: AddWerkingsgebiedRelatedObjectsConfig | None = self._collect_config(event)
        if not config:
            return event

        service: AddWerkingsgebiedRelatedObjectsService = self._service_factory.create_service(
            session,
            config,
            event.payload.rows,
        )

        result_rows: list[BaseModel] = service.add_related_objects()
        event.payload.rows = result_rows

        return event

    def _collect_config(self, event: RetrievedObjectsEvent) -> AddWerkingsgebiedRelatedObjectsConfig | None:
        if not isinstance(event.context.response_model, DynamicObjectModel):
            return None
        if "werkingsgebied_related_objects" not in event.context.response_model.service_config:
            return None

        service_config: dict = event.context.response_model.service_config["werkingsgebied_related_objects"]
        to_field: str = service_config["to_field"]

        werkingsgebied_codes: list[str] = list({r.Code for r in event.payload.rows})

        return AddWerkingsgebiedRelatedObjectsConfig(
            to_field=to_field,
            werkingsgebied_codes=werkingsgebied_codes,
        )


class GetColumnImagesListenerBase[EventRMO: RetrievedObjectsEvent | RetrievedModuleObjectsEvent](ApiListener[EventRMO]):
    def __init__(self, service_factory: ColumnImageInserterFactory):
        self._service_factory: ColumnImageInserterFactory = service_factory

    def handle_event(self, session: Session, event: EventRMO) -> EventRMO | None:
        config: GetImagesConfig | None = self._collect_config(event.context.response_model)
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

    def _collect_config(self, request_model: Model) -> GetImagesConfig | None:
        if not isinstance(request_model, DynamicObjectModel):
            return None
        if "get_image" not in request_model.service_config:
            return None

        config_dict: dict = request_model.service_config.get("get_image", {})
        fields: list[str] = []
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


class JoinDocumentsListenerBase[EventRMO: RetrievedObjectsEvent | RetrievedModuleObjectsEvent](ApiListener[EventRMO]):
    def __init__(self, service_factory: JoinDocumentsServiceFactory):
        self._service_factory: JoinDocumentsServiceFactory = service_factory

    def handle_event(self, session: Session, event: EventRMO) -> EventRMO | None:
        config: JoinDocumentsConfig | None = self._collect_config(event)
        if not config:
            return event

        service: JoinDocumentsService = self._service_factory.create_service(
            session,
            config,
        )

        result_rows: list[BaseModel] = service.join_documents(event.payload.rows)
        event.payload.rows = result_rows

        return event

    def _collect_config(self, event: EventRMO) -> JoinDocumentsConfig | None:
        if not isinstance(event.context.response_model, DynamicObjectModel):
            return None
        if "join_documents" not in event.context.response_model.service_config:
            return None

        service_config: dict = event.context.response_model.service_config["join_documents"]

        all_document_codes: set[str] = set()
        for row in event.payload.rows:
            documents = getattr(row, service_config["from_field"], None) or []
            all_document_codes.update(documents)

        return JoinDocumentsConfig(
            to_field=service_config["to_field"],
            from_field=service_config["from_field"],
            document_codes=all_document_codes,
        )


class JoinDocumentsToObjectsListener(JoinDocumentsListenerBase[RetrievedObjectsEvent]):
    pass


class ResolveChildObjectsViaHierarchyListenerBase[EventRMO: RetrievedObjectsEvent | RetrievedModuleObjectsEvent](
    ApiListener[EventRMO]
):
    def __init__(self, service_factory: ResolveChildObjectsViaHierarchyServiceFactory):
        self._service_factory = service_factory

    def handle_event(self, session: Session, event: EventRMO) -> EventRMO | None:
        config: ResolveChildObjectsViaHierarchyConfig | None = self._collect_config(event)
        if not config:
            return event

        service: ResolveChildObjectsViaHierarchyService = self._service_factory.create_service(
            session,
            config,
        )

        result_rows: list[BaseModel] = service.resolve_child_objects(event.payload.rows)
        event.payload.rows = result_rows

        return event

    def _collect_config(self, event: EventRMO) -> ResolveChildObjectsViaHierarchyConfig | None:
        if not isinstance(event.context.response_model, DynamicObjectModel):
            return None
        if "resolve_child_objects_via_hierarchy_listener" not in event.context.response_model.service_config:
            return None

        service_config: dict = event.context.response_model.service_config[
            "resolve_child_objects_via_hierarchy_listener"
        ]
        return ResolveChildObjectsViaHierarchyConfig(
            to_field=service_config["to_field"],
            response_model=event.context.response_model,
        )


class ObjectResolveChildObjectsViaHierarchyListener(ResolveChildObjectsViaHierarchyListenerBase[RetrievedObjectsEvent]):
    pass


class JoinGebiedenGroepBaseListener[EventRMO: RetrievedObjectsEvent | RetrievedModuleObjectsEvent](
    ApiListener[EventRMO]
):
    def __init__(self, service_factory: JoinGebiedenGroepenServiceFactory):
        self._service_factory: JoinGebiedenGroepenServiceFactory = service_factory

    def handle_event(self, session: Session, event: EventRMO) -> EventRMO | None:
        config: JoinGebiedenGroepenConfig | None = self._collect_config(event)
        if not config:
            return event
        if not config.gebiedengroepen_codes:
            return event

        service: JoinGebiedenGroepenService = self._service_factory.create_service(
            session,
            config,
        )
        result_rows = service.join_gebiedengroepen(event.payload.rows)

        event.payload.rows = result_rows
        return event

    def _collect_config(self, event: EventRMO) -> JoinGebiedenGroepenConfig | None:
        response_model: Model = event.context.response_model
        if not isinstance(response_model, DynamicObjectModel):
            return None
        if "join_gebiedengroepen" not in response_model.service_config:
            return None

        config_dict: dict = response_model.service_config.get("join_gebiedengroepen", {})
        to_field: str = config_dict["to_field"]
        from_field: str = config_dict["from_field"]

        gebiedengroepen_codes: set[str] = {
            getattr(r, from_field) for r in event.payload.rows if getattr(r, from_field) is not None
        }

        return JoinGebiedenGroepenConfig(
            gebiedengroepen_codes=gebiedengroepen_codes,
            from_field=from_field,
            to_field=to_field,
        )


class JoinGebiedenGroepForObjectListener(JoinGebiedenGroepBaseListener[RetrievedObjectsEvent]):
    pass


class JoinObjectsBaseListener[EventRMO: RetrievedObjectsEvent | RetrievedModuleObjectsEvent](ApiListener[EventRMO]):
    def __init__(self, service_factory: JoinObjectsServiceFactory):
        self._service_factory: JoinObjectsServiceFactory = service_factory

    def handle_event(self, session: Session, event: EventRMO) -> EventRMO | None:
        config: JoinObjectsConfig | None = self._collect_config(event)
        if not config:
            return event
        if not config.object_codes:
            return event

        service: JoinObjectsService = self._service_factory.create_service(
            session,
            config,
        )
        result_rows = service.join_objects(event.payload.rows)

        event.payload.rows = result_rows
        return event

    def _collect_config(self, event: EventRMO) -> JoinObjectsConfig | None:
        response_model: Model = event.context.response_model
        if not isinstance(response_model, DynamicObjectModel):
            return None
        if "join_objects" not in response_model.service_config:
            return None

        config_dict: dict = response_model.service_config.get("join_objects", {})
        to_field: str = config_dict["to_field"]
        from_field: str = config_dict["from_field"]

        codes_per_row: list[list[str]] = [getattr(r, from_field) or [] for r in event.payload.rows]

        objects_codes: set[str] = {code for codes in codes_per_row for code in codes if code is not None}

        return JoinObjectsConfig(
            object_codes=objects_codes,
            from_field=from_field,
            to_field=to_field,
        )


class JoinObjectsForObjectListener(JoinObjectsBaseListener[RetrievedObjectsEvent]):
    pass


class JoinGebiedsaanwijzingenBaseListener[EventRMO: RetrievedObjectsEvent | RetrievedModuleObjectsEvent](
    ApiListener[EventRMO]
):
    def __init__(self, service_factory: JoinGebiedsaanwijzingenServiceFactory):
        self._service_factory: JoinGebiedsaanwijzingenServiceFactory = service_factory

    def handle_event(self, session: Session, event: RetrievedModuleObjectsEvent) -> RetrievedModuleObjectsEvent | None:
        config: JoinGebiedsaanwijzingenConfig | None = self._collect_config(event)
        if not config:
            return event

        service: JoinGebiedsaanwijzingenService = self._service_factory.create_service(session, config)
        result_rows: list[BaseModel] = service.join_gebiedsaanwijzingen(event.payload.rows)
        event.payload.rows = result_rows
        return event

    def _collect_config(self, event: RetrievedModuleObjectsEvent) -> JoinGebiedsaanwijzingenConfig | None:
        response_model: Model = event.context.response_model
        if not isinstance(response_model, DynamicObjectModel):
            return None
        if "join_gebiedsaanwijzingen" not in response_model.service_config:
            return None

        config_dict: dict = response_model.service_config.get("join_gebiedsaanwijzingen", {})
        to_field: str = config_dict["to_field"]
        from_fields: set[str] = config_dict["from_fields"]
        return JoinGebiedsaanwijzingenConfig(
            to_field=to_field,
            from_fields=from_fields,
        )


class JoinGebiedsaanwijzingenForObjectListener(JoinGebiedsaanwijzingenBaseListener[RetrievedObjectsEvent]):
    pass


class JoinRelatedFilesToObjectsListener(ApiListener[RetrievedObjectsEvent]):
    def __init__(self, service_factory: JoinRelatedFilesServiceFactory):
        self._service_factory: JoinRelatedFilesServiceFactory = service_factory

    def handle_event(self, session: Session, event: RetrievedObjectsEvent) -> RetrievedObjectsEvent | None:
        config: JoinRelatedFilesConfig | None = self._collect_config(event)
        if not config:
            return event

        service: JoinRelatedFilesService = self._service_factory.create_service(
            session,
            config,
            event.payload.rows,
        )

        result_rows: list[BaseModel] = service.join_related_files()
        event.payload.rows = result_rows

        return event

    def _collect_config(self, event: RetrievedObjectsEvent) -> JoinRelatedFilesConfig | None:
        if not isinstance(event.context.response_model, DynamicObjectModel):
            return None
        if "related_files" not in event.context.response_model.service_config:
            return None

        service_config: dict = event.context.response_model.service_config["related_files"]
        to_field: str = service_config["to_field"]

        object_codes: list[str] = list({r.Code for r in event.payload.rows})

        return JoinRelatedFilesConfig(
            to_field=to_field,
            object_codes=object_codes,
        )
