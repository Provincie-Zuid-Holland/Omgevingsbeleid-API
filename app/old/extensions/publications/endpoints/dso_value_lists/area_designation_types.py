from typing import List

from dso.services.ow.imow_waardelijsten import NON_ALLOWED_DOCUMENT_TYPE_MAPPING
from dso.services.ow.imow_waardelijsten import TypeGebiedsaanwijzingEnum as AreaDesignationTypes
from fastapi import APIRouter
from pydantic import BaseModel

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.publications.enums import DocumentType


class AreaDesignationValueList(BaseModel):
    Allowed_Values: List[str]


class ListAreaDesignationTypesEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(document_type: DocumentType) -> AreaDesignationValueList:  # type: ignore
            non_allowed = NON_ALLOWED_DOCUMENT_TYPE_MAPPING.get(document_type)
            non_allowed = non_allowed or []
            allowed_types_list = [e.name for e in AreaDesignationTypes if e not in non_allowed]
            return AreaDesignationValueList(Allowed_Values=allowed_types_list)

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=AreaDesignationValueList,
            summary="List the allowed types of area designations to use for this publication document_type",
            description=None,
            tags=["Publication Value Lists"],
        )

        return router


class ListAreaDesignationTypesEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "list_area_designation_types"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")

        return ListAreaDesignationTypesEndpoint(path)
