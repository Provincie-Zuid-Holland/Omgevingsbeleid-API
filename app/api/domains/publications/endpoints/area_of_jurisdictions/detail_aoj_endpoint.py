from typing import Annotated

from fastapi import Depends

from app.api.domains.publications.dependencies import depends_publication_area_of_jurisdiction
from app.api.domains.publications.types.models import PublicationAOJ
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.core.tables.publications import PublicationAreaOfJurisdictionTable
from app.core.tables.users import UsersTable


def get_detail_aoj_endpoint(
    area_of_jurisdiction: Annotated[PublicationAreaOfJurisdictionTable, Depends(depends_publication_area_of_jurisdiction)],
    user: Annotated[
    UsersTable,
    Depends(
        depends_current_user_with_permission_curried(
            Permissions.publication_can_view_publication_aoj,
        )
    ),
],
) -> PublicationAOJ:
    result: PublicationAOJ = PublicationAOJ.model_validate(area_of_jurisdiction)
    return result
