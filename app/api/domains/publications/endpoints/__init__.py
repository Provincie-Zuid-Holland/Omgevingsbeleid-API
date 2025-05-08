from .acts import (
    ClosePublicationActEndpointResolver,
    CreateActEndpointResolver,
    DetailPublicationActEndpointResolver,
    EditPublicationActEndpointResolver,
    ListPublicationActsEndpointResolver,
)
from .area_of_jurisdictions import CreatePublicationAOJEndpointResolver, ListPublicationAOJEndpointResolver
from .dso_value_lists.area_designation_groups import ListAreaDesignationGroupsEndpointResolver
from .dso_value_lists.area_designation_types import ListAreaDesignationTypesEndpointResolver
from .environments import (
    CreatePublicationEnvironmentEndpointResolver,
    DetailPublicationEnvironmentEndpointResolver,
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
    DetailActPackageReportEndpointResolver,
    DownloadActPackageReportEndpointResolver,
    ListActPackageReportsEndpointResolver,
    UploadActPackageReportEndpointResolver,
)
from .publications.announcement_packages import (
    CreatePublicationAnnouncementPackageEndpointResolver,
    DownloadPublicationAnnouncementPackageEndpointResolver,
    ListPublicationAnnouncementPackagesEndpointResolver,
)
from .publications.announcement_reports import (
    DetailAnnouncementPackageReportEndpointResolver,
    DownloadAnnouncementPackageReportEndpointResolver,
    ListAnnouncementPackageReportsEndpointResolver,
    UploadAnnouncementPackageReportEndpointResolver,
)
from .publications.announcements import (
    CreatePublicationAnnouncementEndpointResolver,
    DetailPublicationAnnouncementEndpointResolver,
    EditPublicationAnnouncementEndpointResolver,
    ListPublicationAnnouncementsEndpointResolver,
)
from .publications.versions import (
    CreatePublicationVersionEndpointResolver,
    CreatePublicationVersionPdfEndpointResolver,
    DeletePublicationVersionAttachmentEndpointResolver,
    DeletePublicationVersionEndpointResolver,
    DetailPublicationVersionEndpointResolver,
    EditPublicationVersionEndpointResolver,
    ListPublicationVersionsEndpointResolver,
    UploadPublicationVersionAttachmentEndpointResolver,
)
from .templates import (
    CreatePublicationTemplateEndpointResolver,
    DetailPublicationTemplateEndpointResolver,
    EditPublicationTemplateEndpointResolver,
    ListPublicationTemplatesEndpointResolver,
)
