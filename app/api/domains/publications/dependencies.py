import uuid
from typing import Annotated, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.publications.repository.publication_act_package_repository import PublicationActPackageRepository
from app.api.domains.publications.repository.publication_act_report_repository import PublicationActReportRepository
from app.api.domains.publications.repository.publication_act_repository import PublicationActRepository
from app.api.domains.publications.repository.publication_announcement_package_repository import (
    PublicationAnnouncementPackageRepository,
)
from app.api.domains.publications.repository.publication_announcement_report_repository import (
    PublicationAnnouncementReportRepository,
)
from app.api.domains.publications.repository.publication_announcement_repository import (
    PublicationAnnouncementRepository,
)
from app.api.domains.publications.repository.publication_environment_repository import PublicationEnvironmentRepository
from app.api.domains.publications.repository.publication_repository import PublicationRepository
from app.api.domains.publications.repository.publication_template_repository import PublicationTemplateRepository
from app.api.domains.publications.repository.publication_version_attachment_repository import (
    PublicationVersionAttachmentRepository,
)
from app.api.domains.publications.repository.publication_version_repository import PublicationVersionRepository
from app.api.domains.publications.repository.publication_zip_repository import PublicationZipRepository
from app.core.tables.publications import (
    PublicationActPackageReportTable,
    PublicationActPackageTable,
    PublicationActTable,
    PublicationAnnouncementPackageReportTable,
    PublicationAnnouncementPackageTable,
    PublicationAnnouncementTable,
    PublicationAreaOfJurisdictionTable,
    PublicationEnvironmentTable,
    PublicationPackageZipTable,
    PublicationTable,
    PublicationTemplateTable,
    PublicationVersionAttachmentTable,
    PublicationVersionTable,
)


@inject
def depends_publication_template(
    template_uuid: uuid.UUID,
    session: Annotated[Session, Depends(depends_db_session)],
    repository: Annotated[
        PublicationTemplateRepository, Depends(Provide[ApiContainer.publication.template_repository])
    ],
) -> PublicationTemplateTable:
    maybe_template: Optional[PublicationTemplateTable] = repository.get_by_uuid(session, template_uuid)
    if not maybe_template:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Publication template niet gevonden")
    return maybe_template


@inject
def depends_publication(
    publication_uuid: uuid.UUID,
    session: Annotated[Session, Depends(depends_db_session)],
    repository: Annotated[PublicationRepository, Depends(Provide[ApiContainer.publication.publication_repository])],
) -> PublicationTable:
    maybe_publication: Optional[PublicationTable] = repository.get_by_uuid(session, publication_uuid)
    if not maybe_publication:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Publication niet gevonden")
    return maybe_publication


@inject
def depends_publication_version(
    version_uuid: uuid.UUID,
    session: Annotated[Session, Depends(depends_db_session)],
    repository: Annotated[PublicationVersionRepository, Depends(Provide[ApiContainer.publication.version_repository])],
) -> PublicationVersionTable:
    maybe_version: Optional[PublicationVersionTable] = repository.get_by_uuid(session, version_uuid)
    if not maybe_version:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Publication version niet gevonden")
    if maybe_version.Deleted_At:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Publication version is verwijderd")
    return maybe_version


@inject
def depends_publication_version_attachment(
    attachment_id: int,
    session: Annotated[Session, Depends(depends_db_session)],
    repository: Annotated[
        PublicationVersionAttachmentRepository, Depends(Provide[ApiContainer.publication.version_attachment_repository])
    ],
) -> PublicationVersionAttachmentTable:
    maybe_attachment: Optional[PublicationVersionAttachmentTable] = repository.get_by_id(session, attachment_id)
    if not maybe_attachment:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Publication attachment niet gevonden")
    return maybe_attachment


@inject
def depends_publication_act_package(
    act_package_uuid: uuid.UUID,
    session: Annotated[Session, Depends(depends_db_session)],
    package_repository: Annotated[
        PublicationActPackageRepository, Depends(Provide[ApiContainer.publication.act_package_repository])
    ],
) -> PublicationActPackageTable:
    package: Optional[PublicationActPackageTable] = package_repository.get_by_uuid(session, act_package_uuid)
    if package is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Package not found")
    return package


@inject
def depends_publication_announcement(
    announcement_uuid: uuid.UUID,
    session: Annotated[Session, Depends(depends_db_session)],
    repository: Annotated[
        PublicationAnnouncementRepository, Depends(Provide[ApiContainer.publication.announcement_repository])
    ],
) -> PublicationAnnouncementTable:
    maybe_announcement: Optional[PublicationAnnouncementTable] = repository.get_by_uuid(session, announcement_uuid)
    if not maybe_announcement:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Publication announcement niet gevonden")
    return maybe_announcement


@inject
def depends_publication_announcement_package(
    announcement_package_uuid: uuid.UUID,
    session: Annotated[Session, Depends(depends_db_session)],
    package_repository: Annotated[
        PublicationAnnouncementPackageRepository,
        Depends(Provide[ApiContainer.publication.announcement_package_repository]),
    ],
) -> PublicationAnnouncementPackageTable:
    package: Optional[PublicationAnnouncementPackageTable] = package_repository.get_by_uuid(
        session, announcement_package_uuid
    )
    if package is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Package not found")
    return package


@inject
def depends_publication_announcement_report(
    announcement_report_uuid: uuid.UUID,
    session: Annotated[Session, Depends(depends_db_session)],
    repository: Annotated[
        PublicationAnnouncementReportRepository,
        Depends(Provide[ApiContainer.publication.announcement_report_repository]),
    ],
) -> PublicationAnnouncementPackageReportTable:
    report: Optional[PublicationAnnouncementPackageReportTable] = repository.get_by_uuid(
        session, announcement_report_uuid
    )
    if report is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Package report not found")
    return report


@inject
def depends_publication_zip_by_act_package(
    act_package_uuid: uuid.UUID,
    session: Annotated[Session, Depends(depends_db_session)],
    repository: Annotated[PublicationZipRepository, Depends(Provide[ApiContainer.publication.zip_repository])],
) -> PublicationPackageZipTable:
    package_zip: Optional[PublicationPackageZipTable] = repository.get_by_act_package_uuid(session, act_package_uuid)
    if package_zip is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Package Zip not found")
    return package_zip


@inject
def depends_publication_zip_by_announcement_package(
    announcement_package_uuid: uuid.UUID,
    session: Annotated[Session, Depends(depends_db_session)],
    repository: Annotated[PublicationZipRepository, Depends(Provide[ApiContainer.publication.zip_repository])],
) -> PublicationPackageZipTable:
    package_zip: Optional[PublicationPackageZipTable] = repository.get_by_announcement_package_uuid(
        session,
        announcement_package_uuid,
    )
    if package_zip is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Package Zip not found")
    return package_zip


@inject
def depends_publication_act_report(
    act_report_uuid: uuid.UUID,
    session: Annotated[Session, Depends(depends_db_session)],
    repository: Annotated[
        PublicationActReportRepository, Depends(Provide[ApiContainer.publication.act_report_repository])
    ],
) -> PublicationActPackageReportTable:
    report: Optional[PublicationActPackageReportTable] = repository.get_by_uuid(session, act_report_uuid)
    if report is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Package report not found")
    return report


@inject
def depends_publication_environment(
    environment_uuid: uuid.UUID,
    session: Annotated[Session, Depends(depends_db_session)],
    repository: Annotated[
        PublicationEnvironmentRepository, Depends(Provide[ApiContainer.publication.environment_repository])
    ],
) -> PublicationEnvironmentTable:
    maybe_environment: Optional[PublicationEnvironmentTable] = repository.get_by_uuid(session, environment_uuid)
    if not maybe_environment:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Publication environment niet gevonden")
    return maybe_environment


@inject
def depends_publication_act(
    act_uuid: uuid.UUID,
    session: Annotated[Session, Depends(depends_db_session)],
    repository: Annotated[PublicationActRepository, Depends(Provide[ApiContainer.publication.act_repository])],
) -> PublicationActTable:
    maybe_act: Optional[PublicationActTable] = repository.get_by_uuid(session, act_uuid)
    if not maybe_act:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Publicatie regeling niet gevonden")
    return maybe_act


def depends_publication_act_active(
    act: Annotated[PublicationActTable, Depends(depends_publication_act)],
) -> PublicationActTable:
    if not act.Is_Active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Publicatie regeling is gesloten")
    return act

@inject
def depends_publication_area_of_jurisdiction(
    area_of_jurisdiction_uuid: uuid.UUID,
    session: Annotated[Session, Depends(depends_db_session)],
    repository: Annotated[
        PublicationAreaOfJurisdictionTable, Depends(Provide[ApiContainer.publication.aoj_repository])
    ],
) -> PublicationAreaOfJurisdictionTable:
    maybe_area_of_jurisdiction: Optional[PublicationAreaOfJurisdictionTable] = repository.get_by_uuid(session, area_of_jurisdiction_uuid)
    if not maybe_area_of_jurisdiction:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Publication area of jurisdiction niet gevonden")
    return maybe_area_of_jurisdiction
