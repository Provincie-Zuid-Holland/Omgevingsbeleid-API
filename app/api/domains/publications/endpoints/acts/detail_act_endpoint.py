from typing import Annotated

from fastapi import Depends

from app.api.domains.publications.dependencies import depends_publication_act
from app.api.domains.publications.types.models import PublicationAct
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.core.tables.publications import PublicationActTable
from app.core.tables.users import UsersTable


async def get_detail_act_endpoint(
    act: Annotated[PublicationActTable, Depends(depends_publication_act)],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_view_publication_act,
            )
        ),
    ],
) -> PublicationAct:
    result: PublicationAct = PublicationAct.model_validate(act)
    return result
