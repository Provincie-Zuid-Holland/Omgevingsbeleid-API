from typing import Annotated

from fastapi import Depends

from app.api.domains.publications.dependencies import depends_publication_announcement
from app.api.domains.publications.types.models import PublicationAnnouncement
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.core.tables.publications import PublicationAnnouncementTable
from app.core.tables.users import UsersTable


def get_detail_announcement_endpoint(
    announcement: Annotated[PublicationAnnouncementTable, Depends(depends_publication_announcement)],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_view_publication_announcement,
            )
        ),
    ],
) -> PublicationAnnouncement:
    result: PublicationAnnouncement = PublicationAnnouncement.model_validate(announcement)
    return result
