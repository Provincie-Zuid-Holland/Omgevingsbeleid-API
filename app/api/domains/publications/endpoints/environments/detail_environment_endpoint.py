from typing import Annotated

from dependency_injector.wiring import inject
from fastapi import Depends

from app.api.domains.publications.dependencies import depends_publication_environment
from app.api.domains.publications.types.models import PublicationEnvironment
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.core.tables.publications import PublicationEnvironmentTable
from app.core.tables.users import UsersTable


@inject
def get_detail_environment_endpoint(
    environment: Annotated[PublicationEnvironmentTable, Depends(depends_publication_environment)],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_view_publication_environment,
            )
        ),
    ],
) -> PublicationEnvironment:
    result: PublicationEnvironment = PublicationEnvironment.model_validate(environment)
    return result
