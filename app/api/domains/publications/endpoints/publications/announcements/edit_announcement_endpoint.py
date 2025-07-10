from datetime import date, datetime, timezone
from typing import Annotated, Any, Dict, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.domains.publications.dependencies import depends_publication_announcement
from app.api.domains.publications.types.models import AnnouncementContent, AnnouncementMetadata, AnnouncementProcedural
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.api.types import ResponseOK
from app.core.tables.publications import PublicationAnnouncementTable
from app.core.tables.users import UsersTable


class PublicationAnnouncementEdit(BaseModel):
    Announcement_Date: Optional[date] = None

    Metadata: Optional[AnnouncementMetadata] = None
    Procedural: Optional[AnnouncementProcedural] = None
    Content: Optional[AnnouncementContent] = None


@inject
def post_edit_announcement_endpoint(
    object_in: Annotated[PublicationAnnouncementEdit, Depends()],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_edit_publication_announcement,
            )
        ),
    ],
    announcement: Annotated[PublicationAnnouncementTable, Depends(depends_publication_announcement)],
    db: Annotated[Session, Depends(Provide[ApiContainer.db])],
) -> ResponseOK:
    _guard_locked(announcement)

    changes: Dict[str, Any] = object_in.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nothing to update")

    for key, value in changes.items():
        if isinstance(value, BaseModel):
            value = value.model_dump()
        setattr(announcement, key, value)

    announcement.Modified_By_UUID = user.UUID
    announcement.Modified_Date = datetime.now(timezone.utc)

    db.add(announcement)
    db.commit()
    db.flush()

    return ResponseOK()


def _guard_locked(announcement: PublicationAnnouncementTable) -> None:
    if announcement.Is_Locked:
        raise HTTPException(status.HTTP_409_CONFLICT, "This announcement is locked")
    if not announcement.Publication.Act.Is_Active:
        raise HTTPException(status.HTTP_409_CONFLICT, "This act can no longer be used")
