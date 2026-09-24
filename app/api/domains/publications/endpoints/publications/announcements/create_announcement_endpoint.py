import uuid
from datetime import UTC, datetime
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.publications.dependencies import depends_publication_act_package
from app.api.domains.publications.services.publication_announcement_defaults_provider import (
    PublicationAnnouncementDefaultsProvider,
)
from app.api.domains.publications.types.enums import ReportStatusType
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.core.tables.publications import PublicationActPackageTable, PublicationAnnouncementTable, PublicationTable
from app.core.tables.users import UsersTable


class AnnouncementCreatedResponse(BaseModel):
    UUID: uuid.UUID


@inject
def post_create_announcement_endpoint(
    act_package: Annotated[PublicationActPackageTable, Depends(depends_publication_act_package)],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_create_publication_announcement,
            )
        ),
    ],
    defaults_provider: Annotated[
        PublicationAnnouncementDefaultsProvider,
        Depends(Provide[ApiContainer.publication.announcement_defaults_provider]),
    ],
    session: Annotated[Session, Depends(depends_db_session)],
) -> AnnouncementCreatedResponse:
    _guard_can_create_announcement(act_package)

    publication: PublicationTable = act_package.publication_version.publication
    metadata = defaults_provider.get_metadata(publication.document_type, publication.procedure_type)
    procedural = defaults_provider.get_procedural()
    content = defaults_provider.get_content(publication.document_type, publication.procedure_type)

    timepoint: datetime = datetime.now(UTC)
    announcement = PublicationAnnouncementTable(
        id=uuid.uuid4(),
        act_package_id=act_package.id,
        publication_id=publication.id,
        meta_data=metadata.model_dump(),
        procedural=procedural.model_dump(),
        content=content.model_dump(),
        announcement_date=None,
        is_locked=False,
        created_date=timepoint,
        modified_date=timepoint,
        created_by_id=user.UUID,
        modified_by_id=user.UUID,
    )

    session.add(announcement)
    session.flush()
    session.commit()

    return AnnouncementCreatedResponse(
        UUID=announcement.id,
    )


def _guard_can_create_announcement(act_package: PublicationActPackageTable):
    if not act_package.publication_version.publication.module.is_active:
        raise HTTPException(status.HTTP_409_CONFLICT, "This module is not active")
    if not act_package.publication_version.publication.environment.has_state:
        return
    if act_package.report_status != ReportStatusType.VALID:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Can not create an announcement for act package that is not successful",
        )
    if not act_package.act_version.act.is_active:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Can not create an announcement for act that is not active",
        )
