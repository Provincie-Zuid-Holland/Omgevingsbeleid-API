from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.pagination import PagedResponse, PaginatedQueryResult, SortOrder
from app.extensions.storage_files.dependencies import (
    depends_storage_file_repository,
    depends_storage_file_sorted_pagination_curried,
)
from app.extensions.storage_files.models.models import StorageFileBasic
from app.extensions.storage_files.repository.storage_file_repository import (
    StorageFileRepository,
    StorageFileSortColumn,
    StorageFileSortedPagination,
)
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user


class ListStorageFilesEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            only_mine: bool = False,
            filter_filename: Optional[str] = None,
            pagination: StorageFileSortedPagination = Depends(
                depends_storage_file_sorted_pagination_curried(
                    StorageFileSortColumn.Created_Date,
                    SortOrder.DESC,
                )
            ),
            user: UsersTable = Depends(depends_current_active_user),
            storage_file_repository: StorageFileRepository = Depends(depends_storage_file_repository),
        ) -> PagedResponse[StorageFileBasic]:
            return self._handler(
                storage_file_repository,
                user,
                only_mine,
                filter_filename,
                pagination,
            )

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=PagedResponse[StorageFileBasic],
            summary=f"List the storage files",
            description=None,
            tags=["Storage File"],
        )

        return router

    def _handler(
        self,
        storage_file_repository: StorageFileRepository,
        user: UsersTable,
        only_mine: bool,
        filter_filename: Optional[str],
        pagination: StorageFileSortedPagination,
    ):
        filter_on_me: Optional[UUID] = None
        if only_mine:
            filter_on_me = user.UUID

        paginated_result: PaginatedQueryResult = storage_file_repository.get_with_filters(
            pagination=pagination,
            filter_filename=filter_filename,
            mine=filter_on_me,
        )

        storage_files = [StorageFileBasic.from_orm(r) for r in paginated_result.items]

        return PagedResponse[StorageFileBasic](
            total=paginated_result.total_count,
            offset=pagination.offset,
            limit=pagination.limit,
            results=storage_files,
        )


class ListStorageFilesEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "list_storage_files"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")

        return ListStorageFilesEndpoint(path)
