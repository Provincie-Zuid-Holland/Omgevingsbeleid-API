import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.publications.dependencies import depends_publication_repository
from app.extensions.publications.models import PublicationBill
from app.extensions.publications.repository import PublicationRepository


class DetailPublicationBillEndpoint(Endpoint):
    def __init__(self, event_dispatcher: EventDispatcher, path: str):
        self._event_dispatcher: EventDispatcher = event_dispatcher
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            # user: UsersTable = Depends(depends_current_active_user),
            bill_uuid: uuid.UUID,
            pub_repository: PublicationRepository = Depends(depends_publication_repository),
        ) -> PublicationBill:
            bill = pub_repository.get_publication_bill(bill_uuid)
            if not bill:
                raise HTTPException(status_code=404, detail=f"Bill: {bill_uuid} not found")

            return PublicationBill.from_orm(bill)

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=PublicationBill,
            summary=f"Get details of a publication bill",
            description=None,
            tags=["Publications"],
        )

        return router


class DetailPublicationBillEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "detail_publication_bill"

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
        if not "{bill_uuid}" in path:
            raise RuntimeError("Missing {bill_uuid} argument in path")

        return DetailPublicationBillEndpoint(
            event_dispatcher=event_dispatcher,
            path=path,
        )
