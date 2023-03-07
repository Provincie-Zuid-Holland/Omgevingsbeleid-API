from abc import ABC
from typing import List, Dict, Callable, Optional

from fastapi import APIRouter

from app.dynamic.config.models import (
    Column,
    Field,
    IntermediateObject,
    IntermediateModel,
)
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.service_container import ServiceContainer
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import EndpointResolver


class Extension(ABC):
    def __init__(self):
        self._service_container: Optional[ServiceContainer]

    def register_base_columns(self) -> List[Column]:
        return []

    def register_base_fields(self) -> List[Field]:
        return []

    def register_models(self, models_resolver: ModelsResolver):
        pass

    def migrate(self):
        # A place to create own database tables
        # Should not be used to touch the main objects table
        pass

    # @todo: not to sure if i want to give the service container
    # might be removed when everything comes together
    # def supply_service_container(self, service_container: ServiceContainer):
    #     self.service_container = service_container

    def register_tables(self, columns: Dict[str, Column]):
        # A place for extensions to load database tables before we generate the database
        pass

    def register_listeners(
        self,
        main_config: dict,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
    ):
        pass

    def register_serializers(self) -> Dict[str, Callable]:
        return {}

    def register_validators(self) -> Dict[str, Callable]:
        return {}

    def post_build_intermediate(
        self,
        event_dispatcher: EventDispatcher,
        intermediate_object: IntermediateObject,
        intermediate_models: List[IntermediateModel],
    ):
        pass

    def register_endpoints(
        self,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
        router: APIRouter,
    ) -> APIRouter:
        return router

    def register_endpoint_resolvers(
        self,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
    ) -> List[EndpointResolver]:
        return []
