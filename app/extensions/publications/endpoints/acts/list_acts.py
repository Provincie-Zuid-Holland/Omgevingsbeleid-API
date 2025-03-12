import uuid
from typing import Optional

from fastapi import APIRouter, Depends

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.dependencies import depends_simple_pagination
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.pagination import PagedResponse, SimplePagination
from app.extensions.publications.dependencies import depends_publication_act_repository
from app.extensions.publications.enums import DocumentType, ProcedureType
from app.extensions.publications.models.models import PublicationActShort
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.repository.publication_act_repository import PublicationActRepository
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class ListPublicationActsEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            is_active: Optional[bool] = None,
            environment_uuid: Optional[uuid.UUID] = None,
            document_type: Optional[DocumentType] = None,
            procedure_type: Optional[ProcedureType] = None,
            pagination: SimplePagination = Depends(depends_simple_pagination),
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_view_publication_act,
                )
            ),
            act_repository: PublicationActRepository = Depends(depends_publication_act_repository),
        ) -> PagedResponse[PublicationActShort]:
            return self._handler(
                act_repository,
                is_active,
                environment_uuid,
                document_type,
                procedure_type,
                pagination,
            )

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=PagedResponse[PublicationActShort],
            summary=f"List the publication acts",
            description=None,
            tags=["Publication Acts"],
        )

        return router

    def _handler(
        self,
        act_repository: PublicationActRepository,
        is_active: Optional[bool],
        environment_uuid: Optional[uuid.UUID],
        document_type: Optional[DocumentType],
        procedure_type: Optional[ProcedureType],
        pagination: SimplePagination,
    ):
        paginated_result = act_repository.get_with_filters(
            is_active=is_active,
            environment_uuid=environment_uuid,
            document_type=document_type,
            procedure_type=procedure_type,
            offset=pagination.offset,
            limit=pagination.limit,
        )

        results = [PublicationActShort.model_validate(r) for r in paginated_result.items]

        return PagedResponse[PublicationActShort](
            total=paginated_result.total_count,
            offset=pagination.offset,
            limit=pagination.limit,
            results=results,
        )


class ListPublicationActsEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "list_publication_acts"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")

        return ListPublicationActsEndpoint(path)
