from abc import ABC
from typing import Callable, Dict, List, Optional, Type

import click
from fastapi import APIRouter
from pydantic_settings import BaseSettings

from app.dynamic.computed_fields import ComputedField
from app.dynamic.computed_fields.computed_field_resolver import ComputedFieldResolver
from app.dynamic.config.models import Column, Field
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.event_listeners import EventListeners
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.service_container import ServiceContainer


class Extension(ABC):
    def __init__(self):
        self._service_container: Optional[ServiceContainer]

    def extend_settings(self) -> Optional[Type[BaseSettings]]:
        return None

    def initialize(self, main_config: dict):
        pass

    def register_base_columns(self) -> List[Column]:
        return []

    def register_base_fields(self) -> List[Field]:
        return []

    def register_models(self, models_resolver: ModelsResolver):
        pass

    def register_commands(self, main_command_group: click.Group, main_config: dict):
        pass

    def register_computed_fields(self) -> List[ComputedField]:
        return []

    def register_computed_field_handlers(self, computed_field_resolver: ComputedFieldResolver):
        pass

    def migrate(self):
        # A place to create own database tables
        # Should not be used to touch the main objects table
        pass

    # @todo: not to sure if i want to give the service container
    # might be removed when everything comes together
    # def supply_service_container(self, service_container: ServiceContainer):
    #     self.service_container = service_container

    def register_tables(self, event_dispatcher: EventDispatcher, columns: Dict[str, Column]):
        # A place for extensions to load database tables before we generate the database
        pass

    def register_listeners(
        self,
        main_config: dict,
        event_listeners: EventListeners,
        converter: Converter,
        models_resolver: ModelsResolver,
    ):
        pass

    def register_serializers(self) -> Dict[str, Callable]:
        return {}

    def register_validators(self) -> Dict[str, Callable]:
        return {}

    def register_endpoints(
        self,
        event_listeners: EventListeners,
        models_resolver: ModelsResolver,
        router: APIRouter,
    ) -> APIRouter:
        return router

    def register_endpoint_resolvers(
        self,
        event_listeners: EventListeners,
        models_resolver: ModelsResolver,
    ) -> List[EndpointResolver]:
        return []
