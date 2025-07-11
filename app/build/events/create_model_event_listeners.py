from typing import List, Optional

import pydantic

from app.api.domains.modules.types import PublicModuleObjectRevision
from app.api.domains.objects.types import NextObjectVersion
from app.core.services.event.types import Listener
from app.core.types import Model, WerkingsgebiedRelatedObjects

from .create_model_event import CreateModelEvent
from sqlalchemy.orm import Session


class ObjectsExtenderListener(Listener[CreateModelEvent]):
    def handle_event(self, session: Session, event: CreateModelEvent) -> Optional[CreateModelEvent]:
        service_config: dict = event.context.intermediate_model.service_config
        if not "foreign_keys_extender" in service_config:
            return event

        config: dict = service_config["foreign_keys_extender"]
        fields_map_config: List[dict] = config.get("fields_map", [])

        for field_map in fields_map_config:
            field_name: str = field_map["to_field"]
            model_id: str = field_map["model_id"]
            model: Model = event.context.models_provider.get_model(model_id)

            # Attach to the main object
            event.payload.pydantic_fields[field_name] = (
                Optional[model.pydantic_model],
                None,
            )

        return event


class ObjectStaticsExtenderListener(Listener[CreateModelEvent]):
    def handle_event(self, session: Session, event: CreateModelEvent) -> Optional[CreateModelEvent]:
        service_config: dict = event.context.intermediate_model.service_config
        if not "static_foreign_keys_extender" in service_config:
            return event

        config: dict = service_config["static_foreign_keys_extender"]
        fields_map_config: List[dict] = config.get("fields_map", [])

        for field_map in fields_map_config:
            field_name: str = field_map["to_field"]
            model_id: str = field_map["model_id"]
            model: Model = event.context.models_provider.get_model(model_id)

            # Attach to the STATIC object
            event.payload.static_pydantic_fields[field_name] = (
                Optional[model.pydantic_model],
                None,
            )

        return event


class AddRelationsListener(Listener[CreateModelEvent]):
    RELATION_MODEL_ID: str = "read_relation_short"

    def handle_event(self, session: Session, event: CreateModelEvent) -> Optional[CreateModelEvent]:
        service_config: dict = event.context.intermediate_model.service_config
        if not "relations" in service_config:
            return event

        config: dict = service_config["relations"]
        objects_config: List[dict] = config.get("objects", [])
        for object_config in objects_config:
            field_name: str = object_config["to_field"]
            model_id: str = object_config["model_id"]
            target_object_model: Model = event.context.models_provider.get_model(model_id)

            final_model: Model = target_object_model
            if object_config.get("wrapped_with_relation_data", False):
                final_model: Model = self._get_wrapper_model(event, final_model)

            event.payload.pydantic_fields[field_name] = (
                List[final_model.pydantic_model],
                [],
            )

        return event

    def _get_wrapper_model(self, event: CreateModelEvent, target_model: Model) -> Model:
        wrapper_model_id: str = f"{self.RELATION_MODEL_ID}:{target_model.id}"

        wrapper_model_exists: bool = event.context.models_provider.exists(wrapper_model_id)
        if not wrapper_model_exists:
            self._generate_relation_wrapper_model(
                event,
                wrapper_model_id,
                target_model,
            )

        wrapper_model: Model = event.context.models_provider.get_model(wrapper_model_id)
        return wrapper_model

    def _generate_relation_wrapper_model(self, event: CreateModelEvent, id: str, target_model: Model):
        relation_model: Model = event.context.models_provider.get_model(self.RELATION_MODEL_ID)
        name: str = f"{relation_model.name}-{target_model.name}"

        wrapper_model: Model = Model(
            id=id,
            name=name,
            pydantic_model=pydantic.create_model(
                name,
                Relation=(relation_model.pydantic_model, pydantic.Field(default=None)),
                Object=(target_model.pydantic_model, pydantic.Field(default=None)),
            ),
        )

        event.context.models_provider.add(wrapper_model)


class JoinWerkingsgebiedenListener(Listener[CreateModelEvent]):
    def handle_event(self, session: Session, event: CreateModelEvent) -> Optional[CreateModelEvent]:
        service_config: dict = event.context.intermediate_model.service_config
        if not "join_werkingsgebieden" in service_config:
            return event

        config: dict = service_config["join_werkingsgebieden"]
        field_name: str = config["to_field"]
        model_id: str = config["model_id"]
        target_object_model: Model = event.context.models_provider.get_model(model_id)

        event.payload.pydantic_fields[field_name] = (
            Optional[target_object_model.pydantic_model],
            None,
        )

        return event


class AddPublicRevisionsToObjectModelListener(Listener[CreateModelEvent]):
    def handle_event(self, session: Session, event: CreateModelEvent) -> Optional[CreateModelEvent]:
        service_config: dict = event.context.intermediate_model.service_config
        if not "public_revisions" in service_config:
            return event

        config: dict = service_config["public_revisions"]
        field_name: str = config["to_field"]

        event.payload.pydantic_fields[field_name] = (
            List[PublicModuleObjectRevision],
            [],
        )

        return event


class AddNextObjectVersionToObjectModelListener(Listener[CreateModelEvent]):
    def handle_event(self, session: Session, event: CreateModelEvent) -> Optional[CreateModelEvent]:
        service_config: dict = event.context.intermediate_model.service_config
        if not "next_object_version" in service_config:
            return event

        config: dict = service_config["next_object_version"]
        field_name: str = config["to_field"]

        event.payload.pydantic_fields[field_name] = (
            Optional[NextObjectVersion],
            None,
        )

        return event


class AddRelatedObjectsToWerkingsgebiedObjectModelListener(Listener[CreateModelEvent]):
    def handle_event(self, session: Session, event: CreateModelEvent) -> Optional[CreateModelEvent]:
        service_config: dict = event.context.intermediate_model.service_config
        if not "werkingsgebied_related_objects" in service_config:
            return event

        config: dict = service_config["werkingsgebied_related_objects"]
        field_name: str = config["to_field"]

        event.payload.pydantic_fields[field_name] = (
            Optional[WerkingsgebiedRelatedObjects],
            None,
        )

        return event
