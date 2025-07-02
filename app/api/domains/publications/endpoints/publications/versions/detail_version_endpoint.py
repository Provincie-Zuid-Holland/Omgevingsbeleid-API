from typing import Annotated, List

from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.api.api_container import ApiContainer
from app.api.domains.publications.dependencies import depends_publication_version
from app.api.domains.publications.services.publication_version_validator import PublicationVersionValidator
from app.api.domains.publications.types.models import PublicationVersion
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.core.tables.publications import PublicationVersionTable
from app.core.tables.users import UsersTable


@inject
async def get_detail_version_endpoint(
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_view_publication_version,
            )
        ),
    ],
    publication_version: Annotated[PublicationVersionTable, Depends(depends_publication_version)],
    validator: Annotated[PublicationVersionValidator, Depends(Provide[ApiContainer.publication.version_validator])],
) -> PublicationVersion:
    errors: List[dict] = validator.get_errors(publication_version)
    result: PublicationVersion = PublicationVersion.model_validate(publication_version)
    result.Errors = errors

    return result
