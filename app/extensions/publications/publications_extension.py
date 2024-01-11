from typing import List, Dict

from app.dynamic.config.models import ExtensionModel, Column
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.extension import Extension
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.publications.models import (
    PublicationBill,
    PublicationPackage,
    PublicationConfig,
)
from app.extensions.publications import endpoints


class PublicationsExtension(Extension):
    def register_models(self, models_resolver: ModelsResolver):
        models_resolver.add(
            ExtensionModel(
                id="publication_bill",
                name="publication_bill",
                pydantic_model=PublicationBill,
            ),
        )
        models_resolver.add(
            ExtensionModel(
                id="publication_package",
                name="publication_package",
                pydantic_model=PublicationPackage,
            ),
        )
        models_resolver.add(
            ExtensionModel(
                id="publication_config",
                name="publication_config",
                pydantic_model=PublicationConfig,
            ),
        )
        # TODO: Add OW

    def register_endpoint_resolvers(
        self,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
    ) -> List[EndpointResolver]:
        return [
            endpoints.ListPublicationBillsEndpointResolver(),
            endpoints.CreatePublicationBillEndpointResolver(),
            endpoints.CreatePublicationPackageEndpointResolver(),
            endpoints.ListPublicationPackagesEndpointResolver(),
        ]

    def register_listeners(
        self,
        main_config: dict,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
    ):
        pass
