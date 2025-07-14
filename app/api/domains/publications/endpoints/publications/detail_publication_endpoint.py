from typing import Annotated

from fastapi import Depends

from app.api.domains.publications.dependencies import depends_publication
from app.api.domains.publications.types.models import Publication
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.core.tables.publications import PublicationTable
from app.core.tables.users import UsersTable


def get_detail_publication_endpoint(
    publication: Annotated[PublicationTable, Depends(depends_publication)],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_view_publication,
            )
        ),
    ],
) -> Publication:
    result: Publication = Publication.model_validate(publication)
    return result
