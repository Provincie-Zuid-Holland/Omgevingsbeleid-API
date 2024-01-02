from typing import Optional

from fastapi import APIRouter, Depends

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.dependencies import depends_simple_pagination
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.pagination import (
    OrderConfig,
    PagedResponse,
    SimplePagination
)
from app.extensions.modules.models.models import ModuleStatusCode
from app.extensions.publications import PublicationBill, Document_Type
from app.extensions.publications.dependencies import depends_publication_repository
from app.extensions.publications.repository import PublicationRepository


class ListPublicationBillsEndpoint(Endpoint):
    def __init__(self, path: str, order_config: OrderConfig):
        self._path: str = path
        self._order_config: OrderConfig = order_config

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            # user: UsersTable = Depends(depends_current_active_user),
            document_type: Optional[Document_Type] = None,
            version_id: Optional[int] = None,
            module_id: Optional[int] = None,
            module_status: Optional[ModuleStatusCode] = None,
            pagination: SimplePagination = Depends(depends_simple_pagination),
            bill_repository: PublicationRepository = Depends(depends_publication_repository),
        ) -> PagedResponse[PublicationBill]:
            paginated_result = bill_repository.get_publication_bills(
                document_type=document_type,
                version_id=version_id,
                module_id=module_id,
                module_status=module_status,
                offset=pagination.offset,
                limit=pagination.limit
            )

            bills = [PublicationBill.from_orm(r) for r in paginated_result.items]

            return PagedResponse[PublicationBill](
                total=paginated_result.total_count,
                offset=pagination.offset,
                limit=pagination.limit,
                results=bills,
            )

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=PagedResponse[PublicationBill],
            summary="List the existing Publication Bills",
            description=None,
            tags=["Publications"],
        )

        return router


class ListPublicationBillsEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "list_publication_bills"

    def generate_endpoint(
        self,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        order_config: OrderConfig = OrderConfig.from_dict(resolver_config["sort"])

        return ListPublicationBillsEndpoint(
            path=path,
            order_config=order_config,
        )
