from typing import List

from dso.services.ow.waardelijsten import THEMA_VALUES
from dso.services.ow.waardelijsten.models import ValueEntry
from fastapi import APIRouter
from pydantic import BaseModel

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver


class ThemeValueList(BaseModel):
    Allowed_Values: List[ValueEntry]


class ListThemeValuesEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler() -> ThemeValueList:
            return ThemeValueList(Allowed_Values=THEMA_VALUES.waarden.waarde)

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=ThemeValueList,
            summary="List all available thema values",
            description="Returns all possible thema values that can be used in publications",
            tags=["Publication Value Lists"],
        )

        return router


class ListThemeValuesEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "list_theme_values"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")

        return ListThemeValuesEndpoint(path)
