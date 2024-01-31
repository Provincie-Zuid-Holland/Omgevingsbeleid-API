from typing import List

import click

from app.dynamic.config.models import ExtensionModel
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.extension import Extension
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.publications import commands, endpoints
from app.extensions.publications.models import Publication, PublicationBill, PublicationConfig, PublicationPackage


class PublicationsExtension(Extension):
    def register_models(self, models_resolver: ModelsResolver):
        models_resolver.add(
            ExtensionModel(
                id="publication",
                name="publication",
                pydantic_model=Publication,
            ),
        )
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

    def register_endpoint_resolvers(
        self,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
    ) -> List[EndpointResolver]:
        return [
            endpoints.CreatePublicationEndpointResolver(),
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

    def register_commands(self, main_command_group: click.Group, main_config: dict):
        main_command_group.add_command(commands.generate_dso_package, "generate-dso-package")
        main_command_group.add_command(commands.generate_frbr, "generate-frbr")
