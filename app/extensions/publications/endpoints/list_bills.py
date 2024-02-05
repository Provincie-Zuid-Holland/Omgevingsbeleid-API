import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.dependencies import depends_simple_pagination
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.pagination import PagedResponse, SimplePagination
from app.extensions.modules.models.models import ModuleStatusCode
from app.extensions.publications import Procedure_Type, PublicationBill
from app.extensions.publications.dependencies import depends_publication_repository
from app.extensions.publications.repository import PublicationRepository
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user


class PublicationBillShort(BaseModel):
    UUID: uuid.UUID
    Created_Date: datetime
    Modified_Date: datetime

    Publication_UUID: uuid.UUID
    Module_Status_ID: int
    Version_ID: Optional[int]
    Procedure_Type: Procedure_Type
    Is_Official: bool

    class Config:
        orm_mode = True


class ListPublicationBillsEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            publication_uuid: Optional[uuid.UUID] = None,
            version_id: Optional[int] = None,
            module_status: Optional[ModuleStatusCode] = None,
            pagination: SimplePagination = Depends(depends_simple_pagination),
            pub_repository: PublicationRepository = Depends(depends_publication_repository),
            user: UsersTable = Depends(depends_current_active_user),
        ) -> PagedResponse[PublicationBillShort]:
            paginated_result = pub_repository.get_publication_bills(
                publication_uuid=publication_uuid,
                version_id=version_id,
                module_status=module_status,
                offset=pagination.offset,
                limit=pagination.limit,
            )

            bills = [PublicationBill.from_orm(r) for r in paginated_result.items]

            return PagedResponse[PublicationBillShort](
                total=paginated_result.total_count,
                offset=pagination.offset,
                limit=pagination.limit,
                results=bills,
            )

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=PagedResponse[PublicationBillShort],
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

        return ListPublicationBillsEndpoint(path=path)
