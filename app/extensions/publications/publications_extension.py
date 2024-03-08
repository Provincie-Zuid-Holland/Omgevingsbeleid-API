from typing import List

from app.dynamic.config.models import ExtensionModel
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.extension import Extension
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.publications import endpoints
from app.extensions.publications.models import Waardelijsten


class PublicationsExtension(Extension):
    def register_endpoint_resolvers(
        self,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
    ) -> List[EndpointResolver]:
        return [
            endpoints.CreatePublicationEndpointResolver(),
            endpoints.CreatePublicationPackageEndpointResolver(),
            endpoints.DetailPublicationEndpointResolver(),
            endpoints.DownloadPackageEndpointResolver(),
            endpoints.DownloadPackageReportsEndpointResolver(),
            endpoints.EditPublicationEndpointResolver(),
            endpoints.CreatePackageReportEndpointResolver(),
            endpoints.ListPublicationPackagesEndpointResolver(),
            endpoints.ListPublicationsEndpointResolver(),
            # Template
            endpoints.CreatePublicationTemplateEndpointResolver(),
            endpoints.EditPublicationTemplateEndpointResolver(),
            endpoints.ListPublicationTemplatesEndpointResolver(),
            # Environment
            endpoints.CreatePublicationEnvironmentEndpointResolver(),
            endpoints.EditPublicationEnvironmentEndpointResolver(),
            endpoints.ListPublicationEnvironmentsEndpointResolver(),
            # Area of jurisdictions
            endpoints.CreatePublicationAOJEndpointResolver(),
            endpoints.ListPublicationAOJEndpointResolver(),
            # Publication Version
            endpoints.CreatePublicationVersionEndpointResolver(),
            endpoints.EditPublicationVersionEndpointResolver(),
            endpoints.DetailPublicationVersionEndpointResolver(),
            endpoints.ListPublicationVersionsEndpointResolver(),
        ]

    def register_models(self, models_resolver: ModelsResolver):
        models_resolver.add(
            ExtensionModel(
                id="waardelijsten",
                name="Waardelijsten",
                pydantic_model=Waardelijsten,
            )
        )
