from typing import List, Optional

from dso.services.ow.waardelijsten.imow_value_repository import imow_value_repository
from dso.services.ow.waardelijsten.imow_models import GebiedsaanwijzingGroepValue
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver


class AreaDesignationValueList(BaseModel):
    Allowed_Values: List[GebiedsaanwijzingGroepValue]


class ListAreaDesignationGroupsEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
                area_designation_type: Optional[str] = None,
            ) -> AreaDesignationValueList:
            if not area_designation_type:
                return AreaDesignationValueList(Allowed_Values=imow_value_repository.get_all_gebiedsaanwijzing_groepen())

            gba_type = imow_value_repository.get_type_gebiedsaanwijzing_by_any(area_designation_type)
            if not gba_type:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid area designation type. {area_designation_type} is not a valid area designation type"
                )
            allowed_groups = imow_value_repository.get_groups_for_type(gba_type.uri)
            return AreaDesignationValueList(Allowed_Values=allowed_groups)

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=AreaDesignationValueList,
            summary="List the allowed groups to use for this publication document_type",
            description="Accepts area designation type Term or URI as input to identify the area designation groups",
            tags=["Publication Value Lists"],
        )
        return router


class ListAreaDesignationGroupsEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "list_area_designation_groups"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")

        return ListAreaDesignationGroupsEndpoint(path)
