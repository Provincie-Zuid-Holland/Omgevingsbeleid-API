from typing import Annotated

from fastapi import Depends

from app.api.domains.publications.dependencies import depends_publication_template
from app.api.domains.publications.types.models import PublicationTemplate
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.core.tables.publications import PublicationTemplateTable
from app.core.tables.users import UsersTable


async def get_detail_template_endpoint(
    template: Annotated[PublicationTemplateTable, Depends(depends_publication_template)],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_view_publication_template,
            )
        ),
    ],
) -> PublicationTemplate:
    result: PublicationTemplate = PublicationTemplate.model_validate(template)
    return result
