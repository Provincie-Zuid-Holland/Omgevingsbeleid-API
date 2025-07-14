from typing import Annotated, List

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session, depends_optional_sorted_pagination
from app.api.domains.users.dependencies import depends_current_user
from app.api.domains.users.types import User
from app.api.domains.users.user_repository import UserRepository
from app.api.endpoint import BaseEndpointContext
from app.api.utils.pagination import OptionalSortedPagination, OrderConfig, PagedResponse, Sort, SortedPagination
from app.core.tables.users import UsersTable


class ListUsersEndpointContext(BaseEndpointContext):
    order_config: OrderConfig


@inject
def get_list_users_endpoint(
    optional_pagination: Annotated[OptionalSortedPagination, Depends(depends_optional_sorted_pagination)],
    user: Annotated[UsersTable, Depends(depends_current_user)],
    session: Annotated[Session, Depends(depends_db_session)],
    repository: Annotated[UserRepository, Depends(Provide[ApiContainer.user_repository])],
    context: Annotated[ListUsersEndpointContext, Depends()],
) -> PagedResponse[User]:
    sort: Sort = context.order_config.get_sort(optional_pagination.sort)
    pagination: SortedPagination = optional_pagination.with_sort(sort)

    paginated_result = repository.get_active(session, pagination)
    users: List[User] = [User.model_validate(u) for u in paginated_result.items]

    return PagedResponse[User](
        total=paginated_result.total_count,
        offset=pagination.offset,
        limit=pagination.limit,
        results=users,
    )
