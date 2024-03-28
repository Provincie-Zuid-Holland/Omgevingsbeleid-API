from .acts import (
    CreateActEndpointResolver,
    DetailPublicationActEndpointResolver,
    EditPublicationActEndpointResolver,
    ListPublicationActsEndpointResolver,
)
from .area_of_jurisdictions import CreatePublicationAOJEndpointResolver, ListPublicationAOJEndpointResolver
from .environments import (
    CreatePublicationEnvironmentEndpointResolver,
    EditPublicationEnvironmentEndpointResolver,
    ListPublicationEnvironmentsEndpointResolver,
)
from .publications import (
    CreatePublicationEndpointResolver,
    DetailPublicationEndpointResolver,
    EditPublicationEndpointResolver,
    ListPublicationsEndpointResolver,
)
from .publications.act_packages import (
    CreatePublicationPackageEndpointResolver,
    DownloadPackageEndpointResolver,
    ListPublicationPackagesEndpointResolver,
)
from .publications.act_reports import (
    DetailPackageActReportEndpointResolver,
    DownloadPackageActReportEndpointResolver,
    ListPackageActReportsEndpointResolver,
    UploadPackageActReportEndpointResolver,
)
from .publications.announcement_packages import (
    CreatePublicationAnnouncementPackageEndpointResolver,
    DownloadPublicationAnnouncementPackageEndpointResolver,
    ListPublicationAnnouncementPackagesEndpointResolver,
)
from .publications.announcements import (
    CreatePublicationAnnouncementEndpointResolver,
    DetailPublicationAnnouncementEndpointResolver,
    EditPublicationAnnouncementEndpointResolver,
    ListPublicationAnnouncementsEndpointResolver,
)
from .publications.versions import (
    CreatePublicationVersionEndpointResolver,
    DetailPublicationVersionEndpointResolver,
    EditPublicationVersionEndpointResolver,
    ListPublicationVersionsEndpointResolver,
)
from .templates import (
    CreatePublicationTemplateEndpointResolver,
    DetailPublicationTemplateEndpointResolver,
    EditPublicationTemplateEndpointResolver,
    ListPublicationTemplatesEndpointResolver,
)
