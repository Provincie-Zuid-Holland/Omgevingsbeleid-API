import uuid
from datetime import datetime, timezone
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

    publication: PublicationTable = act_package.Publication_Version.Publication
    metadata = defaults_provider.get_metadata(publication.Document_Type, publication.Procedure_Type)
    procedural = defaults_provider.get_procedural()
    content = defaults_provider.get_content(publication.Document_Type, publication.Procedure_Type)

    timepoint: datetime = datetime.now(timezone.utc)
    announcement = PublicationAnnouncementTable(
        UUID=uuid.uuid4(),
        Act_Package_UUID=act_package.UUID,
        Publication_UUID=publication.UUID,
        Metadata=metadata.model_dump(),
        Procedural=procedural.model_dump(),
        Content=content.model_dump(),
        Announcement_Date=None,
        Is_Locked=False,
        Created_Date=timepoint,
        Modified_Date=timepoint,
        Created_By_UUID=user.UUID,
        Modified_By_UUID=user.UUID,
    )

    session.add(announcement)
    session.commit()
    session.flush()

    return AnnouncementCreatedResponse(
        UUID=announcement.UUID,
    )


def _guard_can_create_announcement(act_package: PublicationActPackageTable):
    if not act_package.Publication_Version.Publication.Environment.Has_State:
        return
    if act_package.Report_Status != ReportStatusType.VALID:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Can not create an announcement for act package that is not successful",
        )
    if not act_package.Act_Version.Act.Is_Active:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Can not create an announcement for act that is not active",
        )
