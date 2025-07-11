from typing import Annotated, List, Optional, Sequence

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.objects.endpoints.types import AcknowledgedRelation, build_from_orm
from app.api.domains.objects.repositories.acknowledged_relations_repository import AcknowledgedRelationsRepository
from app.api.domains.users.dependencies import depends_current_user
from app.api.endpoint import BaseEndpointContext
from app.core.tables.acknowledged_relations import AcknowledgedRelationsTable
from app.core.tables.users import UsersTable


class AcknowledgedRelationListEndpointContext(BaseEndpointContext):
    object_type: str


@inject
def get_acknowledged_relation_list_endpoint(
    user: Annotated[UsersTable, Depends(depends_current_user)],
    session: Annotated[Session, Depends(depends_db_session)],
    repository: Annotated[
        AcknowledgedRelationsRepository, Depends(Provide[ApiContainer.acknowledged_relations_repository])
    ],
    context: Annotated[AcknowledgedRelationListEndpointContext, Depends()],
    lineage_id: int,
    requested_by_us: bool = False,
    acknowledged: Optional[bool] = None,
    show_inactive: bool = False,
) -> List[AcknowledgedRelation]:
    object_code: str = f"{context.object_type}-{lineage_id}"
    table_rows: Sequence[AcknowledgedRelationsTable] = repository.get_with_filters(
        session=session,
        code=object_code,
        requested_by_me=requested_by_us,
        acknowledged=acknowledged,
        show_inactive=show_inactive,
    )
    response: List[AcknowledgedRelation] = [build_from_orm(r, object_code) for r in table_rows]
    return response
