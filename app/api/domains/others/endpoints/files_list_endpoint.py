from typing import Annotated, Optional
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_optional_sorted_pagination
from app.api.domains.others.repositories.storage_file_repository import StorageFileRepository, StorageFileSortColumn
from app.api.domains.others.types import StorageFileBasic
from app.api.domains.users.dependencies import depends_current_user
from app.api.utils.pagination import (
    OptionalSortedPagination,
    PagedResponse,
    PaginatedQueryResult,
    Sort,
    SortedPagination,
    SortOrder,
)
from app.core.tables.users import UsersTable


@inject
async def get_files_list_endpoint(
    optional_pagination: Annotated[OptionalSortedPagination, Depends(depends_optional_sorted_pagination)],
    user: Annotated[UsersTable, Depends(depends_current_user)],
    storage_file_repository: Annotated[StorageFileRepository, Depends(Provide[ApiContainer.storage_file_repository])],
    only_mine: bool = False,
    filter_filename: Optional[str] = None,
) -> PagedResponse[StorageFileBasic]:
    pagination: SortedPagination = optional_pagination.with_sort(
        Sort(
            column=StorageFileSortColumn.Created_Date,
            order=SortOrder.DESC,
        )
    )

    filter_on_me: Optional[UUID] = None
    if only_mine:
        filter_on_me = user.UUID

    paginated_result: PaginatedQueryResult = storage_file_repository.get_with_filters(
        pagination=pagination,
        filter_filename=filter_filename,
        mine=filter_on_me,
    )

    storage_files = [StorageFileBasic.model_validate(r) for r in paginated_result.items]

    return PagedResponse[StorageFileBasic](
        total=paginated_result.total_count,
        offset=pagination.offset,
        limit=pagination.limit,
        results=storage_files,
    )
