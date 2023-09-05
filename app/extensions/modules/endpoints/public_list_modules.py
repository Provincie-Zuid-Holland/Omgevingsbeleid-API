from typing import List

from fastapi import APIRouter, Depends

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.dependencies import depends_simple_pagination
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.pagination import PagedResponse, SimplePagination, SortedPagination
from app.extensions.modules.dependencies import depends_module_repository
from app.extensions.modules.models.models import PublicModuleShort
from app.extensions.modules.repository.module_repository import ModuleRepository


class PublicListModulesEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            pagination: SimplePagination = Depends(depends_simple_pagination),
            module_repository: ModuleRepository = Depends(depends_module_repository),
        ) -> PagedResponse[PublicModuleShort]:
            return self._handler(module_repository, pagination)

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=PagedResponse[PublicModuleShort],
            summary=f"List the public modules",
            description=None,
            tags=["Public Modules"],
        )

        return router

    def _handler(
        self,
        module_repository: ModuleRepository,
        pagination: SortedPagination,
    ):
        paginated_result = module_repository.get_public_modules(pagination)

        modules: List[PublicModuleShort] = [
            PublicModuleShort(
                Module_ID=module.Module_ID,
                Title=module.Title,
                Description=module.Description,
                Status=status,
            )
            for status, module in paginated_result.items
        ]

        return PagedResponse[PublicModuleShort](
            total=paginated_result.total_count,
            offset=pagination.offset,
            limit=pagination.limit,
            results=modules,
        )


class PublicListModulesEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "public_list_modules"

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

        return PublicListModulesEndpoint(path)
