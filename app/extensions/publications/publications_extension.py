from typing import List

from app.dynamic.config.models import ExtensionModel
from app.dynamic.endpoints.endpoint import EndpointResolver
from app.dynamic.event_listeners import EventListeners
from app.dynamic.extension import Extension
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.publications import endpoints
from app.extensions.publications.models import Waardelijsten


class PublicationsExtension(Extension):
    def register_endpoint_resolvers(
        self,
        event_listeners: EventListeners,
        models_resolver: ModelsResolver,
    ) -> List[EndpointResolver]:
        return [
            # Template
            endpoints.CreatePublicationTemplateEndpointResolver(),
            endpoints.EditPublicationTemplateEndpointResolver(),
            endpoints.ListPublicationTemplatesEndpointResolver(),
            endpoints.DetailPublicationTemplateEndpointResolver(),
            # Environment
            endpoints.CreatePublicationEnvironmentEndpointResolver(),
            endpoints.EditPublicationEnvironmentEndpointResolver(),
            endpoints.ListPublicationEnvironmentsEndpointResolver(),
            # Area of jurisdictions
            endpoints.CreatePublicationAOJEndpointResolver(),
            endpoints.ListPublicationAOJEndpointResolver(),
            # Acts
            endpoints.CreateActEndpointResolver(),
            endpoints.EditPublicationActEndpointResolver(),
            endpoints.ListPublicationActsEndpointResolver(),
            endpoints.DetailPublicationActEndpointResolver(),
            # Publication
            endpoints.CreatePublicationEndpointResolver(),
            endpoints.DetailPublicationEndpointResolver(),
            endpoints.EditPublicationEndpointResolver(),
            endpoints.ListPublicationsEndpointResolver(),
            # Publication Version
            endpoints.CreatePublicationVersionEndpointResolver(),
            endpoints.EditPublicationVersionEndpointResolver(),
            endpoints.DetailPublicationVersionEndpointResolver(),
            endpoints.ListPublicationVersionsEndpointResolver(),
            endpoints.UploadPublicationVersionAttachmentEndpointResolver(),
            # Package
            endpoints.ListPublicationPackagesEndpointResolver(),
            endpoints.CreatePublicationPackageEndpointResolver(),
            endpoints.DownloadPackageEndpointResolver(),
            # Package Reports
            endpoints.UploadActPackageReportEndpointResolver(),
            endpoints.ListActPackageReportsEndpointResolver(),
            endpoints.DetailActPackageReportEndpointResolver(),
            endpoints.DownloadActPackageReportEndpointResolver(),
            # Announcements
            endpoints.CreatePublicationAnnouncementEndpointResolver(),
            endpoints.ListPublicationAnnouncementsEndpointResolver(),
            endpoints.DetailPublicationAnnouncementEndpointResolver(),
            endpoints.EditPublicationAnnouncementEndpointResolver(),
            # Announcement Packages
            endpoints.CreatePublicationAnnouncementPackageEndpointResolver(),
            endpoints.DownloadPublicationAnnouncementPackageEndpointResolver(),
            endpoints.ListPublicationAnnouncementPackagesEndpointResolver(),
            # Announcement Package Reports
            endpoints.UploadAnnouncementPackageReportEndpointResolver(),
            endpoints.ListAnnouncementPackageReportsEndpointResolver(),
            endpoints.DetailAnnouncementPackageReportEndpointResolver(),
            endpoints.DownloadAnnouncementPackageReportEndpointResolver(),
        ]

    def register_models(self, models_resolver: ModelsResolver):
        models_resolver.add(
            ExtensionModel(
                id="waardelijsten",
                name="Waardelijsten",
                pydantic_model=Waardelijsten,
            )
        )
